#!/bin/bash
# Copyright (C) 2024 Intel Corporation
# SPDX-License-Identifier: Apache-2.0

set -xe

WORKPATH=$(dirname "$PWD")
ip_address=$(hostname -I | awk '{print $1}')
function build_docker_images() {
    cd $WORKPATH
    docker build --no-cache -t opea/retriever-qdrant:comps --build-arg https_proxy=$https_proxy --build-arg http_proxy=$http_proxy -f comps/retrievers/haystack/qdrant/docker/Dockerfile .
}

function start_service() {
    # qdrant
    docker run -d --name test-qdrant-vector-db -p 5010:6333 -e HTTPS_PROXY=$https_proxy -e HTTP_PROXY=$https_proxy qdrant/qdrant
    sleep 10s

    # tei endpoint
    tei_endpoint=5008
    model="BAAI/bge-base-en-v1.5"
    docker run -d --name="test-comps-retriever-tei-endpoint" -e HTTPS_PROXY=$https_proxy -e HTTP_PROXY=$https_proxy -p $tei_endpoint:80 -v ./data:/data --pull always ghcr.io/huggingface/text-embeddings-inference:cpu-1.2 --model-id $model
    sleep 30s
    export TEI_EMBEDDING_ENDPOINT="http://${ip_address}:${tei_endpoint}"

    # qdrant retriever
    export QDRANT_HOST="${ip_address}"
    export QDRANT_PORT=5010
    export INDEX_NAME="rag-qdrant"
    retriever_port=5009
    unset http_proxy
    docker run -d --name="test-comps-retriever-qdrant-server" -p ${retriever_port}:7000 --ipc=host -e TEI_EMBEDDING_ENDPOINT=$TEI_EMBEDDING_ENDPOINT -e http_proxy=$http_proxy -e https_proxy=$https_proxy -e QDRANT_HOST=$QDRANT_HOST -e QDRANT_PORT=$QDRANT_PORT -e INDEX_NAME=$INDEX_NAME opea/retriever-qdrant:comps

    sleep 3m
}

function validate_microservice() {
    retriever_port=5009
    export PATH="${HOME}/miniforge3/bin:$PATH"
    source activate
    test_embedding=$(python -c "import random; embedding = [random.uniform(-1, 1) for _ in range(768)]; print(embedding)")
    http_proxy='' curl http://${ip_address}:$retriever_port/v1/retrieval \
        -X POST \
        -d "{\"text\":\"test\",\"embedding\":${test_embedding}}" \
        -H 'Content-Type: application/json'
    docker logs test-comps-retriever-qdrant-server
    docker logs test-comps-retriever-tei-endpoint
}

function stop_docker() {
    cid_retrievers=$(docker ps -aq --filter "name=test-comps-retrievers*")
    if [[ ! -z "$cid_retrievers" ]]; then
        docker stop $cid_retrievers && docker rm $cid_retrievers && sleep 1s
    fi

    cid_qdrant=$(docker ps -aq --filter "name=test-qdrant-vector-db")
    if [[ ! -z "$cid_qdrant" ]]; then
        docker stop $cid_qdrant && docker rm $cid_qdrant && sleep 1s
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
