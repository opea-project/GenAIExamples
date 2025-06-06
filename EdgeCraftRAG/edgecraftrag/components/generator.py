# Copyright (C) 2024 Intel Corporation
# SPDX-License-Identifier: Apache-2.0

import asyncio
import dataclasses
import json
import os
import urllib.request
from urllib.parse import urlparse

from edgecraftrag.base import BaseComponent, CompType, GeneratorType, InferenceType, NodeParserType
from edgecraftrag.utils import concat_history, save_history
from fastapi.responses import StreamingResponse
from langchain_core.prompts import PromptTemplate
from llama_index.llms.openai_like import OpenAILike
from pydantic import model_serializer
from unstructured.staging.base import elements_from_base64_gzipped_json

DEFAULT_TEMPLATE = """
<|im_start|>System: You are an AI assistant. Your task is to learn from the following context. Then answer the user's question based on what you learned from the context but not your own knowledge.<|im_end|>

<|im_start|>{context}<|im_end|>

<|im_start|>System: Pay attention to your formatting of response. If you need to reference content from context, try to keep the formatting.<|im_end|>
<|im_start|>System: Try to summarize from the context, do some reasoning before response, then response. Make sure your response is logically sound and self-consistent.<|im_end|>

<|im_start|>{input}
"""


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
        if "filename" in metadata:
            reference_doc = (
                metadata["filename"]
                if "page_number" not in metadata
                else metadata["filename"] + " --page" + str(metadata["page_number"])
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
    if image_paths:
        unstructured_str += "\n\n参考图片:\n\n"
        for image_path in image_paths:
            unstructured_str += f"![]({image_path})"
    if link_urls:
        unstructured_str += "\n\n相关链接:\n\n"
        for link in link_urls:
            unstructured_str += f"[{link}]({link})\n\n"
    if reference_docs:
        unstructured_str += "\n\n内容来源:\n\n"
        for reference_doc in reference_docs:
            unstructured_str += f"{reference_doc}\n\n"
    return unstructured_str


async def local_stream_generator(lock, llm, prompt_str, unstructured_str):
    async with lock:
        response = llm.stream_complete(prompt_str)
        collected_data = []
        for r in response:
            collected_data.append(r.delta)
            yield r.delta
            await asyncio.sleep(0)
        if unstructured_str:
            collected_data.append(unstructured_str)
            yield unstructured_str
        res = "".join(collected_data)
        save_history(res)


async def stream_generator(llm, prompt_str, unstructured_str):
    response = llm.stream_complete(prompt_str)
    collected_data = []
    for r in response:
        collected_data.append(r.delta)
        yield r.delta
        await asyncio.sleep(0)
    if unstructured_str:
        collected_data.append(unstructured_str)
        yield unstructured_str
    res = "".join(collected_data)
    save_history(res)


class QnAGenerator(BaseComponent):

    def __init__(self, llm_model, prompt_template_file, inference_type, **kwargs):
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

        if prompt_template_file is None:
            print("There is no template file, using the default template.")
            self.prompt = DocumentedContextRagPromptTemplate.from_template(DEFAULT_TEMPLATE)
        else:
            safe_root = "/templates"
            template_path = os.path.normpath(os.path.join(safe_root, prompt_template_file))
            if not template_path.startswith(safe_root):
                raise ValueError("Invalid template path")
            if not os.path.exists(template_path):
                raise ValueError("Template file not exists")
            self.prompt = DocumentedContextRagPromptTemplate.from_file(template_path)

        self.llm = llm_model
        if isinstance(llm_model, str):
            self.model_id = llm_model
        else:
            self.model_id = llm_model().model_id
        if self.inference_type == InferenceType.LOCAL:
            self.lock = asyncio.Lock()

    def set_prompt(self, prompt):
        if "{context}" not in prompt:
            prompt += "\n<|im_start|>{context}<|im_end|>"
        if "{input}" not in prompt:
            prompt += "\n<|im_start|>{input}"
        self.prompt = prompt

    def reset_prompt(self):
        self.prompt = DocumentedContextRagPromptTemplate.from_template(DEFAULT_TEMPLATE)

    def clean_string(self, string):
        ret = string
        for p in self._REPLACE_PAIRS:
            ret = ret.replace(*p)
        return ret

    def query_transform(self, chat_request, retrieved_nodes):
        """Generate text_gen_context and prompt_str
        :param chat_request: Request object
        :param retrieved_nodes: List of retrieved nodes
        :return: Generated text_gen_context and prompt_str."""
        text_gen_context = ""
        for n in retrieved_nodes:
            origin_text = n.node.get_text()
            text_gen_context += self.clean_string(origin_text.strip())
        query = chat_request.messages
        prompt_str = self.prompt.format(input=query, context=text_gen_context)
        return text_gen_context, prompt_str

    def run(self, chat_request, retrieved_nodes, node_parser_type, **kwargs):
        if self.llm() is None:
            # This could happen when User delete all LLMs through RESTful API
            raise ValueError("No LLM available, please load LLM")
        # query transformation
        chat_request.messages = concat_history(chat_request.messages)
        text_gen_context, prompt_str = self.query_transform(chat_request, retrieved_nodes)
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
        if node_parser_type == NodeParserType.UNSTRUCTURED:
            unstructured_str = extract_unstructured_eles(retrieved_nodes, text_gen_context)
        if chat_request.stream:
            return StreamingResponse(
                local_stream_generator(self.lock, self.llm(), prompt_str, unstructured_str),
                media_type="text/event-stream",
            )
        else:
            result = self.llm().complete(prompt_str)
            save_history(str(result.text))
            return result

    def run_vllm(self, chat_request, retrieved_nodes, node_parser_type, **kwargs):
        # query transformation
        chat_request.messages = concat_history(chat_request.messages)
        text_gen_context, prompt_str = self.query_transform(chat_request, retrieved_nodes)
        llm_endpoint = os.getenv("vLLM_ENDPOINT", "http://localhost:8008")
        model_name = os.getenv("LLM_MODEL", self.model_id)
        llm = OpenAILike(
            api_key="fake",
            api_base=llm_endpoint + "/v1",
            max_tokens=chat_request.max_tokens,
            model=model_name,
            top_p=chat_request.top_p,
            top_k=chat_request.top_k,
            temperature=chat_request.temperature,
            streaming=chat_request.stream,
            repetition_penalty=chat_request.repetition_penalty,
        )
        unstructured_str = ""
        if node_parser_type == NodeParserType.UNSTRUCTURED:
            unstructured_str = extract_unstructured_eles(retrieved_nodes, text_gen_context)
        if chat_request.stream:
            return StreamingResponse(
                stream_generator(llm, prompt_str, unstructured_str), media_type="text/event-stream"
            )
        else:
            result = llm.complete(prompt_str)
            save_history(str(result))
            return result

    @model_serializer
    def ser_model(self):
        set = {
            "idx": self.idx,
            "generator_type": self.comp_subtype,
            "inference_type": self.inference_type,
            "model": self.llm(),
        }
        return set


@dataclasses.dataclass
class INSTRUCTIONS:
    IM_START = "You are an AI assistant that helps users answer questions given a specific context."
    SUCCINCT = "Ensure your response is succinct"
    ACCURATE = "Ensure your response is accurate."
    SUCCINCT_AND_ACCURATE = "Ensure your response is succinct. Try to be accurate if possible."
    ACCURATE_AND_SUCCINCT = "Ensure your response is accurate. Try to be succinct if possible."
    NO_RAMBLING = "Avoid posing new questions or self-questioning and answering, and refrain from repeating words in your response."
    SAY_SOMETHING = "Avoid meaningless answer such a random symbol or blanks."
    ENCOURAGE = "If you cannot well understand the question, try to translate it into English, and translate the answer back to the language of the question."
    NO_IDEA = (
        'If the answer is not discernible, please respond with "Sorry. I have no idea" in the language of the question.'
    )
    CLOZE_TEST = """The task is a fill-in-the-blank/cloze test."""
    NO_MEANINGLESS_SYMBOLS = "Meaningless symbols and ``` should not be included in your response."
    ADAPT_NATIVE_LANGUAGE = "Please try to think like a person that speak the same language that the question used."


def _is_cloze(question):
    return ("()" in question or "（）" in question) and ("填" in question or "fill" in question or "cloze" in question)


# depreciated
def get_instructions(question):
    # naive pre-retrieval rewrite
    # cloze
    if _is_cloze(question):
        instructions = [
            INSTRUCTIONS.CLOZE_TEST,
        ]
    else:
        instructions = [
            INSTRUCTIONS.ACCURATE_AND_SUCCINCT,
            INSTRUCTIONS.NO_RAMBLING,
            INSTRUCTIONS.NO_MEANINGLESS_SYMBOLS,
        ]
    return ["System: {}".format(_) for _ in instructions]


def preprocess_question(question):
    if _is_cloze(question):
        question = question.replace(" ", "").replace("（", "(").replace("）", ")")
        # .replace("()", " <|blank|> ")
        ret = "User: Please finish the following fill-in-the-blank question marked by $$$ at the beginning and end. Make sure all the () are filled.\n$$$\n{}\n$$$\nAssistant: ".format(
            question
        )
    else:
        ret = "User: {}\nAssistant: 从上下文提供的信息中可以知道，".format(question)
    return ret


class DocumentedContextRagPromptTemplate(PromptTemplate):

    def format(self, **kwargs) -> str:
        # context = '\n'.join([clean_string(f"{_.page_content}".strip()) for i, _ in enumerate(kwargs["context"])])
        context = kwargs["context"]
        question = kwargs["input"]
        preprocessed_question = preprocess_question(question)
        if "instructions" in self.template:
            instructions = get_instructions(question)
            prompt_str = self.template.format(
                context=context, instructions="\n".join(instructions), input=preprocessed_question
            )
        else:
            prompt_str = self.template.format(context=context, input=preprocessed_question)
        return prompt_str
