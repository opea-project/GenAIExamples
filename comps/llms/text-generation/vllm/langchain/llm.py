# Copyright (C) 2024 Intel Corporation
# SPDX-License-Identifier: Apache-2.0

import os
from typing import Union

from fastapi.responses import StreamingResponse
from langchain_community.llms import VLLMOpenAI
from langchain_core.prompts import PromptTemplate
from template import ChatTemplate

from comps import (
    CustomLogger,
    GeneratedDoc,
    LLMParamsDoc,
    SearchedDoc,
    ServiceType,
    opea_microservices,
    opea_telemetry,
    register_microservice,
)
from comps.cores.mega.utils import ConfigError, get_access_token, load_model_configs
from comps.cores.proto.api_protocol import ChatCompletionRequest

logger = CustomLogger("llm_vllm")
logflag = os.getenv("LOGFLAG", False)

# Environment variables
TOKEN_URL = os.getenv("TOKEN_URL")
CLIENTID = os.getenv("CLIENTID")
CLIENT_SECRET = os.getenv("CLIENT_SECRET")
MODEL_CONFIGS = os.getenv("MODEL_CONFIGS")
DEFAULT_ENDPOINT = os.getenv("vLLM_ENDPOINT", "http://localhost:8080")

# Validate and Load the models config if MODEL_CONFIGS is not null
configs_map = {}
if MODEL_CONFIGS:
    try:
        configs_map = load_model_configs(MODEL_CONFIGS)
    except ConfigError as e:
        logger.error(f"Failed to load model configurations: {e}")
        raise ConfigError(f"Failed to load model configurations: {e}")


def get_llm_endpoint(model):
    if not MODEL_CONFIGS:
        return DEFAULT_ENDPOINT
    try:
        return configs_map.get(model).get("endpoint")
    except ConfigError as e:
        logger.error(f"Input model {model} not present in model_configs. Error {e}")
        raise ConfigError(f"Input model {model} not present in model_configs")


@opea_telemetry
def post_process_text(text: str):
    if text == " ":
        return "data: @#$\n\n"
    if text == "\n":
        return "data: <br/>\n\n"
    if text.isspace():
        return None
    new_text = text.replace(" ", "@#$")
    return f"data: {new_text}\n\n"


@register_microservice(
    name="opea_service@llm_vllm",
    service_type=ServiceType.LLM,
    endpoint="/v1/chat/completions",
    host="0.0.0.0",
    port=9000,
)
async def llm_generate(input: Union[LLMParamsDoc, ChatCompletionRequest, SearchedDoc]):
    if logflag:
        logger.info(input)

    prompt_template = None
    access_token = (
        get_access_token(TOKEN_URL, CLIENTID, CLIENT_SECRET) if TOKEN_URL and CLIENTID and CLIENT_SECRET else None
    )
    headers = {}
    if access_token:
        headers = {"Authorization": f"Bearer {access_token}"}
    model_name = input.model if input.model else os.getenv("LLM_MODEL", "meta-llama/Meta-Llama-3-8B-Instruct")
    llm_endpoint = get_llm_endpoint(model_name)
    llm = VLLMOpenAI(
        openai_api_key="EMPTY", openai_api_base=llm_endpoint + "/v1", model_name=model_name, default_headers=headers
    )

    if not isinstance(input, SearchedDoc) and input.chat_template:
        prompt_template = PromptTemplate.from_template(input.chat_template)
        input_variables = prompt_template.input_variables

    if isinstance(input, SearchedDoc):
        if logflag:
            logger.info("[ SearchedDoc ] input from retriever microservice")

        prompt = input.initial_query

        if input.retrieved_docs:
            docs = [doc.text for doc in input.retrieved_docs]
            if logflag:
                logger.info(f"[ SearchedDoc ] combined retrieved docs: {docs}")

            prompt = ChatTemplate.generate_rag_prompt(input.initial_query, docs, model_name)

        # use default llm parameter for inference
        new_input = LLMParamsDoc(query=prompt)

        parameters = {
            "max_tokens": new_input.max_tokens,
            "top_p": new_input.top_p,
            "temperature": new_input.temperature,
            "frequency_penalty": new_input.frequency_penalty,
            "presence_penalty": new_input.presence_penalty,
        }

        if logflag:
            logger.info(f"[ SearchedDoc ] final input: {new_input}")

        if new_input.streaming:

            async def stream_generator():
                chat_response = ""
                async for text in llm.astream(new_input.query, **parameters):
                    if text not in ["<|im_end|>", "<|endoftext|>"]:
                        chat_response += text
                        chunk_repr = repr(text.encode("utf-8"))
                        if logflag:
                            logger.info(f"[ SearchedDoc ] chunk: {chunk_repr}")
                        yield f"data: {chunk_repr}\n\n"
                if logflag:
                    logger.info(f"[ SearchedDoc ] stream response: {chat_response}")
                yield "data: [DONE]\n\n"

            return StreamingResponse(stream_generator(), media_type="text/event-stream")

        else:
            response = await llm.ainvoke(new_input.query, **parameters)
            if logflag:
                logger.info(response)

            return GeneratedDoc(text=response, prompt=new_input.query)

    elif isinstance(input, LLMParamsDoc):
        if logflag:
            logger.info("[ LLMParamsDoc ] input from rerank microservice")

        prompt = input.query

        parameters = {
            "max_tokens": input.max_tokens,
            "top_p": input.top_p,
            "temperature": input.temperature,
            "frequency_penalty": input.frequency_penalty,
            "presence_penalty": input.presence_penalty,
        }

        if prompt_template:
            if sorted(input_variables) == ["context", "question"]:
                prompt = prompt_template.format(question=input.query, context="\n".join(input.documents))
            elif input_variables == ["question"]:
                prompt = prompt_template.format(question=input.query)
            else:
                logger.info(
                    f"[ LLMParamsDoc ] {prompt_template} not used, we only support 2 input variables ['question', 'context']"
                )
        else:
            if input.documents:
                # use rag default template
                prompt = ChatTemplate.generate_rag_prompt(input.query, input.documents, model_name)

        if input.streaming:

            async def stream_generator():
                chat_response = ""
                async for text in llm.astream(prompt, **parameters):
                    if text not in ["<|im_end|>", "<|endoftext|>"]:
                        chat_response += text
                        chunk_repr = repr(text.encode("utf-8"))
                        if logflag:
                            logger.info(f"[ LLMParamsDoc ] chunk: {chunk_repr}")
                        yield f"data: {chunk_repr}\n\n"
                if logflag:
                    logger.info(f"[ LLMParamsDoc ] stream response: {chat_response}")
                yield "data: [DONE]\n\n"

            return StreamingResponse(stream_generator(), media_type="text/event-stream")

        else:
            response = await llm.ainvoke(prompt, **parameters)
            if logflag:
                logger.info(response)

            return GeneratedDoc(text=response, prompt=input.query)


if __name__ == "__main__":
    opea_microservices["opea_service@llm_vllm"].start()
