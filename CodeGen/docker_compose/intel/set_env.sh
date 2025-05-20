#!/usr/bin/env bash

# Copyright (C) 2024 Intel Corporation
# SPDX-License-Identifier: Apache-2.0
pushd "../../" > /dev/null
source .set_env.sh
popd > /dev/null

export HOST_IP=$(hostname -I | awk '{print $1}')
export HUGGINGFACEHUB_API_TOKEN=${HUGGINGFACEHUB_API_TOKEN}
if [ -z "${HUGGINGFACEHUB_API_TOKEN}" ]; then
    echo "Error: HUGGINGFACEHUB_API_TOKEN is not set. Please set HUGGINGFACEHUB_API_TOKEN"
fi

if [ -z "${HOST_IP}" ]; then
    echo "Error: HOST_IP is not set. Please set HOST_IP first."
fi

export no_proxy=${no_proxy},${HOST_IP}
export http_proxy=${http_proxy}
export https_proxy=${https_proxy}

export LLM_MODEL_ID="Qwen/Qwen2.5-Coder-7B-Instruct"
export LLM_SERVICE_PORT=9000
export LLM_ENDPOINT="http://${HOST_IP}:8028"
export LLM_SERVICE_HOST_IP=${HOST_IP}
export TGI_LLM_ENDPOINT="http://${HOST_IP}:8028"

export MEGA_SERVICE_PORT=7778
export MEGA_SERVICE_HOST_IP=${HOST_IP}
export BACKEND_SERVICE_ENDPOINT="http://${HOST_IP}:7778/v1/codegen"

export REDIS_DB_PORT=6379
export REDIS_INSIGHTS_PORT=8001
export REDIS_RETRIEVER_PORT=7000
export REDIS_URL="redis://${HOST_IP}:${REDIS_DB_PORT}"
export RETRIEVAL_SERVICE_HOST_IP=${HOST_IP}
export RETRIEVER_COMPONENT_NAME="OPEA_RETRIEVER_REDIS"
export INDEX_NAME="CodeGen"

export EMBEDDING_MODEL_ID="BAAI/bge-base-en-v1.5"
export EMBEDDER_PORT=6000
export TEI_EMBEDDER_PORT=8090
export TEI_EMBEDDING_HOST_IP=${HOST_IP}
export TEI_EMBEDDING_ENDPOINT="http://${HOST_IP}:${TEI_EMBEDDER_PORT}"

export DATAPREP_REDIS_PORT=6007
export DATAPREP_ENDPOINT="http://${HOST_IP}:${DATAPREP_REDIS_PORT}/v1/dataprep"
export LOGFLAG=false
export MODEL_CACHE=${model_cache:-"./data"}
export NUM_CARDS=1
