# Copyright (C) 2024 Intel Corporation
# SPDX-License-Identifier: Apache-2.0

import os

from fastapi.responses import StreamingResponse
from huggingface_hub import AsyncInferenceClient
from langchain.prompts import PromptTemplate

from comps import CustomLogger, GeneratedDoc, LLMParamsDoc, ServiceType, opea_microservices, register_microservice
from comps.cores.mega.utils import get_access_token

logger = CustomLogger("llm_docsum")
logflag = os.getenv("LOGFLAG", False)

# Environment variables
TOKEN_URL = os.getenv("TOKEN_URL")
CLIENTID = os.getenv("CLIENTID")
CLIENT_SECRET = os.getenv("CLIENT_SECRET")

templ_en = """Write a concise summary of the following:


"{text}"


CONCISE SUMMARY:"""

templ_zh = """请简要概括以下内容:


"{text}"


概况:"""


@register_microservice(
    name="opea_service@llm_docsum",
    service_type=ServiceType.LLM,
    endpoint="/v1/chat/docsum",
    host="0.0.0.0",
    port=9000,
)
async def llm_generate(input: LLMParamsDoc):
    if logflag:
        logger.info(input)
    if input.language in ["en", "auto"]:
        templ = templ_en
    elif input.language in ["zh"]:
        templ = templ_zh
    else:
        raise NotImplementedError('Please specify the input language in "en", "zh", "auto"')

    prompt_template = PromptTemplate.from_template(templ)
    prompt = prompt_template.format(text=input.query)

    if logflag:
        logger.info("After prompting:")
        logger.info(prompt)

    access_token = (
        get_access_token(TOKEN_URL, CLIENTID, CLIENT_SECRET) if TOKEN_URL and CLIENTID and CLIENT_SECRET else None
    )
    headers = {}
    if access_token:
        headers = {"Authorization": f"Bearer {access_token}"}
    llm_endpoint = os.getenv("TGI_LLM_ENDPOINT", "http://localhost:8080")
    llm = AsyncInferenceClient(model=llm_endpoint, timeout=600, headers=headers)

    text_generation = await llm.text_generation(
        prompt=prompt,
        stream=input.streaming,
        max_new_tokens=input.max_tokens,
        repetition_penalty=input.repetition_penalty,
        temperature=input.temperature,
        top_k=input.top_k,
        top_p=input.top_p,
        typical_p=input.typical_p,
    )

    if input.streaming:

        async def stream_generator():
            chat_response = ""
            async for text in text_generation:
                chat_response += text
                chunk_repr = repr(text.encode("utf-8"))
                if logflag:
                    logger.info(f"[ docsum - text_summarize ] chunk:{chunk_repr}")
                yield f"data: {chunk_repr}\n\n"
            if logflag:
                logger.info(f"[ docsum - text_summarize ] stream response: {chat_response}")
            yield "data: [DONE]\n\n"

        return StreamingResponse(stream_generator(), media_type="text/event-stream")
    else:
        if logflag:
            logger.info(text_generation)
        return GeneratedDoc(text=text_generation, prompt=input.query)


if __name__ == "__main__":
    opea_microservices["opea_service@llm_docsum"].start()
