# Copyright (C) 2024 Prediction Guard, Inc.
# SPDX-License-Identified: Apache-2.0

import os

import requests
from langchain_community.llms import VLLMOpenAI

from comps import CustomLogger, GeneratedDoc, OpeaComponent, OpeaComponentRegistry, ServiceType
from comps.cores.proto.api_protocol import ChatCompletionRequest

from .common import *

logger = CustomLogger("opea_faqgen_vllm")
logflag = os.getenv("LOGFLAG", False)


@OpeaComponentRegistry.register("OpeaFaqGenvLLM")
class OpeaFaqGenvLLM(OpeaFaqGen):
    """A specialized OPEA FAQGen vLLM component derived from OpeaFaqGen for interacting with vLLM services based on Lanchain VLLMOpenAI API.

    Attributes:
        client (vLLM): An instance of the vLLM client for text generation.
    """

    def check_health(self) -> bool:
        """Checks the health of the vLLM LLM service.

        Returns:
            bool: True if the service is reachable and healthy, False otherwise.
        """

        try:
            response = requests.get(f"{self.llm_endpoint}/health")
            if response.status_code == 200:
                return True
            else:
                return False
        except Exception as e:
            logger.error(e)
            logger.error("Health check failed")
            return False

    async def invoke(self, input: ChatCompletionRequest):
        """Invokes the vLLM LLM service to generate FAQ output for the provided input.

        Args:
            input (ChatCompletionRequest): The input text(s).
        """
        headers = {}
        if self.access_token:
            headers = {"Authorization": f"Bearer {self.access_token}"}

        self.client = VLLMOpenAI(
            openai_api_key="EMPTY",
            openai_api_base=self.llm_endpoint + "/v1",
            model_name=MODEL_NAME,
            default_headers=headers,
            max_tokens=input.max_tokens if input.max_tokens else 1024,
            top_p=input.top_p if input.top_p else 0.95,
            streaming=input.stream,
            temperature=input.temperature if input.temperature else 0.01,
        )
        result = await self.generate(input, self.client)

        return result
