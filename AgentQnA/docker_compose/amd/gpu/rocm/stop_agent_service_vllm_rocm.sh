#!/bin/bash
# Copyright (C) 2024 Advanced Micro Devices, Inc.
# SPDX-License-Identifier: Apache-2.0


# Before start script:
# export host_ip="your_host_ip_or_host_name"
# export HF_TOKEN="your_huggingface_api_token"
# export LANGCHAIN_API_KEY="your_langchain_api_key"
# export LANGCHAIN_TRACING_V2=""

# Set server hostname or IP address
export ip_address=${host_ip}

# Set services IP ports
export VLLM_SERVICE_PORT="18110"
export WORKER_RAG_AGENT_PORT="18111"
export WORKER_SQL_AGENT_PORT="18112"
export SUPERVISOR_REACT_AGENT_PORT="18113"
export CRAG_SERVER_PORT="18114"

export WORKPATH=$(dirname "$PWD")
export WORKDIR=${WORKPATH}/../../../
export HF_TOKEN=${HF_TOKEN}
export VLLM_LLM_MODEL_ID="Intel/neural-chat-7b-v3-3"
export HF_CACHE_DIR="./data"
export MODEL_CACHE="./data"
export TOOLSET_PATH=${WORKPATH}/../../../tools/
export recursion_limit_worker=12
export LLM_ENDPOINT_URL=http://${ip_address}:${VLLM_SERVICE_PORT}
export LLM_MODEL_ID=${VLLM_LLM_MODEL_ID}
export temperature=0.01
export max_new_tokens=512
export RETRIEVAL_TOOL_URL="http://${ip_address}:8889/v1/retrievaltool"
export LANGCHAIN_API_KEY=${LANGCHAIN_API_KEY}
export LANGCHAIN_TRACING_V2=${LANGCHAIN_TRACING_V2}
export db_name=Chinook
export db_path="sqlite:////home/user/chinook-db/Chinook_Sqlite.sqlite"
export recursion_limit_worker=12
export recursion_limit_supervisor=10
export CRAG_SERVER=http://${ip_address}:${CRAG_SERVER_PORT}
export WORKER_AGENT_URL="http://${ip_address}:${WORKER_RAG_AGENT_PORT}/v1/chat/completions"
export SQL_AGENT_URL="http://${ip_address}:${WORKER_SQL_AGENT_PORT}/v1/chat/completions"
export HF_CACHE_DIR=${HF_CACHE_DIR}
export HF_TOKEN=${HF_TOKEN}
export no_proxy=${no_proxy}
export http_proxy=${http_proxy}
export https_proxy=${https_proxy}
export EMBEDDING_MODEL_ID="BAAI/bge-base-en-v1.5"
export RERANK_MODEL_ID="BAAI/bge-reranker-base"
export TEI_EMBEDDING_ENDPOINT="http://${host_ip}:6006"
export TEI_RERANKING_ENDPOINT="http://${host_ip}:8808"
export REDIS_URL="redis://${host_ip}:6379"
export INDEX_NAME="rag-redis"
export RERANK_TYPE="tei"
export MEGA_SERVICE_HOST_IP=${host_ip}
export EMBEDDING_SERVICE_HOST_IP=${host_ip}
export RETRIEVER_SERVICE_HOST_IP=${host_ip}
export RERANK_SERVICE_HOST_IP=${host_ip}
export BACKEND_SERVICE_ENDPOINT="http://${host_ip}:8889/v1/retrievaltool"
export DATAPREP_SERVICE_ENDPOINT="http://${host_ip}:6007/v1/dataprep/ingest"
export DATAPREP_GET_FILE_ENDPOINT="http://${host_ip}:6008/v1/dataprep/get"
export DATAPREP_DELETE_FILE_ENDPOINT="http://${host_ip}:6009/v1/dataprep/delete"

echo ${WORKER_RAG_AGENT_PORT} > ${WORKPATH}/WORKER_RAG_AGENT_PORT_tmp
echo ${WORKER_SQL_AGENT_PORT} > ${WORKPATH}/WORKER_SQL_AGENT_PORT_tmp
echo ${SUPERVISOR_REACT_AGENT_PORT} > ${WORKPATH}/SUPERVISOR_REACT_AGENT_PORT_tmp
echo ${CRAG_SERVER_PORT} > ${WORKPATH}/CRAG_SERVER_PORT_tmp

echo "Removing chinook data..."
rm -R chinook-database
if [ -d "chinook-database" ]; then
    rm -rf chinook-database
fi
echo "Chinook data removed!"

echo "Stopping CRAG server"
docker rm kdd-cup-24-crag-service --force

echo "Stopping Agent services"
docker compose -f compose_vllm.yaml down

echo "Stopping Retrieval services"
docker compose -f ../../../../../DocIndexRetriever/docker_compose/intel/cpu/xeon/compose.yaml down
