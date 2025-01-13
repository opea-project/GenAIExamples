# Copyright (C) 2024 Intel Corporation
# SPDX-License-Identifier: Apache-2.0

import os
import time
from typing import Union

import requests
from fastapi import HTTPException
from fastapi.responses import StreamingResponse
from huggingface_hub import AsyncInferenceClient
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
    statistics_dict,
)

logger = CustomLogger("opea_tgi_llava")
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


@OpeaComponentRegistry.register("OPEA_TGI_LLAVA_LVM")
class OpeaTgiLlavaLvm(OpeaComponent):
    """A specialized TGI LVM component derived from OpeaComponent for LLaVA LVM services."""

    def __init__(self, name: str, description: str, config: dict = None):
        super().__init__(name, ServiceType.LVM.name.lower(), description, config)
        self.base_url = os.getenv("LVM_ENDPOINT", "http://localhost:8399")
        self.lvm_client = AsyncInferenceClient(self.base_url)
        health_status = self.check_health()
        if not health_status:
            logger.error("OpeaTgiLlavaLvm health check failed.")

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
            stream = request.stream
            repetition_penalty = request.repetition_penalty
            temperature = request.temperature
            top_k = request.top_k
            top_p = request.top_p
            if logflag:
                logger.info(
                    f"prompt generated for [LVMSearchedMultimodalDoc ] input from retriever microservice: {prompt}"
                )

        else:
            img_b64_str = request.image
            prompt = request.prompt
            max_new_tokens = request.max_new_tokens
            stream = request.stream
            repetition_penalty = request.repetition_penalty
            temperature = request.temperature
            top_k = request.top_k
            top_p = request.top_p

        if not img_b64_str:
            # Work around an issue where LLaVA-NeXT is not providing good responses when prompted without an image.
            # Provide an image and then instruct the model to ignore the image. The base64 string below is the encoded png:
            # https://raw.githubusercontent.com/opea-project/GenAIExamples/refs/tags/v1.0/AudioQnA/ui/svelte/src/lib/assets/icons/png/audio1.png
            img_b64_str = "iVBORw0KGgoAAAANSUhEUgAAADUAAAAlCAYAAADiMKHrAAAACXBIWXMAAAsTAAALEwEAmpwYAAAAAXNSR0IArs4c6QAAAARnQU1BAACxjwv8YQUAAAKPSURBVHgB7Zl/btowFMefnUTqf+MAHYMTjN4gvcGOABpM+8E0doLSE4xpsE3rKuAG3KC5Ad0J6MYOkP07YnvvhR9y0lVzupTIVT5SwDjB9fd97WfsMkCef1rUXM8dY9HHK4hWUevzi/oVWAqnF8fzLmAtiPA3Aq0lFsVA1fRKxlgNLIbDPaQUZQuu6YO98aIipHOiFGtIqaYfn1UnUCDds6WPyeANlTFbv9WztbFTK+HNUVAPiz7nbPzq7HsPCoKWIBREGfsJXZit5xT07X0jp6iRdIbEHOnjyyD97OvzH00lVS2K5OS2ax11cBXxJgYxlEIE6XZclzdTX6n8XjkkcEIfbj2nMO0/SNd1vy4vsCNjYPyEovfyy88GZIQCSKOCMf6ORgStoboLJuSWKDYCfK2q4jjrMZ+GOh7Pib/gek5DHxVUJtcgA7mJ4kwZRbN7viQXFzQn0Nl52gXG4Fo7DKAYp0yI3VHQ16oaWV0wYa+iGE8nG+wAdx5DzpS/KGyhFGULpShbKEXZQinqLlBK/IKc2asoh4sZvoXJWhlAzuxV1KBVD3HrfYTFAK8ZHgu0hu36DHLG+Izinw250WUkXHJht02QUnxLP7fZxR7f1I6S7Ir2GgmYvIQM5OYUuYBdainATq2ZjTqPBlnbGXYeBrg9Od18DKmc1U0jpw4OIIwEJFxQSl2b4MN2lf74fw8nFNbHt/5N9xWKTZvJ2S6YZk6RC3j2cKpVhSIShZ0mea6caCOCAjyNHd5gPPxGncMBTvI6hunYdaJ6kf8VoSCP2odxX6RkR6NOtanfj13EswKVqEQrPzzFL1lK+YvCFraiEqs8TrwQLGYraqpX4kr/Hixml+63Z+CoM9DTo438AUmP+KyMWT+tAAAAAElFTkSuQmCC"
            prompt = f"Please disregard the image and answer the question. {prompt}"

        image = f"data:image/png;base64,{img_b64_str}"
        image_prompt = f"![]({image})\n{prompt}\nASSISTANT:"

        if stream:
            t_start = time.time()

            async def stream_generator(time_start):
                first_token_latency = None
                chat_response = ""
                text_generation = await self.lvm_client.text_generation(
                    prompt=image_prompt,
                    stream=stream,
                    max_new_tokens=max_new_tokens,
                    repetition_penalty=repetition_penalty,
                    temperature=temperature,
                    top_k=top_k,
                    top_p=top_p,
                )
                async for text in text_generation:
                    if first_token_latency is None:
                        first_token_latency = time.time() - time_start
                    chat_response += text
                    chunk_repr = repr(text.encode("utf-8"))
                    if logflag:
                        logger.info(f"[llm - chat_stream] chunk:{chunk_repr}")
                    yield f"data: {chunk_repr}\n\n"
                if logflag:
                    logger.info(f"[llm - chat_stream] stream response: {chat_response}")
                statistics_dict["opea_service@lvm"].append_latency(time.time() - time_start, first_token_latency)
                yield "data: [DONE]\n\n"

            return StreamingResponse(stream_generator(t_start), media_type="text/event-stream")
        else:
            generated_str = await self.lvm_client.text_generation(
                image_prompt,
                max_new_tokens=max_new_tokens,
                repetition_penalty=repetition_penalty,
                temperature=temperature,
                top_k=top_k,
                top_p=top_p,
            )
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
