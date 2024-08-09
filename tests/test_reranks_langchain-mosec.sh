#!/bin/bash
# Copyright (C) 2024 Intel Corporation
# SPDX-License-Identifier: Apache-2.0

set -xe

WORKPATH=$(dirname "$PWD")
ip_address=$(hostname -I | awk '{print $1}')

function build_mosec_docker_images() {
    cd $WORKPATH
    echo $(pwd)
    docker build --build-arg http_proxy=$http_proxy --build-arg https_proxy=$https_proxy --no-cache -t opea/reranking-langchain-mosec-endpoint:comps -f comps/reranks/langchain-mosec/mosec-docker/Dockerfile .
}

function build_docker_images() {
    cd $WORKPATH
    echo $(pwd)
    docker build --build-arg http_proxy=$http_proxy --build-arg https_proxy=$https_proxy --no-cache -t opea/reranking-langchain-mosec:comps -f comps/reranks/langchain-mosec/docker/Dockerfile .
}

function start_service() {
    mosec_endpoint=5006
    model="BAAI/bge-reranker-large"
    unset http_proxy
    docker run -d --name="test-comps-reranking-langchain-mosec-endpoint" -p $mosec_endpoint:8000  opea/reranking-langchain-mosec-endpoint:comps
    export MOSEC_RERANKING_ENDPOINT="http://${ip_address}:${mosec_endpoint}"
    mosec_service_port=5007
    docker run -d --name="test-comps-reranking-langchain-mosec-server" -e http_proxy=$http_proxy -e https_proxy=$https_proxy -p ${mosec_service_port}:8000 --ipc=host -e MOSEC_RERANKING_ENDPOINT=$MOSEC_RERANKING_ENDPOINT  opea/reranking-langchain-mosec:comps
    sleep 3m
}

function validate_microservice() {
    mosec_service_port=5007
    http_proxy="" curl http://${ip_address}:${mosec_service_port}/v1/reranking\
        -X POST \
        -d '{"initial_query":"What is Deep Learning?", "retrieved_docs": [{"text":"Deep Learning is not..."}, {"text":"Deep learning is..."}]}' \
        -H 'Content-Type: application/json'
    docker logs test-comps-reranking-langchain-mosec-server
    docker logs test-comps-reranking-langchain-mosec-endpoint
}

function stop_docker() {
    cid=$(docker ps -aq --filter "name=test-comps-reranking-langchain-mosec-*")
    if [[ ! -z "$cid" ]]; then docker stop $cid && docker rm $cid && sleep 1s; fi
}

function main() {

    stop_docker

    build_mosec_docker_images

    build_docker_images

    start_service

    validate_microservice

    stop_docker
    echo y | docker system prune

}

main
