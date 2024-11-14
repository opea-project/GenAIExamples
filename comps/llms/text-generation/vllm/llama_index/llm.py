# Copyright (C) 2024 Intel Corporation
# SPDX-License-Identifier: Apache-2.0

import os

from fastapi.responses import StreamingResponse
from llama_index.llms.openai_like import OpenAILike

from comps import (
    CustomLogger,
    GeneratedDoc,
    LLMParamsDoc,
    ServiceType,
    opea_microservices,
    opea_telemetry,
    register_microservice,
)

logger = CustomLogger("llm_vllm_llamaindex")
logflag = os.getenv("LOGFLAG", False)


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
    name="opea_service@llm_vllm_llama_index",
    service_type=ServiceType.LLM,
    endpoint="/v1/chat/completions",
    host="0.0.0.0",
    port=9000,
)
async def llm_generate(input: LLMParamsDoc):
    if logflag:
        logger.info(input)
    llm_endpoint = os.getenv("vLLM_ENDPOINT", "http://localhost:8008")
    model_name = os.getenv("LLM_MODEL", "meta-llama/Meta-Llama-3-8B-Instruct")
    llm = OpenAILike(
        api_key="fake",
        api_base=llm_endpoint + "/v1",
        max_tokens=input.max_tokens,
        model=model_name,
        top_p=input.top_p,
        temperature=input.temperature,
        streaming=input.streaming,
    )

    if input.streaming:

        async def stream_generator():
            async for text in llm.astream_complete(input.query):
                if text.text not in ["<|im_end|>", "<|endoftext|>"]:
                    output = text.text
                    yield f"data: {output}\n\n"
            if logflag:
                logger.info(f"[llm - chat_stream] stream response: {output}")
            yield "data: [DONE]\n\n"

        return StreamingResponse(stream_generator(), media_type="text/event-stream")
    else:
        response = await llm.acomplete(input.query)
        response = response.text
        if logflag:
            logger.info(response)
        return GeneratedDoc(text=response, prompt=input.query)


if __name__ == "__main__":
    opea_microservices["opea_service@llm_vllm_llama_index"].start()
