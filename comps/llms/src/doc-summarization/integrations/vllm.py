# Copyright (C) 2024 Intel Corporation
# SPDX-License-Identifier: Apache-2.0

import os

import requests
from langchain_community.llms import VLLMOpenAI

from comps import CustomLogger, DocSumLLMParams, GeneratedDoc, OpeaComponent, OpeaComponentRegistry, ServiceType

from .common import *

logger = CustomLogger("llm_docsum_vllm")
logflag = os.getenv("LOGFLAG", False)


@OpeaComponentRegistry.register("OPEADocSum_vLLM")
class OPEADocSum_vLLM(OPEADocSum):
    """A specialized OPEA DocSum vLLM component derived from OPEADocSum for interacting with vLLM services based on Lanchain VLLMOpenAI API.

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

    async def invoke(self, input: DocSumLLMParams):
        """Invokes the vLLM LLM service to generate summarization output for the provided input.

        Args:
            input (DocSumLLMParams): The input text(s).
        """
        headers = {}
        if self.access_token:
            headers = {"Authorization": f"Bearer {self.access_token}"}

        if input.stream and input.summary_type == "map_reduce":
            logger.info("Map Reduce mode don't support stream=True, set to stream=False")
            input.stream = False
        self.client = VLLMOpenAI(
            openai_api_key="EMPTY",
            openai_api_base=self.llm_endpoint + "/v1",
            model_name=MODEL_NAME,
            default_headers=headers,
            max_tokens=input.max_tokens,
            top_p=input.top_p,
            streaming=input.stream,
            temperature=input.temperature,
            presence_penalty=input.repetition_penalty,
        )
        result = await self.generate(input, self.client)

        return result
