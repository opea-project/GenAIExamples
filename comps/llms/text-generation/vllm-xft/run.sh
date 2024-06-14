#!/bin/sh

# Copyright (C) 2024 Intel Corporation
# SPDX-License-Identifier: Apache-2.0

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
        --host localhost \
        --port 18688 \
        --trust-remote-code &

# run llm microservice wrapper
python llm.py
