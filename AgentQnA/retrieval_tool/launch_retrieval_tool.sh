# Copyright (C) 2024 Intel Corporation
# SPDX-License-Identifier: Apache-2.0

export HOST_IP=""
export HF_CACHE_DIR=./data
export HUGGINGFACEHUB_API_TOKEN=${HUGGINGFACEHUB_API_TOKEN}
export no_proxy=${no_proxy}
export http_proxy=${http_proxy}
export https_proxy=${https_proxy}
export EMBEDDING_MODEL_ID="BAAI/bge-base-en-v1.5"
export RERANK_MODEL_ID="BAAI/bge-reranker-base"
export TEI_EMBEDDING_ENDPOINT="http://${HOST_IP}:6006"
export TEI_RERANKING_ENDPOINT="http://${HOST_IP}:8808"
export REDIS_URL="redis://${HOST_IP}:6379"
export INDEX_NAME="rag-redis"
export RERANK_TYPE="tei"
export MEGA_SERVICE_HOST_IP=${HOST_IP}
export EMBEDDING_SERVICE_HOST_IP=${HOST_IP}
export RETRIEVER_SERVICE_HOST_IP=${HOST_IP}
export RERANK_SERVICE_HOST_IP=${HOST_IP}
export BACKEND_SERVICE_ENDPOINT="http://${HOST_IP}:8889/v1/retrievaltool"
export DATAPREP_SERVICE_ENDPOINT="http://${HOST_IP}:6007/v1/dataprep/ingest"
export DATAPREP_GET_FILE_ENDPOINT="http://${HOST_IP}:6008/v1/dataprep/get"
export DATAPREP_DELETE_FILE_ENDPOINT="http://${HOST_IP}:6009/v1/dataprep/delete"

docker compose -f ../../DocIndexRetriever/docker_compose/intel/cpu/xeon/compose.yaml up -d
