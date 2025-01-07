# Copyright (C) 2024 Intel Corporation
# SPDX-License-Identifier: Apache-2.0

import asyncio
import os
import time

import requests
from fastapi.responses import StreamingResponse

from comps import CustomLogger, OpeaComponent, OpeaComponentRegistry, ServiceType
from comps.cores.proto.api_protocol import AudioSpeechRequest

logger = CustomLogger("opea_speecht5")
logflag = os.getenv("LOGFLAG", False)


@OpeaComponentRegistry.register("OPEA_SPEECHT5_TTS")
class OpeaSpeecht5Tts(OpeaComponent):
    """A specialized TTS (Text To Speech) component derived from OpeaComponent for SpeechT5 TTS services.

    Attributes:
        model_name (str): The name of the TTS model used.
    """

    def __init__(self, name: str, description: str, config: dict = None):
        super().__init__(name, ServiceType.TTS.name.lower(), description, config)
        self.base_url = os.getenv("TTS_ENDPOINT", "http://localhost:7055")
        health_status = self.check_health()
        if not health_status:
            logger.error("OpeaSpeecht5Tts health check failed.")

    async def invoke(
        self,
        request: AudioSpeechRequest,
    ) -> requests.models.Response:
        """Involve the TTS service to generate speech for the provided input."""
        # validate the request parameters
        if request.model not in ["microsoft/speecht5_tts"]:
            raise Exception("TTS model mismatch! Currently only support model: microsoft/speecht5_tts")
        if request.voice not in ["default", "male"] or request.speed != 1.0:
            logger.warning("Currently parameter 'speed' can only be 1.0 and 'voice' can only be default or male!")

        response = await asyncio.to_thread(
            requests.post,
            f"{self.base_url}/v1/audio/speech",
            json=request.dict(),
        )
        return response

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
