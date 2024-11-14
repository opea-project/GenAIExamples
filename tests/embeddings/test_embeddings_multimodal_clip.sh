#!/bin/bash
# Copyright (C) 2024 Intel Corporation
# SPDX-License-Identifier: Apache-2.0

set -x

WORKPATH=$(dirname "$PWD")
ip_address=$(hostname -I | awk '{print $1}')

function build_docker_images() {
    cd $WORKPATH
    echo $(pwd)
    docker build --no-cache -t opea/embedding-multimodal:comps --build-arg https_proxy=$https_proxy --build-arg http_proxy=$http_proxy  -f comps/embeddings/multimodal_clip/Dockerfile .
    if [ $? -ne 0 ]; then
        echo "opea/embedding-multimodal built fail"
        exit 1
    else
        echo "opea/embedding-multimodal built successful"
    fi
}

function start_service() {
    docker run -d --name="test-embedding-multimodal-server" -e LOGFLAG=True -e http_proxy=$http_proxy -e https_proxy=$https_proxy -p 5038:6000 --ipc=host  opea/embedding-multimodal:comps
    sleep 3m
}

function validate_service() {
    local INPUT_DATA="$1"
    service_port=5038
    result=$(http_proxy="" curl http://${ip_address}:$service_port/v1/embeddings \
        -X POST \
        -d "$INPUT_DATA" \
        -H 'Content-Type: application/json')
    if [[ $result == *"embedding"* ]]; then
        echo "Result correct."
    else
        echo "Result wrong. Received was $result"
        docker logs test-embedding-multimodal-server
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
    cid=$(docker ps -aq --filter "name=test-embedding-multimodal-server-*")
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
