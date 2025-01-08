# Copyright (C) 2024 Intel Corporation
# SPDX-License-Identifier: Apache-2.0

import asyncio
import json
import os

from predictionguard import PredictionGuard

from comps import CustomLogger, OpeaComponent, OpeaComponentRegistry, PIIRequestDoc, PIIResponseDoc, ServiceType

logger = CustomLogger("opea_pii_detection_predictionguard")
logflag = os.getenv("LOGFLAG", False)


@OpeaComponentRegistry.register("PREDICTIONGUARD_PII_DETECTION")
class OpeaPiiDetectionPredictionGuard(OpeaComponent):
    """A specialized PII detection component derived from OpeaComponent."""

    def __init__(self, name: str, description: str, config: dict = None):
        super().__init__(name, ServiceType.GUARDRAIL.name.lower(), description, config)
        self.client = PredictionGuard()
        health_status = self.check_health()
        if not health_status:
            logger.error("OpeaPiiDetectionPredictionGuard health check failed.")

    async def invoke(self, input: PIIRequestDoc):
        """Asynchronously invokes PII (Personally Identifiable Information) detection for the given input.

        This function sends a request to detect PII content in the provided input. It processes
        the result to determine if PII was detected or if a sanitized version of the input text
        is available.

        Args:
            input (PIIRequestDoc):
                - Contains the `prompt` to be analyzed for PII detection.
                - Includes `replace` and `replace_method` options to handle potential PII.

        Returns:
            PIIResponseDoc:
                - If a sanitized version of the input (`new_prompt`) is available, it is returned.
                - If PII types and positions are detected, a detailed report (`detected_pii`) is returned.
                - Otherwise, the response format depends on the PII detection service output.
        """
        result = await asyncio.to_thread(
            self.client.pii.check, prompt=input.prompt, replace=input.replace, replace_method=input.replace_method
        )
        if "new_prompt" in result["checks"][0].keys():
            return PIIResponseDoc(new_prompt=result["checks"][0]["new_prompt"])
        elif "pii_types_and_positions" in result["checks"][0].keys():
            detected_pii = json.loads(result["checks"][0]["pii_types_and_positions"])
            return PIIResponseDoc(detected_pii=detected_pii)

    def check_health(self) -> bool:
        """Checks the health of the PII detection service from PredictionGuard.

        Returns:
            bool: True if the service returns a valid response, False otherwise.
        """
        try:
            if not self.client:
                return False

            # Send a request to do PII check
            response = self.client.pii.check(
                prompt="Hello, my name is John Doe and my SSN is 111-22-3333.",
                replace=True,
                replace_method="mask",
            )

            # Check if the response is a valid dictionary and contains the expected 'checks' key
            if isinstance(response, dict) and "checks" in response:
                return True
            else:
                # Handle the case where the response does not have the expected structure
                return False

        except Exception as e:
            # Handle exceptions such as network errors or unexpected failures
            logger.error(f"Health check failed due to an exception: {e}")
            return False
