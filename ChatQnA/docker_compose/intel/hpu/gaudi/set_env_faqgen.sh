#!/usr/bin/env bash

# Copyright (C) 2024 Intel Corporation
# SPDX-License-Identifier: Apache-2.0
SCRIPT_DIR=$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" &> /dev/null && pwd)

pushd "$SCRIPT_DIR/../../../../../" > /dev/null
source .set_env.sh
popd > /dev/null

export HF_TOKEN=${HF_TOKEN}
export host_ip=${ip_address}
export EMBEDDING_MODEL_ID="BAAI/bge-base-en-v1.5"
export RERANK_MODEL_ID="BAAI/bge-reranker-base"
export LLM_MODEL_ID="meta-llama/Meta-Llama-3-8B-Instruct"
export INDEX_NAME="rag-redis"
export NUM_CARDS=1
export VLLM_SKIP_WARMUP=true
export LOGFLAG=True
export http_proxy=${http_proxy}
export https_proxy=${https_proxy}
export no_proxy="${ip_address},redis-vector-db,dataprep-redis-service,tei-embedding-service,retriever,tei-reranking-service,tgi-service,vllm-service,guardrails,llm-faqgen,chatqna-gaudi-backend-server,chatqna-gaudi-ui-server,chatqna-gaudi-nginx-server"

export LLM_ENDPOINT_PORT=8010
export LLM_SERVER_PORT=9001
export CHATQNA_BACKEND_PORT=8888
export CHATQNA_REDIS_VECTOR_PORT=6377
export CHATQNA_REDIS_VECTOR_INSIGHT_PORT=8006
export CHATQNA_FRONTEND_SERVICE_PORT=5175
export NGINX_PORT=80
export FAQGen_COMPONENT_NAME="OpeaFaqGenvLLM"
export LLM_ENDPOINT="http://${host_ip}:${LLM_ENDPOINT_PORT}"
