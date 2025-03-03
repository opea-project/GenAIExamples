#!/bin/bash
# Copyright (C) 2024 Advanced Micro Devices, Inc.
# SPDX-License-Identifier: Apache-2.0

set -xe

WORKPATH=$(dirname "$PWD")
export WORKDIR=$WORKPATH/../../
export LOG_PATH=$WORKPATH
echo "WORKDIR=${WORKDIR}"
export ip_address=$(hostname -I | awk '{print $1}')
export HUGGINGFACEHUB_API_TOKEN=${HUGGINGFACEHUB_API_TOKEN}
export TOOLSET_PATH=$WORKDIR/GenAIExamples/AgentQnA/tools/
export RETRIEVAL_TOOL_PATH=$WORKPATH/../DocIndexRetriever

export HOST_IP=${ip_address}
export EXTERNAL_HOST_IP=${ip_address}
export AGENT_VLLM_SERVICE_PORT="8081"
export AGENT_HUGGINGFACEHUB_API_TOKEN=${HUGGINGFACEHUB_API_TOKEN}
export AGENT_LLM_MODEL_ID="meta-llama/Meta-Llama-3-8B-Instruct"
export AGENT_RETRIEVAL_PORT="7000"
export AGENT_RAG_AGENT_PORT="9095"
export recursion_limit_worker=12
export AGENT_LLM_ENDPOINT_URL="http://${HOST_IP}:${AGENT_VLLM_SERVICE_PORT}"
export temperature="0.01"
export max_new_tokens="512"
export AGENT_RETRIEVAL_TOOL_URL="http://${HOST_IP}:8889/v1/retrievaltool"
export AGENT_LANGCHAIN_API_KEY=${LANGCHAIN_API_KEY}
export AGENT_LANGCHAIN_TRACING_V2=${LANGCHAIN_TRACING_V2}
export AGENT_FRONTEND_PORT="9090"
export export recursion_limit_supervisor="10"
export AGENT_CRAG_SERVER=http://${HOST_IP}:18881
export AGENT_WORKER_AGENT_URL="http://${HOST_IP}:${AGENT_RAG_AGENT_PORT}/v1/chat/completions"

function stop_crag() {
    cid=$(docker ps -aq --filter "name=kdd-cup-24-crag-service")
    echo "Stopping container kdd-cup-24-crag-service with cid $cid"
    if [[ ! -z "$cid" ]]; then docker rm $cid -f && sleep 1s; fi
}

function stop_agent_docker() {
    cd $WORKPATH/docker_compose/amd/gpu/rocm
    docker compose -f compose_vllm.yaml down
}

function stop_retrieval_tool() {
    echo "Stopping Retrieval tool"
    cd $RETRIEVAL_TOOL_PATH/docker_compose/intel/cpu/xeon/
    docker compose -f compose.yaml down
}

echo "workpath: $WORKPATH"
echo "=================== Stop containers ===================="
stop_agent_docker
stop_retrieval_tool

cd $WORKPATH/tests

function build_agent_docker_images() {
    echo "Building Docker Images...."
    cd $WORKPATH/docker_image_build
    if [ ! -d "GenAIComps" ] ; then
        git clone --single-branch --branch "${opea_branch:-"main"}" https://github.com/opea-project/GenAIComps.git
    fi
    service_list="agent agent-ui vllm-rocm"
    docker compose -f build.yaml build ${service_list} --no-cache > ${LOG_PATH}/docker_image_build.log
    docker images && sleep 3s

    echo "Docker images for Agent built!"
}

function build_retriever_tools_docker_images() {
    echo "Building Docker Images...."
    cd $WORKPATH/../DocIndexRetriever/docker_image_build
    if [ ! -d "GenAIComps" ] ; then
        git clone --single-branch --branch "${opea_branch:-"main"}" https://github.com/opea-project/GenAIComps.git
    fi
    service_list="dataprep embedding retriever reranking doc-index-retriever"
    docker compose -f build.yaml build ${service_list} --no-cache > ${LOG_PATH}/docker_image_build.log

    docker pull ghcr.io/huggingface/text-embeddings-inference:cpu-1.5
    docker pull redis/redis-stack:7.2.0-v9
    docker images && sleep 3s

    echo "Docker images for Retrieval tools built!"
}

function start_retriever_tools_services() {
    echo "Starting Docker Services...."
    cd $WORKPATH/../DocIndexRetriever/docker_compose/intel/cpu/xeon

    host_ip=${ip_address}
    export HF_CACHE_DIR=./data
    export HUGGINGFACEHUB_API_TOKEN=${HUGGINGFACEHUB_API_TOKEN}
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

    # Start Docker Containers
    docker compose -f compose.yaml up -d
    sleep 2m
    echo "Docker services started!"
}

function ingest_data_and_validate() {
    echo "Ingesting data"
    cd $WORKDIR/GenAIExamples/AgentQnA/retrieval_tool/
    echo $PWD
    local CONTENT=$(bash run_ingest_data.sh)
    local EXIT_CODE=$(validate "$CONTENT" "Data preparation succeeded" "dataprep-redis-server")
    echo "$EXIT_CODE"
    local EXIT_CODE="${EXIT_CODE:0-1}"
    echo "return value is $EXIT_CODE"
    if [ "$EXIT_CODE" == "1" ]; then
        docker logs dataprep-redis-server
        return 1
    fi
}

function start_agent_and_api_server() {
    echo "Starting CRAG server"
    docker run -d --runtime=runc --name=kdd-cup-24-crag-service -p=8080:8000 docker.io/aicrowd/kdd-cup-24-crag-mock-api:v0

    echo "Starting Agent services"
    cd $WORKDIR/GenAIExamples/AgentQnA/docker_compose/amd/gpu/rocm
    docker compose -f compose_vllm.yaml up -d
}

cd $WORKPATH/tests

echo "=================== #1 Building docker images===================="
build_agent_docker_images
build_retriever_tools_docker_images
echo "=================== #1 Building docker images completed===================="

echo "=================== #2 Start retrieval tool===================="
start_retriever_tools_services
echo "=================== #2 Retrieval tool started===================="

echo "=================== #3 Ingest data and validate retrieval===================="
ingest_data_and_validate
echo "=================== #3 Data ingestion and validation completed===================="

echo "=================== #4 Start agent and API server===================="
start_agent_and_api_server
echo "=================== #4 Agent test passed ===================="

echo "=================== #5 Stop agent and API server===================="
stop_crag
stop_agent_docker
stop_retrieval_tool
echo "=================== #5 Agent and API server stopped===================="

echo y | docker system prune

echo "ALL DONE!!"
