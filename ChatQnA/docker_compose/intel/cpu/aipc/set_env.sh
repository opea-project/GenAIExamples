#!/usr/bin/env bash

# Copyright (C) 2024 Intel Corporation
# SPDX-License-Identifier: Apache-2.0

pushd "../../../../../" > /dev/null
source .set_env.sh
popd > /dev/null

if [ -z "${HF_TOKEN}" ]; then
    echo "Error: HF_TOKEN is not set. Please set HF_TOKEN."
fi

export host_ip=$(hostname -I | awk '{print $1}')
export EMBEDDING_MODEL_ID="BAAI/bge-base-en-v1.5"
export RERANK_MODEL_ID="BAAI/bge-reranker-base"
export INDEX_NAME="rag-redis"
export OLLAMA_HOST=${host_ip}
export OLLAMA_MODEL="llama3.2"
# Set it as a non-null string, such as true, if you want to enable logging facility,
# otherwise, keep it as "" to disable it.
export LOGFLAG=""
