# Copyright (C) 2024 Intel Corporation
# SPDX-License-Identifier: Apache-2.0

import asyncio
import os
from typing import Union

from langchain_community.utilities.requests import JsonRequestsWrapper
from langchain_huggingface import ChatHuggingFace
from langchain_huggingface.llms import HuggingFaceEndpoint

from comps import CustomLogger, GeneratedDoc, OpeaComponent, OpeaComponentRegistry, ServiceType, TextDoc

logger = CustomLogger("opea_wild_guard")
logflag = os.getenv("LOGFLAG", False)

DEFAULT_MODEL = "allenai/wildguard"
INSTRUCTION_FORMAT = """<s><|user|>
[INST] You are a classifier for analyzing interactions between humans and LLMs. Given a request from a human user and a response from an LLM assistant, determine 1) whether the human user's request is harmful, 2) whether the AI assistant's response is a refusal, and 3) whether the AI assistant's response is harmful.

Human user:
{prompt}

AI assistant:
{response}

---

Answers: [/INST]
<|assistant|>
"""


@OpeaComponentRegistry.register("OPEA_WILD_GUARD")
class OpeaGuardrailsWildGuard(OpeaComponent):
    """A specialized guardrails component derived from OpeaComponent."""

    def __init__(self, name: str, description: str, config: dict = None):
        super().__init__(name, ServiceType.GUARDRAIL.name.lower(), description, config)
        safety_guard_endpoint = os.getenv("SAFETY_GUARD_ENDPOINT", "http://localhost:8080")
        safety_guard_model = os.getenv("SAFETY_GUARD_MODEL_ID", DEFAULT_MODEL)
        self.llm_guard = HuggingFaceEndpoint(
            endpoint_url=safety_guard_endpoint,
            max_new_tokens=100,
            top_k=1,
            top_p=0.95,
            typical_p=0.95,
            temperature=0.01,
            repetition_penalty=1.03,
        )
        # chat engine for server-side prompt templating
        health_status = self.check_health()
        if not health_status:
            logger.error("OpeaGuardrailsWildGuard health check failed.")

    async def invoke(self, input: Union[GeneratedDoc, TextDoc]):
        """Asynchronously invokes guardrails checks for the input.

        This function sends the input to the LLM engine for guardrails validation
        to check if the content adheres to defined policies. If violations are
        detected, the function returns a `TextDoc` object with details of the violated
        policies; otherwise, it returns the original input.

        Args:
            input (Union[GeneratedDoc, TextDoc]):
                - `GeneratedDoc`: Contains both a `prompt` and `text` to be validated.
                - `TextDoc`: Contains a single `text` input to be validated.

        Returns:
            TextDoc:
                - If the input passes the policy checks, the original `text` is returned.
                - If the input violates policies, a message indicating the violated policies
                and a downstream blacklist (`downstream_black_list`) are included.
        """
        if isinstance(input, GeneratedDoc):
            messages = INSTRUCTION_FORMAT.format(prompt=input.prompt, response=input.text)
        else:
            messages = INSTRUCTION_FORMAT.format(prompt=input.text, response="")
        response_input_guard = await asyncio.to_thread(self.llm_guard.invoke, messages)

        if "Harmful request: yes" in response_input_guard or "Harmful response: yes" in response_input_guard:

            if logflag:
                logger.info("Violated policies: harmful")
            res = TextDoc(text="Violated policies: harmful, please check your input.", downstream_black_list=[".*"])
        else:
            res = TextDoc(text=input.text)
        if logflag:
            logger.info(res)
        return res

    def check_health(self) -> bool:
        """Checks the health of the Wild Guard service.

        This function verifies if the Wild Guard service is operational by
        sending a guardrails check request to the LLM engine. It evaluates the
        service's response to determine its health.

        Returns:
            bool:
                - True if the service is reachable and responds with a valid "safe" keyword.
                - False if the service is unreachable, the response is invalid, or an exception occurs.
        """
        try:
            if not self.llm_guard:
                return False

            # Send a request to do guardrails check
            response = self.llm_guard.invoke("The sky is blue.")

            if "safe" in response:
                return True
            else:
                return False

        except Exception as e:
            # Handle exceptions such as network errors or unexpected failures
            logger.error(f"Health check failed due to an exception: {e}")
            return False
