#!/bin/bash
# Copyright (C) 2024 Intel Corporation
# SPDX-License-Identifier: Apache-2.0

set -x

WORKPATH=$(dirname "$PWD")
ip_address=$(hostname -I | awk '{print $1}')

function build_mosec_docker_images() {
    cd $WORKPATH
    echo $(pwd)
    docker build --build-arg http_proxy=$http_proxy --build-arg https_proxy=$https_proxy --no-cache -t opea/embedding-langchain-mosec-endpoint:comps -f comps/embeddings/mosec/langchain/dependency/Dockerfile .
    if [ $? -ne 0 ]; then
        echo "opea/embedding-langchain-mosec-endpoint built fail"
        exit 1
    else
        echo "opea/embedding-langchain-mosec-endpoint built successful"
    fi
}

function build_docker_images() {
    cd $WORKPATH
    echo $(pwd)
    docker build --build-arg http_proxy=$http_proxy --build-arg https_proxy=$https_proxy --no-cache -t opea/embedding-langchain-mosec:comps -f comps/embeddings/mosec/langchain/Dockerfile .
    if [ $? -ne 0 ]; then
        echo "opea/embedding-langchain-mosec built fail"
        exit 1
    else
        echo "opea/embedding-langchain-mosec built successful"
    fi
}

function start_service() {
    mosec_endpoint=5001
    model="BAAI/bge-base-en-v1.5"
    unset http_proxy
    docker run -d --name="test-comps-embedding-langchain-mosec-endpoint" -p $mosec_endpoint:8000  opea/embedding-langchain-mosec-endpoint:comps
    export MOSEC_EMBEDDING_ENDPOINT="http://${ip_address}:${mosec_endpoint}"
    mosec_service_port=5002
    docker run -d --name="test-comps-embedding-langchain-mosec-server" -e LOGFLAG=True -e http_proxy=$http_proxy -e https_proxy=$https_proxy -p ${mosec_service_port}:6000 --ipc=host -e MOSEC_EMBEDDING_ENDPOINT=$MOSEC_EMBEDDING_ENDPOINT  opea/embedding-langchain-mosec:comps
    sleep 3m
}

function validate_service() {
    local INPUT_DATA="$1"
    mosec_service_port=5002
    http_proxy="" curl http://${ip_address}:$mosec_service_port/v1/embeddings \
        -X POST \
        -d "$INPUT_DATA" \
        -H 'Content-Type: application/json'
    if [ $? -eq 0 ]; then
        echo "curl command executed successfully"
    else
        echo "curl command failed"
        docker logs test-comps-embedding-langchain-mosec-endpoint
        docker logs test-comps-embedding-langchain-mosec-server
        exit 1
    fi
}

function validate_microservice() {
    ## query with single text
    validate_service \
        '{"text":"What is Deep Learning?"}'

    ## query with multiple texts
    validate_service \
        '{"text":["What is Deep Learning?","How are you?"]}'

    ## Test OpenAI API, input single text
    validate_service \
        '{"input":"What is Deep Learning?"}'

    ## Test OpenAI API, input multiple texts with parameters
    validate_service \
        '{"input":["What is Deep Learning?","How are you?"], "dimensions":100}'
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
