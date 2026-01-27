# Copyright (C) 2024 Intel Corporation
# SPDX-License-Identifier: Apache-2.0

import asyncio
import json
import os
import urllib.request
from concurrent.futures import ThreadPoolExecutor
from urllib.parse import urlparse

from comps.cores.proto.api_protocol import ChatCompletionRequest
from edgecraftrag.base import BaseComponent, CompType, GeneratorType, InferenceType, NodeParserType
from edgecraftrag.utils import get_prompt_template
from fastapi.responses import StreamingResponse
from llama_index.llms.openai_like import OpenAILike
from pydantic import model_serializer
from unstructured.staging.base import elements_from_base64_gzipped_json


def extract_urls(text):
    urls = []
    words = text.split()
    for word in words:
        parsed_url = urlparse(word)
        if parsed_url.scheme and parsed_url.netloc:
            url = parsed_url.geturl()
            try:
                response = urllib.request.urlopen(url)
                if response.status == 200:
                    urls.append(url)
            except (urllib.error.URLError, urllib.error.HTTPError, Exception):
                pass
    return urls


def extract_unstructured_eles(retrieved_nodes=[], text_gen_context=""):
    IMAGE_NUMBER = 2
    image_count = 0
    link_urls = []
    image_paths = []
    reference_docs = set()
    for node in retrieved_nodes:
        if node.score < 0.5:
            continue
        metadata = node.node.metadata
        # extract referenced docs
        if "file_name" in metadata:
            reference_doc = (
                metadata["file_name"]
                if "page_number" not in metadata
                else metadata["file_name"] + " --page" + str(metadata["page_number"])
            )
            reference_docs.add(reference_doc)
        # extract hyperlinks in chunk
        if "link_urls" in metadata:
            if isinstance(metadata["link_urls"], str):
                try:
                    url_list = json.loads(metadata["link_urls"])
                    link_urls.extend(url_list)
                except json.JSONDecodeError:
                    print("link_urls is not a valid JSON string.")
        # extract images in chunk
        if image_count < IMAGE_NUMBER and "orig_elements" in metadata:
            elements = elements_from_base64_gzipped_json(metadata["orig_elements"])
            for element in elements:
                if element.metadata.image_path:
                    image_paths.append(element.metadata.image_path)
                    image_count += 1
        # extract hyperlinks in chunk
        link_urls.extend(extract_urls(text_gen_context))
    unstructured_str = ""
    if reference_docs:
        unstructured_str += "\n\n --- \n\n### Document Source:\n"
        for reference_doc in reference_docs:
            unstructured_str += f"- {reference_doc}\n\n"
    return unstructured_str


def build_stream_response(status=None, content=None, error=None):
    response = {"status": status, "contentType": "text"}
    if content is not None:
        response["content"] = content
    if error is not None:
        response["error"] = error
    return response


async def local_stream_generator(lock, llm, prompt_str, unstructured_str):
    async with lock:
        response = await llm.astream_complete(prompt_str)
        try:
            async for r in response:
                yield r.delta or ""
                await asyncio.sleep(0)
            if unstructured_str:
                yield unstructured_str
        except Exception as e:
            start_idx = str(e).find("message") + len("message")
            result_error = str(e)[start_idx:]
            yield f"code:0000{result_error}"


async def stream_generator(llm, prompt_str, unstructured_str):
    response = await llm.astream_complete(prompt_str)
    try:
        async for r in response:
            yield r.delta or ""
            await asyncio.sleep(0)
        if unstructured_str:
            yield unstructured_str
            await asyncio.sleep(0)
    except asyncio.CancelledError as e:
        response.aclose()
    except Exception as e:
        start_idx = str(e).find("message") + len("message")
        result_error = str(e)[start_idx:]
        yield f"code:0000{result_error}"


