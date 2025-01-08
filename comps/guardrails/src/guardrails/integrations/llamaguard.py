# Copyright (C) 2024 Intel Corporation
# SPDX-License-Identifier: Apache-2.0

import asyncio
import os
from typing import Union

from langchain_community.utilities.requests import JsonRequestsWrapper
from langchain_huggingface import ChatHuggingFace
from langchain_huggingface.llms import HuggingFaceEndpoint

from comps import CustomLogger, GeneratedDoc, OpeaComponent, OpeaComponentRegistry, ServiceType, TextDoc

logger = CustomLogger("opea_llama_guard")
logflag = os.getenv("LOGFLAG", False)


DEFAULT_MODEL = "meta-llama/LlamaGuard-7b"


def get_unsafe_dict(model_id=DEFAULT_MODEL):
    if model_id == "meta-llama/LlamaGuard-7b":
        return {
            "O1": "Violence and Hate",
            "O2": "Sexual Content",
            "O3": "Criminal Planning",
            "O4": "Guns and Illegal Weapons",
            "O5": "Regulated or Controlled Substances",
            "O6": "Self-Harm",
        }
    else:
        # Standard MLCommons taxonomy of hazard
        # https://mlcommons.org/2024/04/mlc-aisafety-v0-5-poc/
        return {
            "S1": "Violent Crimes",
            "S2": "Non-Violent Crimes",
            "S3": "Sex Crimes",
            "S4": "Child Exploitation",
            "S5": "Specialized Advice",
            "S6": "Privacy",
            "S7": "Intellectual Property",
            "S8": "Indiscriminate Weapons",
            "S9": "Hate",
            "S10": "Self-Harm",
            "S11": "Sexual Content",
        }


def get_tgi_service_model_id(endpoint_url, default=DEFAULT_MODEL):
    """Returns Hugging Face repo id for deployed service's info endpoint
    otherwise return default model."""
    try:
        requests = JsonRequestsWrapper()
        info_endpoint = os.path.join(endpoint_url, "info")
        model_info = requests.get(info_endpoint)
        return model_info["model_id"]
    except Exception as e:
        return default


@OpeaComponentRegistry.register("OPEA_LLAMA_GUARD")
class OpeaGuardrailsLlamaGuard(OpeaComponent):
    """A guardrails factulity alignment component derived from OpeaComponent."""

    def __init__(self, name: str, description: str, config: dict = None):
        super().__init__(name, ServiceType.GUARDRAIL.name.lower(), description, config)
        safety_guard_endpoint = os.getenv("SAFETY_GUARD_ENDPOINT", "http://localhost:8080")
        safety_guard_model = os.getenv("SAFETY_GUARD_MODEL_ID", get_tgi_service_model_id(safety_guard_endpoint))
        llm_guard = HuggingFaceEndpoint(
            endpoint_url=safety_guard_endpoint,
            max_new_tokens=100,
            top_k=1,
            top_p=0.95,
            typical_p=0.95,
            temperature=0.01,
            repetition_penalty=1.03,
        )
        # chat engine for server-side prompt templating
        self.llm_engine_hf = ChatHuggingFace(llm=llm_guard, model_id=safety_guard_model)
        health_status = self.check_health()
        if not health_status:
            logger.error("OpeaGuardrailsLlamaGuard health check failed.")

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
            messages = [{"role": "user", "content": input.prompt}, {"role": "assistant", "content": input.text}]
        else:
            messages = [{"role": "user", "content": input.text}]
        response = await asyncio.to_thread(self.llm_engine_hf.invoke, messages)
        response_input_guard = response.content

        if "unsafe" in response_input_guard:
            unsafe_dict = get_unsafe_dict(self.llm_engine_hf.model_id)
            policy_violation_level = response_input_guard.split("\n")[1].strip()
            policy_violations = unsafe_dict[policy_violation_level]
            if logflag:
                logger.info(f"Violated policies: {policy_violations}")
            res = TextDoc(
                text=f"Violated policies: {policy_violations}, please check your input.", downstream_black_list=[".*"]
            )
        else:
            res = TextDoc(text=input.text)
        if logflag:
            logger.info(res)
        return res

    def check_health(self) -> bool:
        """Checks the health of the Llama Guard service.

        This function verifies if the Llama Guard service is operational by
        sending a guardrails check request to the LLM engine. It evaluates the
        service's response to determine its health.

        Returns:
            bool:
                - True if the service is reachable and responds with a valid "safe" keyword.
                - False if the service is unreachable, the response is invalid, or an exception occurs.
        """
        try:
            if not self.llm_engine_hf:
                return False

            # Send a request to do guardrails check
            response = self.llm_engine_hf.invoke({"role": "user", "content": "The sky is blue."}).content

            if "safe" in response:
                return True
            else:
                return False

        except Exception as e:
            # Handle exceptions such as network errors or unexpected failures
            logger.error(f"Health check failed due to an exception: {e}")
            return False
