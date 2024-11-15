# Copyright (C) 2024 Intel Corporation
# SPDX-License-Identifier: Apache-2.0

import os
import sys
from enum import Enum

import openvino.runtime as ov
from config import SUPPORTED_EMBEDDING_MODELS, SUPPORTED_LLM_MODELS, SUPPORTED_RERANK_MODELS

sys.path.append("..")
from edgecraftrag.base import GeneratorType, IndexerType, NodeParserType, PostProcessorType, RetrieverType


def _get_llm_model_ids(supported_models, model_language=None):
    if model_language is None:
        model_ids = [model_id for model_id, _ in supported_models.items()]
        return model_ids

    if model_language not in supported_models:
        print("Invalid model language! Please choose from the available options.")
        return None

    # Create a list of model IDs based on the selected language
    llm_model_ids = [
        model_id
        for model_id, model_config in supported_models[model_language].items()
        if model_config.get("rag_prompt_template") or model_config.get("normalize_embeddings")
    ]

    return llm_model_ids


def _list_subdirectories(parent_directory):
    """List all subdirectories under the given parent directory using os.listdir.

    Parameters:
    parent_directory (str): The path to the parent directory from which to list subdirectories.

    Returns:
    list: A list of subdirectory names found in the parent directory.
    """
    # Get a list of all entries in the parent directory
    entries = os.listdir(parent_directory)

    # Filter out the entries to only keep directories
    subdirectories = [entry for entry in entries if os.path.isdir(os.path.join(parent_directory, entry))]

    return sorted(subdirectories)


def _get_available_models(model_ids, local_dirs):
    """Filters and sorts model IDs based on their presence in the local directories.

    Parameters:
    model_ids (list): A list of model IDs to check.
    local_dirs (list): A list of local directory names to check against.

    Returns:
    list: A sorted list of available model IDs.
    """
    # Filter model_ids for those that are present in local directories
    return sorted([model_id for model_id in model_ids if model_id in local_dirs])


def get_local_available_models(model_type: str, local_path: str = "./"):
    local_dirs = _list_subdirectories(local_path)
    if model_type == "llm":
        model_ids = _get_llm_model_ids(SUPPORTED_LLM_MODELS, "Chinese")
    elif model_type == "embed":
        model_ids = _get_llm_model_ids(SUPPORTED_EMBEDDING_MODELS, "Chinese")
    elif model_type == "rerank":
        model_ids = _get_llm_model_ids(SUPPORTED_RERANK_MODELS)
    else:
        print("Unknown model type")
    avail_models = _get_available_models(model_ids, local_dirs)
    return avail_models


def get_available_devices():
    core = ov.Core()
    avail_devices = core.available_devices + ["AUTO"]
    if "NPU" in avail_devices:
        avail_devices.remove("NPU")
    return avail_devices


def get_available_weights():
    avail_weights_compression = ["FP16", "INT8", "INT4"]
    return avail_weights_compression


def get_avail_llm_inference_type():
    avail_llm_inference_type = ["local", "vllm"]
    return avail_llm_inference_type


def get_enum_values(c: Enum):
    return [v.value for k, v in vars(c).items() if not callable(v) and not k.startswith("__") and not k.startswith("_")]


def get_available_node_parsers():
    return get_enum_values(NodeParserType)


def get_available_indexers():
    return get_enum_values(IndexerType)


def get_available_retrievers():
    return get_enum_values(RetrieverType)


def get_available_postprocessors():
    return get_enum_values(PostProcessorType)


def get_available_generators():
    return get_enum_values(GeneratorType)


def get_llm_model_dir(prefix, llm_model_id, weights_compression):
    model_dirs = {
        "fp16_model_dir": prefix + llm_model_id + "/FP16",
        "int8_model_dir": prefix + llm_model_id + "/INT8_compressed_weights",
        "int4_model_dir": prefix + llm_model_id + "/INT4_compressed_weights",
    }

    if weights_compression == "INT4":
        model_dir = model_dirs["int4_model_dir"]
    elif weights_compression == "INT8":
        model_dir = model_dirs["int8_model_dir"]
    else:
        model_dir = model_dirs["fp16_model_dir"]

    # if not model_dir.exists():
    #     raise FileNotFoundError(f"The model directory {model_dir} does not exist.")
    # elif not model_dir.is_dir():
    #     raise NotADirectoryError(f"The path {model_dir} is not a directory.")

    return model_dir
