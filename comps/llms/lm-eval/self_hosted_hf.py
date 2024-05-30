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
import sys
from typing import List

import lm_eval.api.registry
import torch
from docarray import BaseDoc
from GenAIEval.evaluation.lm_evaluation_harness.lm_eval.models.huggingface import HFLM, GaudiHFModelAdapter

from comps import ServiceType, opea_microservices, opea_telemetry, register_microservice

lm_eval.api.registry.MODEL_REGISTRY["hf"] = HFLM
lm_eval.api.registry.MODEL_REGISTRY["gaudi-hf"] = GaudiHFModelAdapter


class LLMCompletionDoc(BaseDoc):
    batched_inputs: List
    logprobs: int = 10
    max_tokens: int = 0
    temperature: float = 0.0


model = os.getenv("MODEL", "")
model_args = os.getenv("MODEL_ARGS", "")
device = os.getenv("DEVICE", "")

llm = lm_eval.api.registry.get_model(model).create_from_arg_string(
    model_args,
    {
        "batch_size": 1,  # dummy
        "max_batch_size": None,
        "device": device,
    },
)


@register_microservice(
    name="opea_service@self_hosted_hf",
    service_type=ServiceType.LLM,
    endpoint="/v1/completions",
    host="0.0.0.0",
    port=9006,
)
@opea_telemetry
def llm_generate(input: LLMCompletionDoc):
    global llm
    batched_inputs = torch.tensor(input.batched_inputs, dtype=torch.long, device=llm.device)
    with torch.no_grad():
        # TODO, use model.generate.
        logits = llm._model_call(batched_inputs)

    logits = torch.nn.functional.log_softmax(logits, dim=-1)
    # Check if per-token argmax is exactly equal to continuation
    greedy_tokens = logits.argmax(dim=-1)
    logprobs = torch.gather(logits, 2, batched_inputs[:, 1:].unsqueeze(-1)).squeeze(-1)

    return {
        "greedy_tokens": greedy_tokens.detach().cpu().tolist(),
        "logprobs": logprobs.detach().cpu().tolist(),
        "batched_inputs": input.batched_inputs,
    }


if __name__ == "__main__":
    opea_microservices["opea_service@self_hosted_hf"].start()