class QnAGenerator(BaseComponent):

    def __init__(self, llm_model, prompt_template_file, inference_type, vllm_endpoint, prompt_content, **kwargs):
        BaseComponent.__init__(
            self,
            comp_type=CompType.GENERATOR,
            comp_subtype=GeneratorType.CHATQNA,
        )
        self.inference_type = inference_type
        self._REPLACE_PAIRS = (
            ("\n\n", "\n"),
            ("\t\n", "\n"),
        )
        self.enable_think = False
        self.enable_rag_retrieval = True
        self.prompt_content = prompt_content
        self.prompt_template_file = prompt_template_file
        if isinstance(llm_model, str):
            self.model_id = llm_model
            self.model_path = llm_model
        else:
            llm_instance = llm_model()
            if llm_instance.model_path is None or llm_instance.model_path == "":
                self.model_id = llm_instance.model_id
                self.model_path = os.path.join("/home/user/models", os.getenv("LLM_MODEL", "Qwen/Qwen3-8B"))
            else:
                self.model_id = llm_instance.model_id
                self.model_path = llm_instance.model_path
        self.original_template, self.prompt = self.prompt_handler(
            self.model_path, self.prompt_content, self.prompt_template_file
        )

        self.llm = llm_model
        if self.inference_type == InferenceType.LOCAL:
            self.lock = asyncio.Lock()
        if self.inference_type == InferenceType.VLLM:
            self.vllm_name = llm_model().model_id
            if vllm_endpoint == "":
                vllm_endpoint = os.getenv("vLLM_ENDPOINT", "http://localhost:8086")
        self.vllm_endpoint = vllm_endpoint

    def prompt_handler(
        self, model_path, prompt_content=None, prompt_template_file=None, enable_think=False, enable_rag_retrieval=True
    ):
        if prompt_content:
            return get_prompt_template(model_path, prompt_content, prompt_template_file, enable_think)
        elif prompt_template_file is None:
            print("There is no template file, using the default template.")
            prompt_template = get_prompt_template(model_path, prompt_content, prompt_template_file, enable_think)
            return prompt_template
        else:
            if enable_rag_retrieval:
                safe_root = "/templates"
            else:
                prompt_content = "### User Guide ###You are a helpful assistant. Please respond to user inquiries with concise and professional answers.### Historical Content ###{chat_history}"
                return get_prompt_template(model_path, prompt_content, prompt_template_file, enable_think)

            prompt_template_file = os.path.normpath(os.path.join(safe_root, prompt_template_file))
            if not prompt_template_file.startswith(safe_root):
                raise ValueError("Invalid template path")
            if not os.path.exists(prompt_template_file):
                raise ValueError("Template file not exists")
            return get_prompt_template(model_path, prompt_content, prompt_template_file, enable_think)

    def set_prompt(self, prompt):
        if "{context}" not in prompt:
            prompt += "\n<|im_start|>{context}<|im_end|>"
        if "{chat_history}" not in prompt:
            prompt += "\n<|im_start|>{chat_history}"
        self.prompt_content = prompt
        self.original_template, self.prompt = self.prompt_handler(
            self.model_path, self.prompt_content, self.prompt_template_file
        )

    def reset_prompt(self):
        self.prompt_content = None
        self.original_template, self.prompt = self.prompt_handler(
            self.model_path, self.prompt_content, self.prompt_template_file
        )

    def clean_string(self, string):
        ret = string
        for p in self._REPLACE_PAIRS:
            ret = ret.replace(*p)
        return ret

    def query_transform(self, chat_request, retrieved_nodes, sub_questions=None):
        """Generate text_gen_context and prompt_str
        :param chat_request: Request object
        :param retrieved_nodes: List of retrieved nodes
        :param sub_questions: Optional sub-questions string (safe parameter)
        :return: Generated text_gen_context and prompt_str."""
        text_gen_context = ""
        for n in retrieved_nodes:
            origin_text = n.node.text
            text_gen_context += self.clean_string(origin_text.strip())
        query = chat_request.messages
        chat_history = chat_request.input
        # Modify model think status
        if chat_request.chat_template_kwargs:
            change_flag = False
            if "enable_rag_retrieval" in chat_request.chat_template_kwargs:
                if self.enable_rag_retrieval != chat_request.chat_template_kwargs["enable_rag_retrieval"]:
                    self.enable_rag_retrieval = chat_request.chat_template_kwargs["enable_rag_retrieval"]
                    change_flag = True
            if "enable_thinking" in chat_request.chat_template_kwargs:
                if self.enable_think != chat_request.chat_template_kwargs["enable_thinking"]:
                    self.enable_think = chat_request.chat_template_kwargs["enable_thinking"]
                    change_flag = True
            if change_flag:
                self.original_template, self.prompt = self.prompt_handler(
                    self.model_path,
                    self.prompt_content,
                    self.prompt_template_file,
                    self.enable_think,
                    self.enable_rag_retrieval,
                )

        if sub_questions:
            final_query = f"{query}\n\n### Sub-questions ###\nThe following list is how you should consider the answer, you MUST follow these steps when responding:\n\n{sub_questions}"
        else:
            final_query = query
        prompt_str = self.prompt.format(input=final_query, chat_history=chat_history, context=text_gen_context)
        return text_gen_context, prompt_str

    async def run(self, chat_request, retrieved_nodes, node_parser_type, **kwargs):
        if self.llm() is None:
            # This could happen when User delete all LLMs through RESTful API
            raise ValueError("No LLM available, please load LLM")
        # query transformation
        sub_questions = kwargs.get("sub_questions", None)
        text_gen_context, prompt_str = self.query_transform(chat_request, retrieved_nodes, sub_questions=sub_questions)
        generate_kwargs = dict(
            temperature=chat_request.temperature,
            do_sample=chat_request.temperature > 0.0,
            top_p=chat_request.top_p,
            top_k=chat_request.top_k,
            typical_p=chat_request.typical_p,
            repetition_penalty=chat_request.repetition_penalty,
        )
        self.llm().generate_kwargs = generate_kwargs
        self.llm().max_new_tokens = chat_request.max_tokens
        unstructured_str = ""
        if node_parser_type == NodeParserType.UNSTRUCTURED or node_parser_type == NodeParserType.SIMPLE:
            unstructured_str = extract_unstructured_eles(retrieved_nodes, text_gen_context)
        if chat_request.stream:
            # Asynchronous generator
            async def generator():
                async for chunk in local_stream_generator(self.lock, self.llm(), prompt_str, unstructured_str):
                    yield chunk or ""
                    await asyncio.sleep(0)

            return generator()
        else:
            result = self.llm().complete(prompt_str)
            return result

    async def run_vllm(self, chat_request, retrieved_nodes, node_parser_type, **kwargs):
        # query transformation
        sub_questions = kwargs.get("sub_questions", None)
        text_gen_context, prompt_str = self.query_transform(chat_request, retrieved_nodes, sub_questions=sub_questions)
        llm = OpenAILike(
            api_key="fake",
            api_base=self.vllm_endpoint + "/v1",
            max_tokens=chat_request.max_tokens,
            model=self.vllm_name,
            top_p=chat_request.top_p,
            top_k=chat_request.top_k,
            temperature=chat_request.temperature,
            streaming=chat_request.stream,
            repetition_penalty=chat_request.repetition_penalty,
        )
        unstructured_str = ""
        if node_parser_type == NodeParserType.UNSTRUCTURED or node_parser_type == NodeParserType.SIMPLE:
            unstructured_str = extract_unstructured_eles(retrieved_nodes, text_gen_context)
        if chat_request.stream:

            # Asynchronous generator
            async def generator():
                async for chunk in stream_generator(llm, prompt_str, unstructured_str):
                    yield chunk or ""
                    await asyncio.sleep(0)

            return generator()
        else:
            result = await llm.acomplete(prompt_str)
            return result

    @model_serializer
    def ser_model(self):
        set = {
            "idx": self.idx,
            "generator_type": self.comp_subtype,
            "inference_type": self.inference_type,
            "model": self.llm(),
            "vllm_endpoint": self.vllm_endpoint,
        }
        return set


