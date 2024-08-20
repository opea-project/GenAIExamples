# Copyright (C) 2024 Intel Corporation
# SPDX-License-Identifier: Apache-2.0

import os
import time

from fastapi.responses import StreamingResponse
from huggingface_hub import AsyncInferenceClient

from comps import (
    CustomLogger,
    LVMDoc,
    ServiceType,
    TextDoc,
    opea_microservices,
    register_microservice,
    register_statistics,
    statistics_dict,
)

logger = CustomLogger("lvm_tgi")
logflag = os.getenv("LOGFLAG", False)


@register_microservice(
    name="opea_service@lvm_tgi",
    service_type=ServiceType.LVM,
    endpoint="/v1/lvm",
    host="0.0.0.0",
    port=9399,
    input_datatype=LVMDoc,
    output_datatype=TextDoc,
)
@register_statistics(names=["opea_service@lvm_tgi"])
async def lvm(request: LVMDoc):
    if logflag:
        logger.info(request)
    start = time.time()
    stream_gen_time = []
    img_b64_str = request.image
    prompt = request.prompt
    max_new_tokens = request.max_new_tokens
    streaming = request.streaming
    repetition_penalty = request.repetition_penalty
    temperature = request.temperature
    top_k = request.top_k
    top_p = request.top_p

    image = f"data:image/png;base64,{img_b64_str}"
    image_prompt = f"![]({image})\n{prompt}\nASSISTANT:"

    if streaming:

        async def stream_generator():
            chat_response = ""
            text_generation = await lvm_client.text_generation(
                prompt=image_prompt,
                stream=streaming,
                max_new_tokens=max_new_tokens,
                repetition_penalty=repetition_penalty,
                temperature=temperature,
                top_k=top_k,
                top_p=top_p,
            )
            async for text in text_generation:
                stream_gen_time.append(time.time() - start)
                chat_response += text
                chunk_repr = repr(text.encode("utf-8"))
                if logflag:
                    logger.info(f"[llm - chat_stream] chunk:{chunk_repr}")
                yield f"data: {chunk_repr}\n\n"
            if logflag:
                logger.info(f"[llm - chat_stream] stream response: {chat_response}")
            statistics_dict["opea_service@lvm_tgi"].append_latency(stream_gen_time[-1], stream_gen_time[0])
            yield "data: [DONE]\n\n"

        return StreamingResponse(stream_generator(), media_type="text/event-stream")
    else:
        generated_str = await lvm_client.text_generation(
            image_prompt,
            max_new_tokens=max_new_tokens,
            repetition_penalty=repetition_penalty,
            temperature=temperature,
            top_k=top_k,
            top_p=top_p,
        )
        statistics_dict["opea_service@lvm_tgi"].append_latency(time.time() - start, None)
        if logflag:
            logger.info(generated_str)
        return TextDoc(text=generated_str)


if __name__ == "__main__":
    lvm_endpoint = os.getenv("LVM_ENDPOINT", "http://localhost:8399")
    lvm_client = AsyncInferenceClient(lvm_endpoint)
    logger.info("[LVM] LVM initialized.")
    opea_microservices["opea_service@lvm_tgi"].start()
