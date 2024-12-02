#!/usr/bin/env bash

# Copyright (C) 2024 Intel Corporation
# SPDX-License-Identifier: Apache-2.0

pushd "../../../../../" > /dev/null
source .set_env.sh
popd > /dev/null

if [ -z "${your_hf_api_token}" ]; then
    echo "Error: HUGGINGFACEHUB_API_TOKEN is not set. Please set your_hf_api_token."
fi

if [ -z "${host_ip}" ]; then
    echo "Error: host_ip is not set. Please set host_ip first."
fi

export HUGGINGFACEHUB_API_TOKEN=${your_hf_api_token}
export EMBEDDING_MODEL_ID="BAAI/bge-base-en-v1.5"
export RERANK_MODEL_ID="BAAI/bge-reranker-base"
export INDEX_NAME="rag-redis"
export OLLAMA_HOST=${host_ip}
export OLLAMA_MODEL="llama3.2"
