# Copyright (C) 2024 Intel Corporation
# SPDX-License-Identifier: Apache-2.0
import json
import os

import requests

from comps import CustomLogger, OpeaComponent, OpeaComponentRegistry, ServiceType

logger = CustomLogger("opea_animation")
logflag = os.getenv("LOGFLAG", False)


@OpeaComponentRegistry.register("OPEA_ANIMATION")
class OpeaAnimation(OpeaComponent):
    """A specialized animation component derived from OpeaComponent."""

    def __init__(self, name: str, description: str, config: dict = None):
        super().__init__(name, ServiceType.ANIMATION.name.lower(), description, config)
        self.base_url = os.getenv("WAV2LIP_ENDPOINT", "http://localhost:7860")
        health_status = self.check_health()
        if not health_status:
            logger.error("OpeaAnimation health check failed.")

    async def invoke(self, input: str):
        """Invokes the animation service to generate embeddings for the animation input.

        Args:
            input (Audio Byte Str)
        """
        inputs = {"audio": input}

        response = requests.post(url=f"{self.base_url}/v1/wav2lip", data=json.dumps(inputs), proxies={"http": None})

        outfile = response.json()["wav2lip_result"]
        return outfile

    def check_health(self) -> bool:
        """Checks the health of the animation service.

        Returns:
            bool: True if the service is reachable and healthy, False otherwise.
        """
        try:
            response = requests.get(f"{self.base_url}/v1/health")
            # If status is 200, the service is considered alive
            if response.status_code == 200:
                return True
            else:
                return False
        except Exception as e:
            # Handle connection errors, timeouts, etc.
            logger.error(f"Health check failed: {e}")
        return False
