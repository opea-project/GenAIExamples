#!/bin/sh

# Copyright (C) 2024 Intel Corporation
# SPDX-License-Identifier: Apache-2.0

# Preloading libiomp5.so is essential for optimal performance.
# libiomp5.so is the Intel OpenMP runtime library, providing parallel computation support,
# thread management, task scheduling, and performance optimization on Intel X86 platforms.
export $(python -c 'import xfastertransformer as xft; print(xft.get_env())')

# convert the model to fastertransformer format
python -c 'import os; import xfastertransformer as xft; xft.Qwen2Convert().convert(os.environ["HF_DATASET_DIR"], os.environ["OUTPUT_DIR"])'

unset http_proxy

# serving with vllm
python -m vllm.entrypoints.openai.api_server \
        --model ${OUTPUT_DIR} \
        --tokenizer ${TOKEN_PATH} \
        --dtype bf16 \
        --kv-cache-dtype fp16 \
        --served-model-name xft \
        --host 0.0.0.0 \
        --port 18688 \
        --trust-remote-code &

# run llm microservice wrapper
python llm.py
