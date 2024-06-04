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


import copy
import os
import shutil
import time

import torch
from optimum.habana.checkpoint_utils import (
    get_ds_injection_policy,
    get_repo_root,
    model_is_optimized,
    model_on_meta,
    write_checkpoints_json,
)
from optimum.habana.utils import check_habana_frameworks_version, check_optimum_habana_min_version, set_seed
from transformers import AutoConfig, AutoModelForCausalLM, AutoTokenizer
from transformers.utils import check_min_version


def setup_env():
    # Will error if the minimal version of Transformers is not installed. Remove at your own risks.
    check_min_version("4.34.0")
    check_optimum_habana_min_version("1.9.0.dev0")
    # TODO: SW-167588 - WA for memory issue in hqt prep_model
    os.environ.setdefault("EXPERIMENTAL_WEIGHT_SHARING", "FALSE")

    # Tweak generation so that it runs faster on Gaudi
    from optimum.habana.transformers.modeling_utils import adapt_transformers_to_gaudi

    adapt_transformers_to_gaudi()


def setup_device():
    import habana_frameworks.torch.core as htcore

    return torch.device("hpu")


def get_torch_compiled_model(model):
    model.model = torch.compile(model.model, backend="hpu_backend")
    return model


def setup_model(model_name_or_path, model_dtype, model_kwargs):
    model = AutoModelForCausalLM.from_pretrained(model_name_or_path, torch_dtype=model_dtype, **model_kwargs)
    model = model.eval().to("hpu")

    from habana_frameworks.torch.hpu import wrap_in_hpu_graph

    if check_habana_frameworks_version("1.13.0") and model.config.model_type == "falcon":
        model = wrap_in_hpu_graph(model, hash_with_views=False)
    else:
        model = wrap_in_hpu_graph(model)

    if model.config.model_type == "llama":
        model = get_torch_compiled_model(model)

    return model


def setup_tokenizer(model_name_or_path, model):
    tokenizer_kwargs = {
        "revision": "main",
        "token": None,
    }
    tokenizer = AutoTokenizer.from_pretrained(model_name_or_path, **tokenizer_kwargs)
    if not model.config.is_encoder_decoder:
        tokenizer.padding_side = "left"
    # Some models like GPT2 do not have a PAD token so we have to set it if necessary
    if model.config.model_type == "llama":
        # unwind broken decapoda-research config
        model.generation_config.pad_token_id = 0
        model.generation_config.bos_token_id = 1
        model.generation_config.eos_token_id = 2
        tokenizer.bos_token_id = model.generation_config.bos_token_id
        tokenizer.eos_token_id = model.generation_config.eos_token_id
        tokenizer.pad_token_id = model.generation_config.pad_token_id
        tokenizer.pad_token = tokenizer.decode(tokenizer.pad_token_id)
        tokenizer.eos_token = tokenizer.decode(tokenizer.eos_token_id)
        tokenizer.bos_token = tokenizer.decode(tokenizer.bos_token_id)

    if tokenizer.pad_token is None:
        tokenizer.pad_token = tokenizer.eos_token
        model.generation_config.pad_token_id = model.generation_config.eos_token_id
    return tokenizer, model


def setup_generation_config(model, tokenizer, max_new_tokens):
    bad_words_ids = None
    force_words_ids = None

    is_optimized = model_is_optimized(model.config)
    # Generation configuration
    generation_config = copy.deepcopy(model.generation_config)
    generation_config.max_new_tokens = max_new_tokens
    generation_config.use_cache = True
    generation_config.static_shapes = is_optimized
    generation_config.bucket_size = -1
    generation_config.bucket_internal = True
    generation_config.do_sample = True
    generation_config.num_beams = 1
    generation_config.bad_words_ids = bad_words_ids
    generation_config.force_words_ids = force_words_ids
    generation_config.num_return_sequences = 1
    generation_config.trim_logits = True
    generation_config.attn_softmax_bf16 = True
    generation_config.limit_hpu_graphs = True
    generation_config.reuse_cache = False
    generation_config.reduce_recompile = False
    generation_config.use_flash_attention = False
    generation_config.flash_attention_recompute = True
    generation_config.flash_attention_causal_mask = True
    return generation_config


def initialize_model(model_name_or_path, max_new_tokens=128):
    init_start = time.perf_counter()
    setup_env()
    setup_device()
    set_seed(17)
    get_repo_root(model_name_or_path, local_rank=0, token=None)
    model_dtype = torch.bfloat16

    model_kwargs = {"revision": "main", "token": None, "device_map": "auto", "offload_folder": "/tmp/offload_folder/"}

    model = setup_model(model_name_or_path, model_dtype, model_kwargs)
    tokenizer, model = setup_tokenizer(model_name_or_path, model)
    generation_config = setup_generation_config(model, tokenizer, max_new_tokens)

    init_end = time.perf_counter()
    print(f"Model initialization took {(init_end - init_start):.3f}s")
    return model, tokenizer, generation_config
