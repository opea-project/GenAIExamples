#!/usr/bin/env bash

# Copyright (C) 2024 Intel Corporation
# SPDX-License-Identifier: Apache-2.0
pushd "../../../../../" > /dev/null
source .set_env.sh
popd > /dev/null

ip_address=$(hostname -I | awk '{print $1}')
export EMBEDDING_MODEL_ID="BAAI/bge-base-en-v1.5"
export RERANK_MODEL_ID="BAAI/bge-reranker-base"
export TEI_EMBEDDING_ENDPOINT="http://${ip_address}:6006"
export TEI_RERANKING_ENDPOINT="http://${ip_address}:8808"
export TGI_LLM_ENDPOINT="http://${ip_address}:8008"
export HF_TOKEN=${HF_TOKEN}
export MEGA_SERVICE_HOST_IP=${ip_address}
export EMBEDDING_SERVICE_HOST_IP=${ip_address}
export RETRIEVER_SERVICE_HOST_IP=${ip_address}
export RERANK_SERVICE_HOST_IP=${ip_address}
export LLM_SERVICE_HOST_IP=${ip_address}
export host_ip=${ip_address}
export RERANK_TYPE="tei"
export LOGFLAG=true

export REDIS_URL="redis://${ip_address}:6379"
export INDEX_NAME="rag-redis"

export MILVUS_HOST=${ip_address}
export DATAPREP_SERVICE_ENDPOINT="http://${host_ip}:6007/v1/dataprep/ingest"
