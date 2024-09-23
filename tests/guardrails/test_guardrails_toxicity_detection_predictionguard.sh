#!/bin/bash
# Copyright (C) 2024 Intel Corporation
# SPDX-License-Identifier: Apache-2.0

set -x  # Print commands and their arguments as they are executed

WORKPATH=$(dirname "$PWD")
ip_address=$(hostname -I | awk '{print $1}')  # Adjust to a more reliable command
if [ -z "$ip_address" ]; then
    ip_address="localhost"  # Default to localhost if IP address is empty
fi

function build_docker_images() {
    cd $WORKPATH
    echo $(pwd)
    docker build --no-cache -t opea/toxicity-pg:comps -f comps/guardrails/toxicity_detection/predictionguard/Dockerfile .
    if [ $? -ne 0 ]; then
        echo "opea/toxicity-pg build failed"
        exit 1
    else
        echo "opea/toxicity-pg built successfully"
    fi
}

function start_service() {
    toxicity_service_port=9090
    unset http_proxy
    docker run -d --name=test-comps-toxicity-pg-server \
        -e http_proxy= -e https_proxy= \
        -e PREDICTIONGUARD_API_KEY=${PREDICTIONGUARD_API_KEY} \
        -p 9090:9090 --ipc=host opea/toxicity-pg:comps
    sleep 60  # Sleep for 1 minute to allow the service to start
}

function validate_microservice() {
    toxicity_service_port=9090
    result=$(http_proxy="" curl http://${ip_address}:${toxicity_service_port}/v1/toxicity \
        -X POST \
        -d '{"text": "I hate you."}' \
        -H 'Content-Type: application/json')

    if [[ $result == *"score"* ]]; then
        echo "Service response is correct."
    else
        echo "Result wrong. Received was $result"
        docker logs test-comps-toxicity-pg-server
        exit 1
    fi
}

function stop_docker() {
    cid=$(docker ps -aq --filter "name=test-comps-toxicity-pg-*")
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
