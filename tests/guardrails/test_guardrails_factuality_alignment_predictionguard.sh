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
    docker build --no-cache -t opea/factuality-pg:comps -f comps/guardrails/src/factuality_alignment/Dockerfile .
    if [ $? -ne 0 ]; then
        echo "opea/factuality-pg build failed"
        exit 1
    else
        echo "opea/factuality-pg built successfully"
    fi
}

function start_service() {
    factuality_service_port=9075
    unset http_proxy

    # Set your API key here (ensure this environment variable is set)
    docker run -d --name=test-comps-factuality-pg-server \
        -e http_proxy= -e https_proxy= \
        -e PREDICTIONGUARD_API_KEY=${PREDICTIONGUARD_API_KEY} \
        -p 9075:9075 --ipc=host opea/factuality-pg:comps
    sleep 60  # Sleep for 3 minutes to allow the service to start
}

function validate_microservice() {
    factuality_service_port=9075
    result=$(http_proxy="" curl http://${ip_address}:${factuality_service_port}/v1/factuality \
        -X POST \
        -d '{"reference": "The Eiffel Tower is in Paris.", "text": "The Eiffel Tower is in Berlin."}' \
        -H 'Content-Type: application/json')

    if [[ $result == *"score"* ]]; then
        echo "Service response is correct."
    else
        echo "Result wrong. Received was $result"
        docker logs test-comps-factuality-pg-server
        exit 1
    fi
}

function stop_docker() {
    cid=$(docker ps -aq --filter "name=test-comps-factuality-pg-*")
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
