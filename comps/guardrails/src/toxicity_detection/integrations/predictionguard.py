# Copyright (C) 2024 Intel Corporation
# SPDX-License-Identifier: Apache-2.0

import asyncio
import os

from predictionguard import PredictionGuard

from comps import CustomLogger, OpeaComponent, OpeaComponentRegistry, ScoreDoc, ServiceType, TextDoc

logger = CustomLogger("opea_toxicity_detection_predictionguard")
logflag = os.getenv("LOGFLAG", False)


@OpeaComponentRegistry.register("PREDICTIONGUARD_TOXICITY_DETECTION")
class OpeaToxicityDetectionPredictionGuard(OpeaComponent):
    """A specialized toxicity detection component derived from OpeaComponent."""

    def __init__(self, name: str, description: str, config: dict = None):
        super().__init__(name, ServiceType.GUARDRAIL.name.lower(), description, config)
        self.client = PredictionGuard()
        health_status = self.check_health()
        if not health_status:
            logger.error("OpeaToxicityDetectionPredictionGuard health check failed.")

    async def invoke(self, input: TextDoc):
        """Invokes the toxicity detection for the input asynchronously.

        Args:
            input (TextDoc): An object containing text to check.

        Returns:
            ScoreDoc: A ScoreDoc instance with the toxicity score.
        """
        text = input.text
        result = await asyncio.to_thread(self.client.toxicity.check, text=text)
        return ScoreDoc(score=result["checks"][0]["score"])

    def check_health(self) -> bool:
        """Checks the health of the toxicity detection service from PredictionGuard.

        Returns:
            bool: True if the service returns a valid response, False otherwise.
        """
        try:
            if not self.client:
                return False
            # Send a request to do toxicity check
            response = self.client.toxicity.check(text="This is a perfectly fine statement.")

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
