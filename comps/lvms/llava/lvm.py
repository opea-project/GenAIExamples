# Copyright (C) 2024 Intel Corporation
# SPDX-License-Identifier: Apache-2.0


import json
import os
import time
from typing import Union

import requests
from fastapi import HTTPException
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

logger = CustomLogger("lvm")
logflag = os.getenv("LOGFLAG", False)


@register_microservice(
    name="opea_service@lvm",
    service_type=ServiceType.LVM,
    endpoint="/v1/lvm",
    host="0.0.0.0",
    port=9399,
)
@register_statistics(names=["opea_service@lvm"])
async def lvm(request: Union[LVMDoc, LVMSearchedMultimodalDoc]) -> Union[TextDoc, MetadataTextDoc]:
    if logflag:
        logger.info(request)
    start = time.time()
    if isinstance(request, LVMSearchedMultimodalDoc):
        if logflag:
            logger.info("[LVMSearchedMultimodalDoc ] input from retriever microservice")
        retrieved_metadatas = request.metadata
        if retrieved_metadatas is None or len(retrieved_metadatas) == 0:
            # there is no video segments retrieved.
            # Raise HTTPException status_code 204
            # due to llava-tgi-gaudi should receive image as input; Otherwise, the generated text is bad.
            raise HTTPException(status_code=500, detail="There is no video segments retrieved given the query!")

        img_b64_str = retrieved_metadatas[0]["b64_img_str"]
        has_image = img_b64_str != ""
        initial_query = request.initial_query
        context = retrieved_metadatas[0]["transcript_for_inference"]
        prompt = initial_query
        if request.chat_template is None:
            prompt = ChatTemplate.generate_multimodal_rag_on_videos_prompt(initial_query, context, has_image)
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
        if logflag:
            logger.info(f"prompt generated for [LVMSearchedMultimodalDoc ] input from retriever microservice: {prompt}")

    else:
        img_b64_str = request.image
        prompt = request.prompt
        max_new_tokens = request.max_new_tokens

    inputs = {"img_b64_str": img_b64_str, "prompt": prompt, "max_new_tokens": max_new_tokens}
    # forward to the LLaVA server
    response = requests.post(url=f"{lvm_endpoint}/generate", data=json.dumps(inputs), proxies={"http": None})

    statistics_dict["opea_service@lvm"].append_latency(time.time() - start, None)
    result = response.json()["text"]
    if logflag:
        logger.info(result)
    if isinstance(request, LVMSearchedMultimodalDoc):
        retrieved_metadata = request.metadata[0]
        return_metadata = {}  # this metadata will be used to construct proof for generated text
        return_metadata["video_id"] = retrieved_metadata["video_id"]
        return_metadata["source_video"] = retrieved_metadata["source_video"]
        return_metadata["time_of_frame_ms"] = retrieved_metadata["time_of_frame_ms"]
        return_metadata["transcript_for_inference"] = retrieved_metadata["transcript_for_inference"]
        return MetadataTextDoc(text=result, metadata=return_metadata)
    else:
        return TextDoc(text=result)


if __name__ == "__main__":
    lvm_endpoint = os.getenv("LVM_ENDPOINT", "http://localhost:8399")

    logger.info("[LVM] LVM initialized.")
    opea_microservices["opea_service@lvm"].start()
