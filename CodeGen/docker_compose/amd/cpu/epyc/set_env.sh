#!/usr/bin/env bash

# Copyright (C) 2025 Advanced Micro Devices, Inc.
# Copyright (C) 2025 Intel Corporation
# SPDX-License-Identifier: Apache-2.0

# export host_ip=<your External Public IP>
host_ip=$(hostname -I | awk '{print $1}')
export host_ip

export HF_TOKEN=${HF_TOKEN}
if [ -z "${HF_TOKEN}" ]; then
	echo "Error: HF_TOKEN is not set. Please set HF_TOKEN"
fi

if [ -z "${host_ip}" ]; then
	echo "Error: host_ip is not set. Please set host_ip first."
fi

export no_proxy="${no_proxy},${host_ip}"
export http_proxy=${http_proxy}
export https_proxy=${https_proxy}

export LLM_MODEL_ID="Qwen/Qwen2.5-Coder-7B-Instruct"
export LLM_SERVICE_PORT=9000
export LLM_ENDPOINT="http://${host_ip}:8028"
export LLM_SERVICE_HOST_IP=${host_ip}
export TGI_LLM_ENDPOINT="http://${host_ip}:8028"

export MEGA_SERVICE_PORT=7778
export MEGA_SERVICE_HOST_IP=${host_ip}
export BACKEND_SERVICE_ENDPOINT="http://${host_ip}:7778/v1/codegen"

export REDIS_DB_PORT=6379
export REDIS_INSIGHTS_PORT=8001
export REDIS_RETRIEVER_PORT=7000
export REDIS_URL="redis://${host_ip}:${REDIS_DB_PORT}"
export RETRIEVAL_SERVICE_HOST_IP=${host_ip}
export RETRIEVER_COMPONENT_NAME="OPEA_RETRIEVER_REDIS"
export INDEX_NAME="CodeGen"

export EMBEDDING_MODEL_ID="BAAI/bge-base-en-v1.5"
export EMBEDDER_PORT=6000
export TEI_EMBEDDER_PORT=8090
export TEI_EMBEDDING_HOST_IP=${host_ip}
export TEI_EMBEDDING_ENDPOINT="http://${host_ip}:${TEI_EMBEDDER_PORT}"

export DATAPREP_REDIS_PORT=6007
export DATAPREP_ENDPOINT="http://${host_ip}:${DATAPREP_REDIS_PORT}/v1/dataprep"
export LOGFLAG=false
export MODEL_CACHE=${model_cache:-"./data"}
export NUM_CARDS=1
