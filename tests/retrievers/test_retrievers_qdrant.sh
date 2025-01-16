#!/bin/bash
# Copyright (C) 2024 Intel Corporation
# SPDX-License-Identifier: Apache-2.0

set -x

WORKPATH=$(dirname "$PWD")
LOG_PATH="$WORKPATH/tests"
ip_address=$(hostname -I | awk '{print $1}')
function build_docker_images() {
    cd $WORKPATH
    docker build --no-cache -t opea/retriever-qdrant:comps --build-arg https_proxy=$https_proxy --build-arg http_proxy=$http_proxy -f comps/retrievers/src/Dockerfile .
    if [ $? -ne 0 ]; then
        echo "opea/retriever-qdrant built fail"
        exit 1
    else
        echo "opea/retriever-qdrant built successful"
    fi
}

function start_service() {
    # qdrant
    export QDRANT_PORT=5056
    docker run -d --name test-comps-retriever-qdrant-vector-db -p $QDRANT_PORT:6333 -e HTTPS_PROXY=$https_proxy -e HTTP_PROXY=$https_proxy qdrant/qdrant
    sleep 10s

    # qdrant retriever
    export QDRANT_HOST="${ip_address}"
    export INDEX_NAME="rag-qdrant"
    retriever_port=5057
    unset http_proxy
    docker run -d --name="test-comps-retriever-qdrant-server" -p ${retriever_port}:7000 --ipc=host -e http_proxy=$http_proxy -e https_proxy=$https_proxy -e QDRANT_HOST=$QDRANT_HOST -e QDRANT_PORT=$QDRANT_PORT -e INDEX_NAME=$INDEX_NAME -e RETRIEVER_COMPONENT_NAME="OPEA_RETRIEVER_QDRANT" opea/retriever-qdrant:comps

    sleep 3m
}

function validate_microservice() {
    retriever_port=5057
    export PATH="${HOME}/miniforge3/bin:$PATH"
    source activate
    test_embedding=$(python -c "import random; embedding = [random.uniform(-1, 1) for _ in range(768)]; print(embedding)")
    result=$(http_proxy='' curl http://${ip_address}:$retriever_port/v1/retrieval \
        -X POST \
        -d "{\"text\":\"test\",\"embedding\":${test_embedding}}" \
        -H 'Content-Type: application/json')
    if [[ $result == *"retrieved_docs"* ]]; then
        echo "Result correct."
    else
        echo "Result wrong. Received was $result"
        docker logs test-comps-retriever-qdrant-server >> ${LOG_PATH}/retriever.log
        exit 1
    fi
}

function stop_docker() {
    cid_retrievers=$(docker ps -aq --filter "name=test-comps-retriever-qdrant*")
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
