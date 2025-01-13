# Copyright (C) 2024 Intel Corporation
# SPDX-License-Identifier: Apache-2.0

import json
import os
from typing import Union

import requests

from comps import CustomLogger, LVMDoc, OpeaComponent, OpeaComponentRegistry, ServiceType, TextDoc

logger = CustomLogger("opea_predictionguard")
logflag = os.getenv("LOGFLAG", False)


@OpeaComponentRegistry.register("OPEA_PREDICTION_GUARD_LVM")
class OpeaPredictionguardLvm(OpeaComponent):
    """A specialized LVM component derived from OpeaComponent for Predictionguard services."""

    def __init__(self, name: str, description: str, config: dict = None):
        super().__init__(name, ServiceType.LVM.name.lower(), description, config)
        self.base_url = os.getenv("LVM_ENDPOINT", "http://localhost:9399")
        health_status = self.check_health()
        if not health_status:
            logger.error("OpeaPredictionguardLvm health check failed.")

    async def invoke(
        self,
        request: Union[LVMDoc],
    ) -> Union[TextDoc]:
        """Involve the LVM service to generate answer for the provided input."""
        if logflag:
            logger.info(request)

        inputs = {"image": request.image, "prompt": request.prompt, "max_new_tokens": request.max_new_tokens}
        # forward to the PredictionGuard server
        response = requests.post(url=f"{self.base_url}/v1/lvm", data=json.dumps(inputs), proxies={"http": None})

        result = response.json()["text"]
        if logflag:
            logger.info(result)

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
