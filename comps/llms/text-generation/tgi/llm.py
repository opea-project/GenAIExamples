# Copyright (C) 2024 Intel Corporation
# SPDX-License-Identifier: Apache-2.0

import os
import time

from fastapi.responses import StreamingResponse
from langchain_community.llms import HuggingFaceEndpoint
from langsmith import traceable

from comps import (
    GeneratedDoc,
    LLMParamsDoc,
    ServiceType,
    opea_microservices,
    register_microservice,
    register_statistics,
    statistics_dict,
)


@register_microservice(
    name="opea_service@llm_tgi",
    service_type=ServiceType.LLM,
    endpoint="/v1/chat/completions",
    host="0.0.0.0",
    port=9000,
)
@traceable(run_type="llm")
@register_statistics(names=["opea_service@llm_tgi"])
def llm_generate(input: LLMParamsDoc):
    start = time.time()
    llm_endpoint = os.getenv("TGI_LLM_ENDPOINT", "http://localhost:8080")
    llm = HuggingFaceEndpoint(
        endpoint_url=llm_endpoint,
        max_new_tokens=input.max_new_tokens,
        top_k=input.top_k,
        top_p=input.top_p,
        typical_p=input.typical_p,
        temperature=input.temperature,
        repetition_penalty=input.repetition_penalty,
        streaming=input.streaming,
        timeout=600,
    )

    if input.streaming:

        stream_gen_time = []

        async def stream_generator():
            chat_response = ""
            async for text in llm.astream(input.query):
                stream_gen_time.append(time.time() - start)
                chat_response += text
                chunk_repr = repr(text.encode("utf-8"))
                print(f"[llm - chat_stream] chunk:{chunk_repr}")
                yield f"data: {chunk_repr}\n\n"
            print(f"[llm - chat_stream] stream response: {chat_response}")
            statistics_dict["opea_service@llm_tgi"].append_latency(stream_gen_time[-1], stream_gen_time[0])
            yield "data: [DONE]\n\n"

        return StreamingResponse(stream_generator(), media_type="text/event-stream")
    else:
        response = llm.invoke(input.query)
        statistics_dict["opea_service@llm_tgi"].append_latency(time.time() - start, None)
        return GeneratedDoc(text=response, prompt=input.query)


if __name__ == "__main__":
    opea_microservices["opea_service@llm_tgi"].start()
