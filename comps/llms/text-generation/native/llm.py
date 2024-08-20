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
import sys

sys.path.append("/test/GenAIComps/")

import logging
import os
import threading
import time

import torch
from langchain_core.prompts import PromptTemplate
from template import ChatTemplate, args_dict, input_sentences
from utils import initialize_model

from comps import (
    GeneratedDoc,
    LLMParamsDoc,
    ServiceType,
    opea_microservices,
    register_microservice,
    register_statistics,
)

logflag = os.getenv("LOGFLAG", False)

logging.basicConfig(
    format="%(asctime)s - %(levelname)s - %(name)s - %(message)s",
    datefmt="%m/%d/%Y %H:%M:%S",
    level=logging.INFO,
)
logger = logging.getLogger(__name__)


class Args:
    def __init__(self, **entries):
        self.__dict__.update(entries)


model = None
assistant_model = None
tokenizer = None
generation_config = None
args = Args(**args_dict)
initialization_lock = threading.Lock()
initialized = False


def generate(
    input_query: list,
    device="hpu",
    use_lazy_mode=True,
    use_hpu_graphs=True,
    profiling_steps=0,
    profiling_warmup_steps=0,
    ignore_eos=True,
    profiling_record_shapes=False,
):
    """Generates sequences from the input sentences and returns them."""
    logger.info(f"[llm - generate] starting to inference with prompt {input_query}")
    encode_t0 = time.perf_counter()

    # Tokenization
    input_tokens = tokenizer.batch_encode_plus(input_query, return_tensors="pt", padding=True)
    encode_duration = time.perf_counter() - encode_t0
    logger.info(f"[llm - generate] input tokenized: {input_tokens}")

    # Move inputs to target device(s)
    for t in input_tokens:
        logger.info(f"[llm - generate] t: {t}")
        if torch.is_tensor(input_tokens[t]):
            logger.info("[llm - generate] input[t] is tensor")
            logger.info(f"[llm - generate] device: {model.device}")
            input_tokens[t] = input_tokens[t].to(model.device)

    logger.info("[llm - generate] inputs transferred.")

    iteration_times = []
    outputs = model.generate(
        **input_tokens,
        generation_config=generation_config,
        assistant_model=assistant_model,
        lazy_mode=use_lazy_mode,
        hpu_graphs=use_hpu_graphs,
        profiling_steps=profiling_steps,
        profiling_warmup_steps=profiling_warmup_steps,
        ignore_eos=ignore_eos,
        iteration_times=iteration_times,
        profiling_record_shapes=profiling_record_shapes,
    ).cpu()
    logger.info("[llm - generate] result generated")
    first_token_time = iteration_times[0] + encode_duration
    result = tokenizer.batch_decode(outputs, skip_special_tokens=True)
    logger.info(f"[llm - generate] result: {result}")
    logger.info(f"[llm - generate] Time to first token = {first_token_time*1000}ms")
    return result


def initialize():
    global model, assistant_model, tokenizer, generation_config, initialized
    with initialization_lock:
        if not initialized:
            # initialize model and tokenizer
            import habana_frameworks.torch.hpu as torch_hpu
            from optimum.habana.utils import HabanaProfile

            model, assistant_model, tokenizer, generation_config = initialize_model(args, logger)
            logger.info("[llm] model and tokenizer initialized.")

            # compilation and model warmup
            HabanaProfile.disable()
            logger.info("[llm - native] Graph compilation...")
            for _ in range(args.warmup):
                generate(input_sentences)
            logger.info("[llm - native] model warm up finished.")
            torch_hpu.synchronize()
            HabanaProfile.enable()
            logger.info("[llm - native] Ready to inference")
            res = generate(["What is Deep Learning?"])
            logger.info(f"[llm - native] test result: {res}")
            initialized = True


@register_microservice(
    name="opea_service@llm_native",
    service_type=ServiceType.LLM,
    endpoint="/v1/chat/completions",
    host="0.0.0.0",
    port=9000,
)
@register_statistics(names=["opea_service@llm_native"])
def llm_generate(input: LLMParamsDoc):
    initialize()
    if logflag:
        logger.info(input)
    prompt = input.query
    prompt_template = None
    if input.chat_template:
        prompt_template = PromptTemplate.from_template(input.chat_template)
        input_variables = prompt_template.input_variables
    if prompt_template:
        if sorted(input_variables) == ["context", "question"]:
            prompt = prompt_template.format(question=input.query, context="\n".join(input.documents))
        elif input_variables == ["question"]:
            prompt = prompt_template.format(question=input.query)
        else:
            logger.info(f"{prompt_template} not used, we only support 2 input variables ['question', 'context']")
    else:
        if input.documents:
            prompt = ChatTemplate.generate_rag_prompt(input.query, input.documents)
    res = generate([prompt])

    if logflag:
        logger.info(f"[llm - native] inference result: {res}")
    return GeneratedDoc(text=res[0], prompt=input.query)


if __name__ == "__main__":
    opea_microservices["opea_service@llm_native"].start()
