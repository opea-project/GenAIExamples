# Copyright (C) 2024 Intel Corporation
# SPDX-License-Identifier: Apache-2.0

import os
import time
from typing import Union

from fastapi import HTTPException
from fastapi.responses import StreamingResponse
from huggingface_hub import AsyncInferenceClient
from langchain_core.prompts import PromptTemplate
from template import ChatTemplate

from comps import (
    CustomLogger,
    LVMDoc,
    LVMSearchedMultimodalDoc,
    MetadataTextDoc,
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
async def lvm(request: Union[LVMDoc, LVMSearchedMultimodalDoc]) -> Union[TextDoc, MetadataTextDoc]:
    if logflag:
        logger.info(request)
    start = time.time()
    stream_gen_time = []

    if isinstance(request, LVMSearchedMultimodalDoc):
        if logflag:
            logger.info("[LVMSearchedMultimodalDoc ] input from retriever microservice")
        retrieved_metadatas = request.metadata
        if not retrieved_metadatas or len(retrieved_metadatas) == 0:
            # there is no video segments retrieved.
            # Raise HTTPException status_code 204
            # due to llava-tgi-gaudi should receive image as input; Otherwise, the generated text is bad.
            raise HTTPException(status_code=500, detail="There is no video segments retrieved given the query!")
        img_b64_str = retrieved_metadatas[0]["b64_img_str"]
        initial_query = request.initial_query
        context = retrieved_metadatas[0]["transcript_for_inference"]
        prompt = initial_query
        if request.chat_template is None:
            prompt = ChatTemplate.generate_multimodal_rag_on_videos_prompt(initial_query, context)
        else:
            prompt_template = PromptTemplate.from_template(request.chat_template)
            input_variables = prompt_template.input_variables
            if sorted(input_variables) == ["context", "question"]:
                prompt = prompt_template.format(question=initial_query, context=context)
            else:
                logger.info(
                    f"[ LVMSearchedMultimodalDoc ] {prompt_template} not used, we only support 2 input variables ['question', 'context']"
                )
        max_new_tokens = request.max_new_tokens
        streaming = request.streaming
        repetition_penalty = request.repetition_penalty
        temperature = request.temperature
        top_k = request.top_k
        top_p = request.top_p
        if logflag:
            logger.info(f"prompt generated for [LVMSearchedMultimodalDoc ] input from retriever microservice: {prompt}")

    else:
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
        if isinstance(request, LVMSearchedMultimodalDoc):
            retrieved_metadata = request.metadata[0]
            return_metadata = {}  # this metadata will be used to construct proof for generated text
            return_metadata["video_id"] = retrieved_metadata["video_id"]
            return_metadata["source_video"] = retrieved_metadata["source_video"]
            return_metadata["time_of_frame_ms"] = retrieved_metadata["time_of_frame_ms"]
            return_metadata["transcript_for_inference"] = retrieved_metadata["transcript_for_inference"]
            return MetadataTextDoc(text=generated_str, metadata=return_metadata)
        else:
            return TextDoc(text=generated_str)


if __name__ == "__main__":
    lvm_endpoint = os.getenv("LVM_ENDPOINT", "http://localhost:8399")
    lvm_client = AsyncInferenceClient(lvm_endpoint)
    logger.info("[LVM] LVM initialized.")
    opea_microservices["opea_service@lvm_tgi"].start()
