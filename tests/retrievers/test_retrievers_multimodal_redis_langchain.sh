#!/bin/bash
# Copyright (C) 2024 Intel Corporation
# SPDX-License-Identifier: Apache-2.0

set -x

WORKPATH=$(dirname "$PWD")
LOG_PATH="$WORKPATH/tests"
ip_address=$(hostname -I | awk '{print $1}')

function build_docker_images() {
    cd $WORKPATH
    docker build --no-cache -t opea/retriever-multimodal-redis:comps --build-arg https_proxy=$https_proxy --build-arg http_proxy=$http_proxy -f comps/retrievers/multimodal/redis/langchain/Dockerfile .
    if [ $? -ne 0 ]; then
        echo "opea/retriever-multimodal-redis built fail"
        exit 1
    else
        echo "opea/retriever-multimodal-redis built successful"
    fi
}

function start_service() {
    # redis
    docker run -d --name test-comps-multimodal-retriever-redis-vector-db -p 5689:6379 -p 5011:8001 -e HTTPS_PROXY=$https_proxy -e HTTP_PROXY=$https_proxy redis/redis-stack:7.2.0-v9
    sleep 10s

    # redis retriever
    export REDIS_URL="redis://${ip_address}:5689"
    export INDEX_NAME="rag-redis"
    retriever_port=5434
    unset http_proxy
    docker run -d --name="test-comps-retriever-multimodal-redis" -p ${retriever_port}:7000 --ipc=host -e http_proxy=$http_proxy -e https_proxy=$https_proxy -e REDIS_URL=$REDIS_URL -e INDEX_NAME=$INDEX_NAME opea/retriever-multimodal-redis:comps

    sleep 5m
}

function validate_microservice() {
    retriever_port=5434
    export PATH="${HOME}/miniforge3/bin:$PATH"
    source activate
    URL="http://${ip_address}:$retriever_port/v1/multimodal_retrieval"
    test_embedding=$(python -c "import random; embedding = [random.uniform(-1, 1) for _ in range(512)]; print(embedding)")

    HTTP_STATUS=$(curl -s -o /dev/null -w "%{http_code}" -X POST -d "{\"text\":\"test\",\"embedding\":${test_embedding}}" -H 'Content-Type: application/json' "$URL")
    if [ "$HTTP_STATUS" -eq 200 ]; then
        echo "[ retriever ] HTTP status is 200. Checking content..."
        local CONTENT=$(curl -s -X POST -d "{\"text\":\"test\",\"embedding\":${test_embedding}}" -H 'Content-Type: application/json' "$URL" | tee ${LOG_PATH}/retriever.log)

        if echo "$CONTENT" | grep -q "retrieved_docs"; then
            echo "[ retriever ] Content is as expected."
        else
            echo "[ retriever ] Content does not match the expected result: $CONTENT"
            docker logs test-comps-retriever-multimodal-redis >> ${LOG_PATH}/retriever.log
            exit 1
        fi
    else
        echo "[ retriever ] HTTP status is not 200. Received status was $HTTP_STATUS"
        docker logs test-comps-retriever-multimodal-redis >> ${LOG_PATH}/retriever.log
        exit 1
    fi
}

function stop_docker() {
    cid_retrievers=$(docker ps -aq --filter "name=test-comps-*")
    if [[ ! -z "$cid_retrievers" ]]; then
        docker stop $cid_retrievers && docker rm $cid_retrievers && sleep 1s
    fi
}

function main() {

    stop_docker

    build_docker_images
    start_service

    validate_microservice

    stop_docker
    echo y | docker system prune

}

main
