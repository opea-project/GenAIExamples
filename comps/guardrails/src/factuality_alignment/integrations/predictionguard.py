# Copyright (C) 2024 Intel Corporation
# SPDX-License-Identifier: Apache-2.0

import asyncio
import os

from predictionguard import PredictionGuard

from comps import CustomLogger, FactualityDoc, OpeaComponent, OpeaComponentRegistry, ScoreDoc, ServiceType

logger = CustomLogger("opea_factulity_predictionguard")
logflag = os.getenv("LOGFLAG", False)


@OpeaComponentRegistry.register("OPEA_FACTUALITY_PREDICTIONGUARD")
class OpeaFactualityPredictionGuard(OpeaComponent):
    """A specialized factulity alignment component derived from OpeaComponent."""

    def __init__(self, name: str, description: str, config: dict = None):
        super().__init__(name, ServiceType.GUARDRAIL.name.lower(), description, config)
        self.client = PredictionGuard()
        health_status = self.check_health()
        if not health_status:
            logger.error("OpeaFactualityPredictionGuard health check failed.")

    async def invoke(self, input: FactualityDoc):
        """Invokes the factulity alignment for the input asynchronously.

        Args:
            input (FactualityDoc): An object containing the reference and text to check.

        Returns:
            ScoreDoc: A ScoreDoc instance with the factuality score.
        """
        reference = input.reference
        text = input.text
        result = await asyncio.to_thread(self.client.factuality.check, reference=reference, text=text)
        return ScoreDoc(score=result["checks"][0]["score"])

    def check_health(self) -> bool:
        """Checks the health of the Prediction Guard factulity service.

        Returns:
            bool: True if the service returns a valid response, False otherwise.
        """
        try:
            if not self.client:
                return False
            # Send a request to do factuality check
            response = self.client.factuality.check(reference="The sky is blue.", text="The sky is green.")

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
