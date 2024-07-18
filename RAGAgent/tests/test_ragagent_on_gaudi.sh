#!/bin/bash
# Copyright (C) 2024 Intel Corporation
# SPDX-License-Identifier: Apache-2.0

set -e
echo "IMAGE_REPO=${IMAGE_REPO}"
echo "HUGGINGFACEHUB_API_TOKEN=${HUGGINGFACEHUB_API_TOKEN}"

WORKPATH=$(dirname "$PWD")
LOG_PATH="$WORKPATH/tests"
ip_address=$(hostname -I | awk '{print $1}')

function build_docker_images_indexretriever() {
    cd $WORKPATH/../../
    if [ ! -d "GenAIComps" ] ; then
        git clone https://github.com/opea-project/GenAIComps.git
    fi
    cd GenAIComps
    local CUR=$(git branch --show-current)
    echo "Check to DocIndexerRetriever component, Current Branch is ${CUR}"
    if [ "${CUR}" != "PR314" ] ; then
        git fetch origin pull/314/head:PR314; git checkout PR314
    fi

    docker build -t opea/embedding-tei:latest -f comps/embeddings/langchain/docker/Dockerfile .
    docker build -t opea/retriever-redis:latest -f comps/retrievers/langchain/redis/docker/Dockerfile .
    docker build -t opea/reranking-tei:latest -f comps/reranks/tei/docker/Dockerfile .
    docker build -t opea/dataprep-on-ray-redis:latest -f comps/dataprep/redis/langchain_ray/docker/Dockerfile .

    docker pull ghcr.io/huggingface/tgi-gaudi:latest
    docker pull redis/redis-stack:7.2.0-v9

    cd $WORKPATH/../../
    cd GenAIExamples
    git checkout -b ragagent
    local CUR=$(git branch --show-current)
    echo "Check to DocIndexerRetriever megaservice, Current Branch is ${CUR}"
    if [ "${CUR}" != "PR405" ] ; then
        git fetch origin pull/405/head:PR405; git checkout PR405
    fi
    cd ..
    docker build -t opea/doc-index-retriever:latest -f GenAIExamples/DocIndexRetriever/docker/Dockerfile .
    cd GenAIExamples; git checkout ragagent; cd ..
}

function build_docker_images_agent() {
    cd $WORKPATH/../../
    if [ ! -d "GenAIComps" ] ; then
        git clone https://github.com/opea-project/GenAIComps.git
    fi
    cd GenAIComps
    local CUR=$(git branch --show-current)
    echo "Check to Agent component, Current Branch is ${CUR}"
    if [ "${CUR}" != "PR228" ] ; then
        git fetch origin pull/228/head:PR228; git checkout PR228
    fi
    docker build -t opea/comps-agent-langchain:latest -f comps/agent/langchain/docker/Dockerfile .
}

function start_services() {
    # build tei-gaudi for each test instead of pull from local registry
    cd $WORKPATH/docker/gaudi
    export LLM_MODEL=meta-llama/Meta-Llama-3-8B-Instruct
    export AGENT_STRATEGY=react
    export LLM_ENDPOINT_URL="http://${ip_address}:8008"
    export TOOLSET_PATH=$WORKPATH/tools
    export HF_TOKEN=${HUGGINGFACEHUB_API_TOKEN}
    export EMBEDDING_MODEL_ID="BAAI/bge-base-en-v1.5"
    export RERANK_MODEL_ID="BAAI/bge-reranker-base"
    export TEI_EMBEDDING_ENDPOINT="http://${ip_address}:8090"
    export TEI_RERANKING_ENDPOINT="http://${ip_address}:8808"
    export REDIS_URL="redis://${ip_address}:6379"
    export INDEX_NAME="rag-redis"
    export MEGA_SERVICE_HOST_IP=${ip_address}
    export EMBEDDING_SERVICE_HOST_IP=${ip_address}
    export RETRIEVER_SERVICE_HOST_IP=${ip_address}
    export RERANK_SERVICE_HOST_IP=${ip_address}

    # Start Docker Containers
    docker compose -f docker_compose.yaml up -d
    sleep 20
    echo "Waiting tgi gaudi ready"
    n=0
    until [[ "$n" -ge 100 ]] || [[ $ready == true ]]; do
        docker logs tgi-gaudi-server > ${WORKPATH}/tests/tgi-gaudi-service.log
        n=$((n+1))
        if grep -q Connected ${WORKPATH}/tests/tgi-gaudi-service.log; then
            break
        fi
        sleep 5s
    done
    sleep 5s
    echo "Service started successfully"
    docker ps
}

function validate() {
    local CONTENT="$1"
    local EXPECTED_RESULT="$2"
    local SERVICE_NAME="$3"

    if echo "$CONTENT" | grep -q "$EXPECTED_RESULT"; then
        echo "[ $SERVICE_NAME ] Content is as expected: $CONTENT"
        echo 0
    else
        echo "[ $SERVICE_NAME ] Content does not match the expected result: $CONTENT"
        echo 1
    fi
}

function validate_megaservice() {
    echo "Testing DataPrep Service"
    local CONTENT=$(curl -X POST "http://${ip_address}:6007/v1/dataprep" \
     -H "Content-Type: multipart/form-data" \
     -F 'link_list=["https://opea.dev"]' | tee -a ${LOG_PATH}/test-dataprep.log)
    local EXIT_CODE=$(validate "$CONTENT" "Data preparation succeeded" "test-dataprep" )
    echo "$EXIT_CODE"
    local EXIT_CODE="${EXIT_CODE:0-1}"
    if [ "$EXIT_CODE" == "1" ]; then
        docker logs dataprep-redis-server >> ${LOG_PATH}/test-dataprep.log
        exit 1
    fi

    echo "Testing agent service"
    local CONTENT=$(curl http://${ip_address}:9090/v1/chat/completions -X POST -H "Content-Type: application/json" -d '{
     "query": "What is Intel OPEA project?"
    }' | tee -a ${LOG_PATH}/test-ragagent.log)
    local EXIT_CODE=$(validate "$CONTENT" "OPEA" "test-ragagent")
    echo "$EXIT_CODE"
    local EXIT_CODE="${EXIT_CODE:0-1}"
    echo "return value is $EXIT_CODE"
    docker container logs rag-agent-server &> ${LOG_PATH}/test-ragagent-service.log
    docker container logs doc-index-retriever-server &> ${LOG_PATH}/test-doc-index-retriever.log
    if [ "$EXIT_CODE" == "1" ]; then
        docker container logs tgi-gaudi-server &> ${LOG_PATH}/tgi-gaudi-service.log
        exit 1
    fi
}

function stop_docker() {
    cd $WORKPATH/docker/gaudi
    container_list=$(cat docker_compose.yaml | grep container_name | cut -d':' -f2)
    for container_name in $container_list; do
        cid=$(docker ps -aq --filter "name=$container_name")
        echo "Stopping container $container_name"
        if [[ ! -z "$cid" ]]; then docker rm $cid -f && sleep 1s; fi
    done
}

function main() {

    stop_docker
    echo "Step 1: Build Docker Images for RAG megaservice"
    build_docker_images_indexretriever
    echo "Step 2: Build Docker Images for Agent megaservice"
    build_docker_images_agent
    start_time=$(date +%s)
    echo "Step 3: Launch megaservice"
    start_services
    end_time=$(date +%s)
    duration=$((end_time-start_time))
    echo "Mega service start duration is $duration s"
    echo "Step 4: send msg for validation"
    validate_megaservice

    echo "Step 5: Clean ENV"
    stop_docker
    echo y | docker system prune

}

main
