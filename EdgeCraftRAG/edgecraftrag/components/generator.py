# Copyright (C) 2024 Intel Corporation
# SPDX-License-Identifier: Apache-2.0

import asyncio
import dataclasses
import json
import os

from comps import GeneratedDoc
from edgecraftrag.base import BaseComponent, CompType, GeneratorType
from fastapi.responses import StreamingResponse
from langchain_core.prompts import PromptTemplate
from llama_index.llms.openai_like import OpenAILike
from pydantic import model_serializer
from unstructured.staging.base import elements_from_base64_gzipped_json


async def stream_generator(llm, prompt_str, retrieved_nodes=[], text_gen_context=""):
    response = llm.stream_complete(prompt_str)
    for r in response:
        yield json.dumps({"llm_res": r.delta})
        await asyncio.sleep(0)
    for node in retrieved_nodes:
        node.node.metadata["score"] = float(node.score)
        yield json.dumps(node.node.metadata)
        await asyncio.sleep(0)
    yield json.dumps({"retrieved_text": text_gen_context})


class QnAGenerator(BaseComponent):

    def __init__(self, llm_model, prompt_template, inference_type, **kwargs):
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
        safe_root = "/templates"
        template = os.path.normpath(os.path.join(safe_root, prompt_template))
        if not template.startswith(safe_root):
            raise ValueError("Invalid template path")
        if not os.path.exists(template):
            raise ValueError("Template file not exists")
        self.prompt = DocumentedContextRagPromptTemplate.from_file(template)
        self.llm = llm_model
        if isinstance(llm_model, str):
            self.model_id = llm_model
        else:
            self.model_id = llm_model().model_id

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

    def run(self, chat_request, retrieved_nodes, **kwargs):
        if self.llm() is None:
            # This could happen when User delete all LLMs through RESTful API
            return "No LLM available, please load LLM"
        # query transformation
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
        if chat_request.stream:
            return StreamingResponse(
                stream_generator(self.llm(), prompt_str, retrieved_nodes, text_gen_context),
                media_type="text/event-stream",
            )
        else:
            return self.llm().complete(prompt_str)

    def run_vllm(self, chat_request, retrieved_nodes, **kwargs):
        if self.llm is None:
            return "No LLM provided, please provide model_id_or_path"
        # query transformation
        text_gen_context, prompt_str = self.query_transform(chat_request, retrieved_nodes)
        llm_endpoint = os.getenv("vLLM_ENDPOINT", "http://localhost:8008")
        model_name = self.llm().model_id
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

        if chat_request.stream:
            return StreamingResponse(
                stream_generator(llm, prompt_str, retrieved_nodes, text_gen_context), media_type="text/event-stream"
            )
        else:
            response = llm.complete(prompt_str)
            response = response.text

            return GeneratedDoc(text=response, prompt=prompt_str)

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
