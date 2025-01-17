# Copyright (C) 2025 Intel Corporation
# SPDX-License-Identifier: Apache-2.0

import os
from typing import Union

import requests
from fastapi.responses import StreamingResponse
from langchain.schema import HumanMessage, SystemMessage
from langchain_community.llms import VLLMOpenAI
from langchain_core.prompts import ChatPromptTemplate, PromptTemplate

from comps import (
    CustomLogger,
    GeneratedDoc,
    LLMParamsDoc,
    OpeaComponent,
    OpeaComponentRegistry,
    SearchedDoc,
    ServiceType,
)
from comps.cores.proto.api_protocol import ChatCompletionRequest
from comps.guardrails.src.hallucination_detection.integrations.template import ChatTemplate

logger = CustomLogger("opea_hallucination_guard")
logflag = os.getenv("LOGFLAG", False)

llm_endpoint = os.getenv("vLLM_ENDPOINT", "http://localhost:8008")
model_name = os.getenv("LLM_MODEL", "meta-llama/Meta-Llama-3-8B-Instruct")
llm = VLLMOpenAI(openai_api_key="EMPTY", openai_api_base=llm_endpoint + "/v1", model_name=model_name)


@OpeaComponentRegistry.register("OPEA_HALLUCINATION_GUARD")
class OpeaHallucinationGuard(OpeaComponent):
    """A specialized hallucination detection component derived from OpeaComponent."""

    def __init__(self, name: str, description: str, config: dict = None):
        super().__init__(name, ServiceType.LLM.name.lower(), description, config)
        self.model = os.getenv("LLM_MODEL", "meta-llama/Meta-Llama-3-8B-Instruct")
        health_status = self.check_health()
        if not health_status:
            logger.error("OpenAIHallucinationGuard health check failed.")

    async def invoke(self, input: Union[LLMParamsDoc, ChatCompletionRequest, SearchedDoc]):
        """Invokes the hallucination detection for the input.

        Args:
            input (Union[LLMParamsDoc, ChatCompletionRequest, SearchedDoc])
        """
        if logflag:
            logger.info(f"Input received: {input}")

        if isinstance(input, ChatCompletionRequest):
            if logflag:
                logger.info("[ ChatCompletionRequest ] input from user")

            headers = {"Content-Type": "application/json"}
            payload = {}
            payload["messages"] = input.messages
            payload["max_tokens"] = input.max_tokens
            payload["model"] = input.model
            response = requests.post(llm_endpoint + "/v1/chat/completions", json=payload, headers=headers)

            if logflag:
                logger.info(response.text)

            return GeneratedDoc(text=response.json()["choices"][0]["message"]["content"], prompt="")
        else:
            logger.info("[ UNKNOWN ] input from user")

    def check_health(self) -> bool:
        """Checks the health of the hallucination detection service.

        Returns:
            bool: True if the service is reachable and healthy, False otherwise.
        """
        try:
            response = requests.get(llm_endpoint + "health")
            if response.status_code == 200:
                return True
            else:
                return False
        except Exception as e:
            logger.error(f"Health check failed due to an exception: {e}")
            return False
