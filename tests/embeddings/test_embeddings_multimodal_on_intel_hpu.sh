#!/bin/bash
# Copyright (C) 2024 Intel Corporation
# SPDX-License-Identifier: Apache-2.0

set -x

WORKPATH=$(dirname "$PWD")
ip_address=$(hostname -I | awk '{print $1}')
export your_mmei_port=8087
export EMBEDDER_PORT=$your_mmei_port
export MMEI_EMBEDDING_ENDPOINT="http://$ip_address:$your_mmei_port/v1/encode"
export your_embedding_port_microservice=6608
export MM_EMBEDDING_PORT_MICROSERVICE=$your_embedding_port_microservice
unset http_proxy

function build_mmei_docker_images() {
    cd $WORKPATH
    echo $(pwd)
    docker build --no-cache -t opea/embedding-multimodal-bridgetower:latest --build-arg EMBEDDER_PORT=$EMBEDDER_PORT --build-arg https_proxy=$https_proxy --build-arg http_proxy=$http_proxy -f comps/embeddings/multimodal/bridgetower/Dockerfile.intel_hpu .

    if [ $? -ne 0 ]; then
        echo "opea/embedding-multimodal-bridgetower built fail"
        exit 1
    else
        echo "opea/embedding-multimodal-bridgetower built successful"
    fi
}

function build_embedding_service_images() {
    cd $WORKPATH
    echo $(pwd)
    docker build --no-cache -t opea/embedding-multimodal:latest --build-arg https_proxy=$https_proxy --build-arg http_proxy=$http_proxy -f comps/embeddings/multimodal/multimodal_langchain/Dockerfile .

    if [ $? -ne 0 ]; then
        echo "opea/embedding-multimodal built fail"
        exit 1
    else
        echo "opea/embedding-multimodal built successful"
    fi
}

function build_docker_images() {
    build_mmei_docker_images
    build_embedding_service_images
}

function start_service() {
    cd $WORKPATH
    cd comps/embeddings/multimodal/bridgetower/
    docker compose -f docker_compose_bridgetower_embedding_endpoint.yaml up -d
    cd $WORKPATH
    cd comps/embeddings/multimodal/multimodal_langchain/
    docker compose -f docker_compose_multimodal_embedding.yaml up -d
    sleep 2m
}

function validate_microservice_text_embedding() {
    result=$(http_proxy="" curl http://${ip_address}:$MM_EMBEDDING_PORT_MICROSERVICE/v1/embeddings \
        -X POST \
        -H "Content-Type: application/json" \
        -d '{"text" : "This is some sample text."}')

    if [[ $result == *"embedding"* ]]; then
        echo "Result correct."
    else
        echo "Result wrong. Received was $result"
        docker logs embedding-multimodal-bridgetower
        docker logs embedding-multimodal
        exit 1
    fi
}

function validate_microservice_image_text_pair_embedding() {
    result=$(http_proxy="" curl http://${ip_address}:$MM_EMBEDDING_PORT_MICROSERVICE/v1/embeddings \
        -X POST \
        -H "Content-Type: application/json" \
        -d '{"text": {"text" : "This is some sample text."}, "image" : {"url": "https://github.com/docarray/docarray/blob/main/tests/toydata/image-data/apple.png?raw=true"}}')

    if [[ $result == *"embedding"* ]]; then
        echo "Result correct."
    else
        echo "Result wrong. Received was $result"
        docker logs embedding-multimodal-bridgetower
        docker logs embedding-multimodal
        exit 1
    fi
}

function validate_microservice() {
    validate_microservice_text_embedding
    validate_microservice_image_text_pair_embedding
}

function stop_docker() {
    cid=$(docker ps -aq --filter "name=embedding-multimodal-bridgetower" --filter "name=embedding-multimodal")
    if [[ ! -z "$cid" ]]; then docker stop $cid && docker rm $cid && sleep 1s; fi
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
