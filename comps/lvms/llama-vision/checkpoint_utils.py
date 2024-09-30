# Copyright (C) 2024 Intel Corporation
# SPDX-License-Identifier: Apache-2.0

import json
import os
from pathlib import Path

import torch
from huggingface_hub import list_repo_files, snapshot_download
from transformers import modeling_utils
from transformers.utils import is_offline_mode


def get_repo_root(model_name_or_path, local_rank=-1, token=None):
    """Downloads the specified model checkpoint and returns the repository where it was downloaded."""
    if Path(model_name_or_path).is_dir():
        # If it is a local model, no need to download anything
        return model_name_or_path
    else:
        # Checks if online or not
        if is_offline_mode():
            if local_rank == 0:
                print("Offline mode: forcing local_files_only=True")

        # Only download PyTorch weights by default
        if any(
            ".safetensors" in filename for filename in list_repo_files(model_name_or_path, token=token)
        ):  # Some models like Falcon-180b are in only safetensors format
            allow_patterns = ["*.safetensors"]
        elif any(".bin" in filename for filename in list_repo_files(model_name_or_path, token=token)):
            allow_patterns = ["*.bin"]
        else:
            raise TypeError("Only PyTorch models are supported")

        # Download only on first process
        if local_rank in [-1, 0]:
            cache_dir = snapshot_download(
                model_name_or_path,
                local_files_only=is_offline_mode(),
                cache_dir=os.getenv("TRANSFORMERS_CACHE", None),
                allow_patterns=allow_patterns,
                max_workers=16,
                token=token,
            )
            if local_rank == -1:
                # If there is only one process, then the method is finished
                return cache_dir

        # Make all processes wait so that other processes can get the checkpoint directly from cache
        if torch.distributed.is_initialized():
            torch.distributed.barrier()

        return snapshot_download(
            model_name_or_path,
            local_files_only=is_offline_mode(),
            cache_dir=os.getenv("TRANSFORMERS_CACHE", None),
            allow_patterns=allow_patterns,
            token=token,
        )


def get_checkpoint_files(model_name_or_path, local_rank, token=None):
    cached_repo_dir = get_repo_root(model_name_or_path, local_rank=local_rank, token=token)

    # Extensions: .bin | .safetensors | .pt
    # Creates a list of paths from all downloaded files in cache dir

    if any(file.suffix == ".bin" for file in Path(cached_repo_dir).rglob("*")):
        (name, ext) = os.path.splitext(modeling_utils.WEIGHTS_NAME)
    elif any(file.suffix == ".safetensors" for file in Path(cached_repo_dir).rglob("*")):
        (name, ext) = os.path.splitext(modeling_utils.SAFE_WEIGHTS_NAME)
    else:
        (name, ext) = ("*", ".pt")

    file_list = [
        str(entry)
        for entry in Path(cached_repo_dir).rglob("*")
        if (entry.is_file() and entry.name.startswith(name) and entry.name.endswith(ext))
    ]

    return file_list


def write_checkpoints_json(model_name_or_path, local_rank, f, token=None):
    """Dumps metadata into a JSON file for DeepSpeed-inference."""
    checkpoint_files = get_checkpoint_files(model_name_or_path, local_rank, token)
    data = {"type": "ds_model", "checkpoints": checkpoint_files, "version": 1.0}
    json.dump(data, f)
    f.flush()


def model_on_meta(config):
    """Checks if load the model to meta."""
    # return config.model_type in ["bloom", "llama", "falcon", "mixtral", "qwen2", "mllama"]
    return config.model_type in ["bloom", "llama", "falcon", "mixtral", "qwen2"]


def get_optimized_model_name(config):
    from .transformers.generation import MODELS_OPTIMIZED_WITH_STATIC_SHAPES

    for model_type in MODELS_OPTIMIZED_WITH_STATIC_SHAPES:
        if model_type == config.model_type:
            return model_type

    return None


def model_is_optimized(config):
    """Checks if the given config belongs to a model in optimum/habana/transformers/models, which has a
    new input token_idx."""
    return get_optimized_model_name(config) is not None


def get_ds_injection_policy(config):
    model_type = get_optimized_model_name(config)
    policy = {}
    if model_type:
        if model_type == "bloom":
            from transformers.models.bloom.modeling_bloom import BloomBlock

            policy = {BloomBlock: ("self_attention.dense", "mlp.dense_4h_to_h")}

        if model_type == "opt":
            from transformers.models.opt.modeling_opt import OPTDecoderLayer

            policy = {OPTDecoderLayer: ("self_attn.out_proj", ".fc2")}

        if model_type == "gpt2":
            from transformers.models.gpt2.modeling_gpt2 import GPT2MLP

            policy = {GPT2MLP: ("attn.c_proj", "mlp.c_proj")}

        if model_type == "gptj":
            from transformers.models.gptj.modeling_gptj import GPTJBlock

            policy = {GPTJBlock: ("attn.out_proj", "mlp.fc_out")}

        if model_type == "gpt_neox":
            from transformers.models.gpt_neox.modeling_gpt_neox import GPTNeoXLayer

            policy = {GPTNeoXLayer: ("attention.dense", "mlp.dense_4h_to_h")}

        if model_type == "llama":
            from transformers.models.llama.modeling_llama import LlamaDecoderLayer

            policy = {LlamaDecoderLayer: ("self_attn.o_proj", "mlp.down_proj")}

        # if model_type == "mllama":
        # #AutoTP:  [(<class 'transformers.models.mllama.modeling_mllama.MllamaVisionEncoderLayer'>, {'self_attn.o_proj', 'mlp.fc2'}), (<class 'transformers.models.mllama.modeling_mllama.MllamaSelfAttentionDecoderLayer'>, ['self_attn.o_proj', 'mlp.down_proj']), (<class 'transformers.models.mllama.modeling_mllama.MllamaCrossAttentionDecoderLayer'>, ['cross_attn.o_proj', 'mlp.down_proj'])]
        #     from transformers.models.mllama.modeling_mllama import MllamaVisionEncoderLayer, MllamaSelfAttentionDecoderLayer, MllamaCrossAttentionDecoderLayer

        #     policy = {MllamaSelfAttentionDecoderLayer: ("self_attn.o_proj", "mlp.down_proj"), MllamaCrossAttentionDecoderLayer: ('cross_attn.o_proj', 'mlp.down_proj'), MllamaVisionEncoderLayer: ('self_attn.o_proj', 'mlp.fc2')}
        #     policy = {MllamaSelfAttentionDecoderLayer: ("self_attn.o_proj", "mlp.down_proj"), MllamaCrossAttentionDecoderLayer: ('cross_attn.o_proj', 'mlp.down_proj')}

        if model_type == "mistral":
            from transformers.models.mistral.modeling_mistral import MistralDecoderLayer

            policy = {MistralDecoderLayer: ("self_attn.o_proj", "mlp.down_proj")}

    return policy
