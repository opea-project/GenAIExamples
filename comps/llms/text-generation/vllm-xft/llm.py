# Copyright (C) 2024 Intel Corporation
# SPDX-License-Identifier: Apache-2.0

import os

from fastapi.responses import StreamingResponse
from langchain_community.llms import VLLMOpenAI
from langsmith import traceable

from comps import GeneratedDoc, LLMParamsDoc, ServiceType, opea_microservices, register_microservice


@register_microservice(
    name="opea_service@llm_vllm_xft",
    service_type=ServiceType.LLM,
    endpoint="/v1/chat/completions",
    host="0.0.0.0",
    port=9000,
)
@traceable(run_type="llm")
def llm_generate(input: LLMParamsDoc):
    llm_endpoint = os.getenv("vLLM_LLM_ENDPOINT", "http://localhost:18688")
    llm = VLLMOpenAI(
        openai_api_key="EMPTY",
        openai_api_base=llm_endpoint + "/v1",
        max_tokens=input.max_new_tokens,
        model_name="xft",
        top_p=input.top_p,
        temperature=input.temperature,
        presence_penalty=input.repetition_penalty,
        streaming=input.streaming,
    )

    if input.streaming:

        def stream_generator():
            chat_response = ""
            for text in llm.stream(input.query):
                chat_response += text
                chunk_repr = repr(text.encode("utf-8"))
                print(f"[llm - chat_stream] chunk:{chunk_repr}")
                yield f"data: {chunk_repr}\n\n"
            print(f"[llm - chat_stream] stream response: {chat_response}")
            yield "data: [DONE]\n\n"

        return StreamingResponse(stream_generator(), media_type="text/event-stream")
    else:
        response = llm.invoke(input.query)
        return GeneratedDoc(text=response, prompt=input.query)


if __name__ == "__main__":
    opea_microservices["opea_service@llm_vllm_xft"].start()
