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
from datetime import datetime

import torch
from fastapi.responses import StreamingResponse
from langsmith import traceable
from utils import initialize_model

from comps import GeneratedDoc, LLMParamsDoc, ServiceType, opea_microservices, register_microservice


def warmup():
    input_sentences = ["DeepSpeed is a machine learning framework", "He is working on", "He has a", "He got all"]
    input_tokens = tokenizer.batch_encode_plus(input_sentences, return_tensors="pt", padding=True)
    for t in input_tokens:
        if torch.is_tensor(input_tokens[t]):
            input_tokens[t] = input_tokens[t].to("hpu")
    for i in range(3):
        print(f"Current time: {datetime.now()}")
        print(f"Warming up {i+1}...")
        outputs = model.generate(
            **input_tokens,
            generation_config=generation_config,
            lazy_mode=True,
            hpu_graphs=True,
            profiling_steps=0,
            profiling_warmup_steps=0,
        ).cpu()
        res = tokenizer.batch_decode(outputs, skip_special_tokens=True)
        print(f"res: {res}")


@register_microservice(
    name="opea_service@llm_qwen",
    service_type=ServiceType.LLM,
    endpoint="/v1/chat/completions",
    host="0.0.0.0",
    port=8000,
)
@traceable(run_type="llm")
def llm_generate(input: LLMParamsDoc):
    input_query = input.query
    input_tokens = tokenizer.batch_encode_plus([input_query], return_tensors="pt", padding=True)
    for t in input_tokens:
        if torch.is_tensor(input_tokens[t]):
            input_tokens[t] = input_tokens[t].to("hpu")

    print(f"[llm - qwen] Current time: {datetime.now()}")
    output = model.generate(
        **input_tokens,
        generation_config=generation_config,
        lazy_mode=True,
        hpu_graphs=True,
        profiling_steps=0,
        profiling_warmup_steps=0,
    ).cpu()
    res = tokenizer.batch_decode(output, skip_special_tokens=True)[0]
    print(f"[llm - qwen] res: {res}")
    return res


if __name__ == "__main__":
    model, tokenizer, generation_config = initialize_model(
        model_name_or_path="Qwen/Qwen1.5-7B-Chat", max_new_tokens=128
    )
    import habana_frameworks.torch.hpu as torch_hpu

    print("[llm - qwen] model and tokenizer initialized.")

    from optimum.habana.utils import HabanaProfile

    # compilation stage disable profiling
    HabanaProfile.disable()
    # Compilation
    print("Graph compilation...")
    warmup()
    print("[llm - qwen] model warm up finished.")

    torch_hpu.synchronize()
    HabanaProfile.enable()
    print("[llm - qwen] Ready to inference")

    opea_microservices["opea_service@llm_qwen"].start()
