#!/bin/bash
# Copyright (C) 2024 Prediction Guard, Inc.
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
    docker build --no-cache -t opea/lvm-pg:comps -f comps/lvms/predictionguard/Dockerfile .
    if [ $? -ne 0 ]; then
        echo "opea/lvm-pg build failed"
        exit 1
    else
        echo "opea/lvm-pg built successfully"
    fi
}

function start_service() {
    lvm_service_port=9399
    unset http_proxy
    docker run -d --name=test-comps-lvm-pg-server \
        -e http_proxy= -e https_proxy= \
        -e PREDICTIONGUARD_API_KEY=${PREDICTIONGUARD_API_KEY} \
        -p 9399:9399 --ipc=host opea/lvm-pg:comps
    sleep 60  # Sleep for 1 minute to allow the service to start
}

function validate_microservice() {
    lvm_service_port=9399
    result=$(http_proxy="" curl http://${ip_address}:${lvm_service_port}/v1/lvm \
        -X POST \
        -d '{"image": "iVBORw0KGgoAAAANSUhEUgAAAAoAAAAKCAYAAACNMs+9AAAAFUlEQVR42mP8/5+hnoEIwDiqkL4KAcT9GO0U4BxoAAAAAElFTkSuQmCC", "prompt": "Describe the image.", "max_new_tokens": 100}' \
        -H 'Content-Type: application/json')

    if [[ $result == *"text"* ]]; then
        echo "Service response is correct."
    else
        echo "Result wrong. Received was $result"
        docker logs test-comps-lvm-pg-server
        exit 1
    fi
}

function stop_docker() {
    cid=$(docker ps -aq --filter "name=test-comps-lvm-pg-*")
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
