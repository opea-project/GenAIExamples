# Copyright (C) 2024 Intel Corporation
# SPDX-License-Identifier: Apache-2.0

import os
from typing import List, Union

from langchain_huggingface.llms import HuggingFaceEndpoint

from comps import CustomLogger, GeneratedDoc, ServiceType, TextDoc, opea_microservices, register_microservice

logger = CustomLogger("guardrails_tgi")
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


@register_microservice(
    name="opea_service@wildguard_tgi",
    service_type=ServiceType.GUARDRAIL,
    endpoint="/v1/guardrails",
    host="0.0.0.0",
    port=9090,
    input_datatype=Union[GeneratedDoc, TextDoc],
    output_datatype=TextDoc,
)
def safety_guard(input: Union[GeneratedDoc, TextDoc]) -> TextDoc:
    if logflag:
        logger.info(input)

    if isinstance(input, GeneratedDoc):
        messages = INSTRUCTION_FORMAT.format(prompt=input.prompt, response=input.text)
    else:
        messages = INSTRUCTION_FORMAT.format(prompt=input.text, response="")
    response_input_guard = llm_guard.invoke(messages)

    if "Harmful request: yes" in response_input_guard or "Harmful response: yes" in response_input_guard:

        if logflag:
            logger.info("Violated policies: harmful")
        res = TextDoc(text="Violated policies: harmful, please check your input.", downstream_black_list=[".*"])
    else:
        res = TextDoc(text=input.text)
    if logflag:
        logger.info(res)
    return res


if __name__ == "__main__":
    safety_guard_endpoint = os.getenv("SAFETY_GUARD_ENDPOINT", "http://localhost:8080")
    safety_guard_model = os.getenv("SAFETY_GUARD_MODEL_ID", DEFAULT_MODEL)
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
    logger.info("guardrails - router] LLM initialized.")
    opea_microservices["opea_service@wildguard_tgi"].start()
