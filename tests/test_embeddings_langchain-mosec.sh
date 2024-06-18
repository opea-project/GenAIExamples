#!/bin/bash
# Copyright (C) 2024 Intel Corporation
# SPDX-License-Identifier: Apache-2.0

set -xe

WORKPATH=$(dirname "$PWD")
ip_address=$(hostname -I | awk '{print $1}')

function build_mosec_docker_images() {
    cd $WORKPATH
    echo $(pwd)
    docker build --build-arg http_proxy=$http_proxy --build-arg https_proxy=$https_proxy --no-cache -t langchain-mosec:comps -f comps/embeddings/langchain-mosec/mosec-docker/Dockerfile .
}

function build_docker_images() {
    cd $WORKPATH
    echo $(pwd)
    docker build --build-arg http_proxy=$http_proxy --build-arg https_proxy=$https_proxy --no-cache -t opea/embedding-langchain-mosec:comps -f comps/embeddings/langchain-mosec/docker/Dockerfile .
}

function start_service() {
    mosec_endpoint=5001
    model="BAAI/bge-large-en-v1.5"
    unset http_proxy
    docker run -d --name="test-comps-embedding-langchain-mosec-endpoint" -p $mosec_endpoint:8000  langchain-mosec:comps
    export MOSEC_EMBEDDING_ENDPOINT="http://${ip_address}:${mosec_endpoint}"
    mosec_service_port=5002
    docker run -d --name="test-comps-embedding-langchain-mosec-server" -e http_proxy=$http_proxy -e https_proxy=$https_proxy -p ${mosec_service_port}:6000 --ipc=host -e MOSEC_EMBEDDING_ENDPOINT=$MOSEC_EMBEDDING_ENDPOINT  opea/embedding-langchain-mosec:comps
    sleep 3m
}

function validate_microservice() {
    mosec_service_port=5002
    http_proxy="" curl http://${ip_address}:$mosec_service_port/v1/embeddings \
        -X POST \
        -d '{"text":"What is Deep Learning?"}' \
        -H 'Content-Type: application/json'
}

function stop_docker() {
    cid=$(docker ps -aq --filter "name=test-comps-embedding-langchain-mosec-*")
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
