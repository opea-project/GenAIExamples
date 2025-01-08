# Copyright (C) 2024 Intel Corporation
# SPDX-License-Identifier: Apache-2.0

import asyncio
import os

from transformers import pipeline

from comps import CustomLogger, OpeaComponent, OpeaComponentRegistry, ServiceType, TextDoc

logger = CustomLogger("opea_bias_native")
logflag = os.getenv("LOGFLAG", False)


@OpeaComponentRegistry.register("OPEA_NATIVE_BIAS")
class OpeaBiasDetectionNative(OpeaComponent):
    """A specialized bias detection component derived from OpeaComponent."""

    def __init__(self, name: str, description: str, config: dict = None):
        super().__init__(name, ServiceType.GUARDRAIL.name.lower(), description, config)
        self.model = os.getenv("BIAS_DETECTION_MODEL", "valurank/distilroberta-bias")
        self.bias_pipeline = pipeline("text-classification", model=self.model, tokenizer=self.model)
        health_status = self.check_health()
        if not health_status:
            logger.error("OpeaBiasDetectionNative health check failed.")

    async def invoke(self, input: str):
        """Invokes the bias detection for the input.

        Args:
            input (Input Str)
        """
        toxic = await asyncio.to_thread(self.bias_pipeline, input)
        if toxic[0]["label"] == "BIASED":
            return TextDoc(text="Violated policies: bias, please check your input.", downstream_black_list=[".*"])
        else:
            return TextDoc(text=input)

    def check_health(self) -> bool:
        """Checks the health of the animation service.

        Returns:
            bool: True if the service is reachable and healthy, False otherwise.
        """
        if self.bias_pipeline:
            return True
        else:
            return False
