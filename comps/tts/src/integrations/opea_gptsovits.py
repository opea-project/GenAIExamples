# Copyright (C) 2024 Intel Corporation
# SPDX-License-Identifier: Apache-2.0

import asyncio
import os
import time

import requests
from fastapi.responses import StreamingResponse

from comps import CustomLogger, OpeaComponent, OpeaComponentRegistry, ServiceType
from comps.cores.proto.api_protocol import AudioSpeechRequest

logger = CustomLogger("opea_gptsovits")
logflag = os.getenv("LOGFLAG", False)


@OpeaComponentRegistry.register("OPEA_GPTSOVITS_TTS")
class OpeaGptsovitsTts(OpeaComponent):
    """A specialized TTS (Text To Speech) component derived from OpeaComponent for GPTSoVITS TTS services.

    Attributes:
        model_name (str): The name of the TTS model used.
    """

    def __init__(self, name: str, description: str, config: dict = None):
        super().__init__(name, ServiceType.TTS.name.lower(), description, config)
        self.base_url = os.getenv("TTS_ENDPOINT", "http://localhost:9880")
        health_status = self.check_health()
        if not health_status:
            logger.error("OpeaGptsovitsTts health check failed.")

    async def invoke(
        self,
        request: AudioSpeechRequest,
    ) -> requests.models.Response:
        """Involve the TTS service to generate speech for the provided input."""
        # see https://github.com/Spycsh/GPT-SoVITS/blob/openai_compat/api.py#L948 for usage
        # make sure you change the refer_wav_path locally
        request.voice = None

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
