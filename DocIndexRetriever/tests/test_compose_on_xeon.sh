#!/bin/bash
# Copyright (C) 2024 Intel Corporation
# SPDX-License-Identifier: Apache-2.0

set -e
echo "IMAGE_REPO=${IMAGE_REPO}"
IMAGE_TAG=${IMAGE_TAG:-"latest"}
echo "REGISTRY=IMAGE_REPO=${IMAGE_REPO}"
echo "TAG=IMAGE_TAG=${IMAGE_TAG}"
# export REGISTRY=${IMAGE_REPO}
# export TAG=${IMAGE_TAG}

WORKPATH=$(dirname "$PWD")
LOG_PATH="$WORKPATH/tests"
ip_address=$(hostname -I | awk '{print $1}')

function build_docker_images() {
    cd $WORKPATH/docker_image_build
    if [ ! -d "GenAIComps" ] ; then
        git clone https://github.com/opea-project/GenAIComps.git && cd GenAIComps && git checkout "${opea_branch:-"main"}" && cd ../
    fi
    cd GenAIComps

    docker build -t opea/embedding-tei:latest -f comps/embeddings/tei/langchain/Dockerfile .
    docker build -t opea/retriever-redis:latest -f comps/retrievers/redis/langchain/Dockerfile .
    docker build -t opea/reranking-tei:latest -f comps/reranks/tei/Dockerfile .
    docker build -t opea/dataprep-redis:latest -f comps/dataprep/redis/langchain/Dockerfile .

    docker pull ghcr.io/huggingface/text-embeddings-inference:cpu-1.5
    docker pull redis/redis-stack:7.2.0-v9

    cd $WORKPATH/
    docker build -t opea/doc-index-retriever:latest -f ./Dockerfile .
}

function start_services() {
    cd $WORKPATH/docker_compose/intel/cpu/xeon
    export EMBEDDING_MODEL_ID="BAAI/bge-base-en-v1.5"
    export RERANK_MODEL_ID="BAAI/bge-reranker-base"
    export TEI_EMBEDDING_ENDPOINT="http://${ip_address}:6006"
    export TEI_RERANKING_ENDPOINT="http://${ip_address}:8808"
    export TGI_LLM_ENDPOINT="http://${ip_address}:8008"
    export REDIS_URL="redis://${ip_address}:6379"
    export INDEX_NAME="rag-redis"
    export HUGGINGFACEHUB_API_TOKEN=${HUGGINGFACEHUB_API_TOKEN}
    export MEGA_SERVICE_HOST_IP=${ip_address}
    export EMBEDDING_SERVICE_HOST_IP=${ip_address}
    export RETRIEVER_SERVICE_HOST_IP=${ip_address}
    export RERANK_SERVICE_HOST_IP=${ip_address}
    export LLM_SERVICE_HOST_IP=${ip_address}
    export RERANK_SERVICE_PORT=18000

    # Start Docker Containers
    docker compose up -d
    sleep 20
}

function validate() {
    local CONTENT="$1"
    local EXPECTED_RESULT="$2"
    local SERVICE_NAME="$3"

    if echo "$CONTENT" | grep -q "$EXPECTED_RESULT"; then
        echo "[ $SERVICE_NAME ] Content is as expected: $CONTENT."
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
     -F 'link_list=["https://opea.dev"]')
    local EXIT_CODE=$(validate "$CONTENT" "Data preparation succeeded" "dataprep-redis-service-xeon")
    echo "$EXIT_CODE"
    local EXIT_CODE="${EXIT_CODE:0-1}"
    echo "return value is $EXIT_CODE"
    if [ "$EXIT_CODE" == "1" ]; then
        docker logs dataprep-redis-server | tee -a ${LOG_PATH}/dataprep-redis-service-xeon.log
        return 1
    fi

    # Curl the Mega Service
    echo "Testing retriever service"
    local CONTENT=$(curl http://${ip_address}:8889/v1/retrievaltool -X POST -H "Content-Type: application/json" -d '{
     "text": "Explain the OPEA project?"
    }')
    local EXIT_CODE=$(validate "$CONTENT" "OPEA" "doc-index-retriever-service-xeon")
    echo "$EXIT_CODE"
    local EXIT_CODE="${EXIT_CODE:0-1}"
    echo "return value is $EXIT_CODE"
    if [ "$EXIT_CODE" == "1" ]; then
        docker logs tei-embedding-xeon-server | tee -a ${LOG_PATH}/doc-index-retriever-service-xeon.log
        docker logs retriever-redis-server | tee -a ${LOG_PATH}/doc-index-retriever-service-xeon.log
        docker logs reranking-tei-server | tee -a ${LOG_PATH}/doc-index-retriever-service-xeon.log
        docker logs doc-index-retriever-server | tee -a ${LOG_PATH}/doc-index-retriever-service-xeon.log
        exit 1
    fi
}

function stop_docker() {
    cd $WORKPATH/docker_compose/intel/cpu/xeon
    container_list=$(cat compose.yaml | grep container_name | cut -d':' -f2)
    for container_name in $container_list; do
        cid=$(docker ps -aq --filter "name=$container_name")
        echo "Stopping container $container_name"
        if [[ ! -z "$cid" ]]; then docker rm $cid -f && sleep 1s; fi
    done
}

function main() {

    stop_docker
    build_docker_images
    start_time=$(date +%s)
    start_services
    end_time=$(date +%s)
    duration=$((end_time-start_time))
    echo "Mega service start duration is $duration s"
    validate_megaservice

    stop_docker
    echo y | docker system prune

}

main
