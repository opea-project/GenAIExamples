# Copyright (c) 2024 Intel Corporation
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#    http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

import os

from langchain_huggingface import ChatHuggingFace
from langchain_huggingface.llms import HuggingFaceEndpoint
from langsmith import traceable

from comps import ServiceType, TextDoc, opea_microservices, register_microservice


def get_unsafe_dict(model_id="meta-llama/LlamaGuard-7b"):
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


@register_microservice(
    name="opea_service@guardrails_tgi_gaudi",
    service_type=ServiceType.GUARDRAIL,
    endpoint="/v1/guardrails",
    host="0.0.0.0",
    port=9090,
    input_datatype=TextDoc,
    output_datatype=TextDoc,
)
@traceable(run_type="llm")
def safety_guard(input: TextDoc) -> TextDoc:
    # chat engine for server-side prompt templating
    llm_engine_hf = ChatHuggingFace(llm=llm_guard)
    response_input_guard = llm_engine_hf.invoke([{"role": "user", "content": input.text}]).content
    if "unsafe" in response_input_guard:
        unsafe_dict = get_unsafe_dict(llm_engine_hf.model_id)
        policy_violation_level = response_input_guard.split("\n")[1].strip()
        policy_violations = unsafe_dict[policy_violation_level]
        print(f"Violated policies: {policy_violations}")
        res = TextDoc(text=f"Violated policies: {policy_violations}, please check your input.")
    else:
        res = TextDoc(text="safe")

    return res


if __name__ == "__main__":
    safety_guard_endpoint = os.getenv("SAFETY_GUARD_ENDPOINT", "http://localhost:8080")
    llm_guard = HuggingFaceEndpoint(
        endpoint_url=safety_guard_endpoint,
        max_new_tokens=100,
        top_k=1,
        top_p=0.95,
        typical_p=0.95,
        temperature=0.01,
        repetition_penalty=1.03,
    )
    print("guardrails - router] LLM initialized.")
    opea_microservices["opea_service@guardrails_tgi_gaudi"].start()