class FreeChatGenerator(BaseComponent):

    def __init__(self, llm_model, inference_type, vllm_endpoint, **kwargs):
        BaseComponent.__init__(
            self,
            comp_type=CompType.GENERATOR,
            comp_subtype=GeneratorType.FREECHAT,
        )
        self.inference_type = inference_type
        self.prompt_content = ""
        self.prompt_template_file = ""
        self._REPLACE_PAIRS = (
            ("\n\n", "\n"),
            ("\t\n", "\n"),
        )
        self.enable_think = False
        if isinstance(llm_model, str):
            self.model_id = llm_model
            self.model_path = llm_model
        else:
            llm_instance = llm_model()
            if llm_instance.model_path is None or llm_instance.model_path == "":
                self.model_id = llm_instance.model_id
                self.model_path = os.path.join("/home/user/models", os.getenv("LLM_MODEL", "Qwen/Qwen3-8B"))
            else:
                self.model_id = llm_instance.model_id
                self.model_path = llm_instance.model_path

        self.llm = llm_model
        if self.inference_type == InferenceType.VLLM:
            self.vllm_name = llm_model().model_id
            if vllm_endpoint == "":
                vllm_endpoint = os.getenv("vLLM_ENDPOINT", "http://localhost:8086")
        self.vllm_endpoint = vllm_endpoint

    async def run(self, chat_request, retrieved_nodes, node_parser_type, **kwargs):
        response = await self.run_vllm(chat_request, retrieved_nodes, node_parser_type, **kwargs)
        return response

    async def run_vllm(self, chat_request, retrieved_nodes, node_parser_type, **kwargs):
        llm = OpenAILike(
            api_key="fake",
            api_base=self.vllm_endpoint + "/v1",
            max_tokens=chat_request.max_tokens,
            model=self.vllm_name,
            top_p=chat_request.top_p,
            top_k=chat_request.top_k,
            temperature=chat_request.temperature,
            streaming=chat_request.stream,
            repetition_penalty=chat_request.repetition_penalty,
        )
        prompt_str = chatcompletion_to_chatml(chat_request)
        if chat_request.stream:

            # Asynchronous generator
            async def generator():
                gen = await llm.astream_complete(prompt_str)
                async for chunk in gen:
                    yield chunk.delta or ""
                    await asyncio.sleep(0)

            return generator()
        else:
            result = await llm.acomplete(prompt_str)
            return str(result)

    @model_serializer
    def ser_model(self):
        set = {
            "idx": self.idx,
            "generator_type": self.comp_subtype,
            "inference_type": self.inference_type,
            "model": self.llm(),
            "vllm_endpoint": self.vllm_endpoint,
        }
        return set


def chatcompletion_to_chatml(request: ChatCompletionRequest) -> str:
    """Convert a ChatCompletionRequest dict to a ChatML-formatted string."""
    chatml = ""
    for msg in request.messages:
        chatml += f"<|im_start|>{msg.get('role', '')}\n{msg.get('content', '')}<|im_end|>\n"
    # start generation from assistant role
    chatml += "<|im_start|>assistant\n"
    return chatml
