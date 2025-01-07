#!/bin/bash
# Copyright (C) 2024 Intel Corporation
# SPDX-License-Identifier: Apache-2.0

set -x

WORKPATH=$(dirname "$PWD")
ip_address=$(hostname -I | awk '{print $1}')  # Adjust to a more reliable command
if [ -z "$ip_address" ]; then
    ip_address="localhost"  # Default to localhost if IP address is empty
fi

function build_docker_images() {
    cd $WORKPATH
    echo $(pwd)
    docker build --no-cache -t opea/embedding:comps -f comps/embeddings/src/Dockerfile .
    if [ $? -ne 0 ]; then
        echo "opea/embedding built fail"
        exit 1
    else
        echo "opea/embedding built successfully"
    fi
}

function start_service() {
    pg_service_port=5124
    unset http_proxy
    docker run -d --name=test-comps-embedding-pg-server \
    -e LOGFLAG=True -e http_proxy=$http_proxy -e https_proxy=$https_proxy \
    -e PREDICTIONGUARD_API_KEY=${PREDICTIONGUARD_API_KEY} \
    -e EMBEDDING_COMPONENT_NAME="OPEA_PREDICTIONGUARD_EMBEDDING" \
    -p ${pg_service_port}:6000 --ipc=host opea/embedding:comps
    sleep 60
}

function validate_service() {
    local INPUT_DATA="$1"
    pg_service_port=5124
    result=$(http_proxy="" curl http://${ip_address}:${pg_service_port}/v1/embeddings \
        -X POST \
        -d "$INPUT_DATA" \
        -H 'Content-Type: application/json')

    # Check for a proper response format
    if [[ $result == *"embedding"* ]]; then
        echo "Result correct."
    elif [[ $result == *"error"* || $result == *"detail"* ]]; then
        echo "Result wrong. Error received was: $result"
        docker logs test-comps-embedding-pg-server
        exit 1
    else
        echo "Unexpected result format received was: $result"
        docker logs test-comps-embedding-pg-server
        exit 1
    fi
}

function validate_microservice() {
    ## Test OpenAI API, input single text
    validate_service \
        '{"input":"What is Deep Learning?"}'

    ## Test OpenAI API, input multiple texts with parameters
    validate_service \
        '{"input":["What is Deep Learning?","How are you?"], "dimensions":100}'
}

function stop_docker() {
    cid=$(docker ps -aq --filter "name=test-comps-embedding-pg-*")
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
