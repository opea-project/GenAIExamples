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
    docker build --no-cache -t opea/pii-pg:comps -f comps/guardrails/pii_detection/predictionguard/Dockerfile .
    if [ $? -ne 0 ]; then
        echo "opea/pii-pg build failed"
        exit 1
    else
        echo "opea/pii-pg built successfully"
    fi
}

function start_service() {
    pii_service_port=9080
    unset http_proxy
    docker run -d --name=test-comps-pii-pg-server \
        -e http_proxy= -e https_proxy= \
        -e PREDICTIONGUARD_API_KEY=${PREDICTIONGUARD_API_KEY} \
        -p 9080:9080 --ipc=host opea/pii-pg:comps
    sleep 60  # Sleep for 1 minute to allow the service to start
}

function validate_microservice() {
    pii_service_port=9080
    result=$(http_proxy="" curl http://${ip_address}:${pii_service_port}/v1/pii \
        -X POST \
        -d '{"prompt": "My name is John Doe and my phone number is 123-456-7890.", "replace": true, "replace_method": "mask"}' \
        -H 'Content-Type: application/json')

    if [[ $result == *"new_prompt"* || $result == *"detected_pii"* ]]; then
        echo "Service response is correct."
    else
        echo "Result wrong. Received was $result"
        docker logs test-comps-pii-pg-server
        exit 1
    fi
}

function stop_docker() {
    cid=$(docker ps -aq --filter "name=test-comps-pii-pg-*")
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
