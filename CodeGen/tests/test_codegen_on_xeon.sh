#!/bin/bash
# Copyright (C) 2024 Intel Corporation
# SPDX-License-Identifier: Apache-2.0

set -xe

WORKPATH=$(dirname "$PWD")
LOG_PATH="$WORKPATH/tests"
ip_address=$(hostname -I | awk '{print $1}')

function build_docker_images() {
    cd $WORKPATH
    git clone https://github.com/opea-project/GenAIComps.git
    cd GenAIComps

    docker build -t opea/llm-tgi:latest -f comps/llms/text-generation/tgi/Dockerfile .

    cd $WORKPATH/docker
    docker build --no-cache -t opea/codegen:latest -f Dockerfile .

    cd $WORKPATH/docker/ui
    docker build --no-cache -t opea/codegen-ui:latest -f docker/Dockerfile .

    docker images
}

function start_services() {
    cd $WORKPATH/docker/xeon

    export LLM_MODEL_ID="Intel/neural-chat-7b-v3-3"
    export TGI_LLM_ENDPOINT="http://${ip_address}:8028"
    export HUGGINGFACEHUB_API_TOKEN=${HUGGINGFACEHUB_API_TOKEN}
    export MEGA_SERVICE_HOST_IP=${ip_address}
    export LLM_SERVICE_HOST_IP=${ip_address}
    export BACKEND_SERVICE_ENDPOINT="http://${ip_address}:6666/v1/codegen"

    # Start Docker Containers
    # TODO: Replace the container name with a test-specific name
    docker compose -f docker_compose.yaml up -d

    sleep 2m # Waits 2 minutes
}

function validate_microservices() {
    # Check if the microservices are running correctly.
    # TODO: Any results check required??

    export PATH="${HOME}/miniforge3/bin:$PATH"

    curl http://${ip_address}:8028/generate \
        -X POST \
        -d '{"inputs":"def print_hello_world():","parameters":{"max_new_tokens":256, "do_sample": true}}' \
        -H 'Content-Type: application/json' > ${LOG_PATH}/generate.log
    sleep 5s

    curl http://${ip_address}:9000/v1/chat/completions \
        -X POST \
        -d '{"text":"def print_hello_world():"}' \
        -H 'Content-Type: application/json' > ${LOG_PATH}/completions.log
    sleep 5s
}

function validate_megaservice() {
    # Curl the Mega Service
    curl http://${ip_address}:6666/v1/codegen -H "Content-Type: application/json" -d '{
        "messages": "def print_hello_world():"}' > ${LOG_PATH}/curl_megaservice.log

    sleep 2s
    echo "Checking response results, make sure the output is reasonable. "
    local status=false
    if [[ -f $LOG_PATH/curl_megaservice.log ]] && \
    [[ $(grep -c "Hello" $LOG_PATH/curl_megaservice.log) != 0 ]]; then
        status=true
    fi

    if [ $status == false ]; then
        echo "Response check failed, please check the logs in artifacts!"
        exit 1
    else
        echo "Response check succeed!"
    fi

    echo "Checking response format, make sure the output format is acceptable for UI."
    # TODO

}

function stop_docker() {
    cd $WORKPATH/docker/xeon
    container_list=$(cat docker_compose.yaml | grep container_name | cut -d':' -f2)
    for container_name in $container_list; do
        cid=$(docker ps -aq --filter "name=$container_name")
        if [[ ! -z "$cid" ]]; then docker stop $cid && docker rm $cid && sleep 1s; fi
    done
}

function main() {

    stop_docker

    build_docker_images
    start_services

    validate_microservices
    validate_megaservice

    stop_docker
    echo y | docker system prune

}

main
