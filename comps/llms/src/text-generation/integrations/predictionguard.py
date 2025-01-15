# Copyright (C) 2024 Prediction Guard, Inc.
# SPDX-License-Identified: Apache-2.0

import os
import time

from fastapi import HTTPException
from fastapi.responses import StreamingResponse
from predictionguard import PredictionGuard

from comps import CustomLogger, OpeaComponent, OpeaComponentRegistry, ServiceType
from comps.cores.proto.api_protocol import ChatCompletionRequest

logger = CustomLogger("opea_textgen_predictionguard")
logflag = os.getenv("LOGFLAG", False)


@OpeaComponentRegistry.register("OPEATextGen_Predictionguard")
class OPEATextGen_Predictionguard(OpeaComponent):
    """A specialized OPEA TextGen component derived from OpeaComponent for interacting with Predictionguard services.

    Attributes:
        client (Predictionguard): An instance of the Predictionguard client for text generation.
    """

    def __init__(self, name: str, description: str, config: dict = None):
        super().__init__(name, ServiceType.LLM.name.lower(), description, config)
        self.client = PredictionGuard()
        health_status = self.check_health()
        if not health_status:
            logger.error("OPEATextGen_Predictionguard health check failed.")
        else:
            logger.info("OPEATextGen_Predictionguard health check success.")

    def check_health(self) -> bool:
        """Checks the health of the Predictionguard LLM service.

        Returns:
            bool: True if the service is reachable and healthy, False otherwise.
        """

        try:
            response = self.client.models.list()
            return response is not None
        except Exception as e:
            logger.error(e)
            logger.error("Health check failed")
            return False

    async def invoke(self, input: ChatCompletionRequest):
        """Invokes the Predictionguard LLM service to generate output for the provided input.

        Args:
            input (ChatCompletionRequest): The input text(s).
        """
        if isinstance(input.messages, str):
            messages = [
                {
                    "role": "system",
                    "content": "You are a helpful assistant. Your goal is to provide accurate, detailed, and safe responses to the user's queries.",
                },
                {"role": "user", "content": input.messages},
            ]
        else:
            messages = input.messages

        if input.stream:

            async def stream_generator():
                chat_response = ""
                for res in self.client.chat.completions.create(
                    model=input.model,
                    messages=messages,
                    max_tokens=input.max_tokens,
                    temperature=input.temperature,
                    top_p=input.top_p,
                    top_k=input.top_k,
                    stream=True,
                ):
                    if "choices" in res["data"] and "delta" in res["data"]["choices"][0]:
                        delta_content = res["data"]["choices"][0]["delta"]["content"]
                        chat_response += delta_content
                        yield f"data: {delta_content}\n\n"
                    else:
                        yield "data: [DONE]\n\n"

            return StreamingResponse(stream_generator(), media_type="text/event-stream")
        else:
            try:
                response = self.client.chat.completions.create(
                    model=input.model,
                    messages=messages,
                    max_tokens=input.max_tokens,
                    temperature=input.temperature,
                    top_p=input.top_p,
                    top_k=input.top_k,
                )
            except Exception as e:
                raise HTTPException(status_code=500, detail=str(e))

            return response
