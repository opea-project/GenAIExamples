# Copyright (C) 2024 Intel Corporation
# SPDX-License-Identifier: Apache-2.0

import json
import os
from typing import Union

import requests
from fastapi import HTTPException
from langchain_core.prompts import PromptTemplate

from comps import (
    CustomLogger,
    LVMDoc,
    LVMSearchedMultimodalDoc,
    MetadataTextDoc,
    OpeaComponent,
    OpeaComponentRegistry,
    ServiceType,
    TextDoc,
)

logger = CustomLogger("opea_llava")
logflag = os.getenv("LOGFLAG", False)


class ChatTemplate:

    @staticmethod
    def generate_multimodal_rag_on_videos_prompt(question: str, context: str, has_image: bool = False):

        if has_image:
            template = """The transcript associated with the image is '{context}'. {question}"""
        else:
            template = (
                """Refer to the following results obtained from the local knowledge base: '{context}'. {question}"""
            )

        return template.format(context=context, question=question)


@OpeaComponentRegistry.register("OPEA_LLAVA_LVM")
class OpeaLlavaLvm(OpeaComponent):
    """A specialized LVM component derived from OpeaComponent for LLaVA LVM services."""

    def __init__(self, name: str, description: str, config: dict = None):
        super().__init__(name, ServiceType.LVM.name.lower(), description, config)
        self.base_url = os.getenv("LVM_ENDPOINT", "http://localhost:8399")
        health_status = self.check_health()
        if not health_status:
            logger.error("OpeaLlavaLvm health check failed.")

    async def invoke(
        self,
        request: Union[LVMDoc, LVMSearchedMultimodalDoc],
    ) -> Union[TextDoc, MetadataTextDoc]:
        """Involve the LVM service to generate answer for the provided input."""
        if logflag:
            logger.info(request)
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
                logger.info(
                    f"prompt generated for [LVMSearchedMultimodalDoc ] input from retriever microservice: {prompt}"
                )

        else:
            img_b64_str = request.image
            prompt = request.prompt
            max_new_tokens = request.max_new_tokens

        inputs = {"img_b64_str": img_b64_str, "prompt": prompt, "max_new_tokens": max_new_tokens}
        # forward to the LLaVA server
        response = requests.post(url=f"{self.base_url}/generate", data=json.dumps(inputs), proxies={"http": None})

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

    def check_health(self) -> bool:
        """Checks the health of the embedding service.

        Returns:
            bool: True if the service is reachable and healthy, False otherwise.
        """
        try:
            response = requests.get(f"{self.base_url}/health")
            if response.status_code == 200:
                return True
            else:
                return False
        except Exception as e:
            # Handle connection errors, timeouts, etc.
            logger.error(f"Health check failed: {e}")
        return False
