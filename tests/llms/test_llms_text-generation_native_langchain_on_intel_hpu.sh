#!/bin/bash
# Copyright (C) 2024 Intel Corporation
# SPDX-License-Identifier: Apache-2.0

set -x

WORKPATH=$(dirname "$PWD")
LOG_PATH="$WORKPATH/tests"
ip_address=$(hostname -I | awk '{print $1}')

function build_docker_images() {
    cd $WORKPATH
    docker build --no-cache \
        --build-arg https_proxy=$https_proxy --build-arg http_proxy=$http_proxy \
        -t opea/llm-native:comps \
        -f comps/llms/text-generation/native/langchain/Dockerfile .
    if [ $? -ne 0 ]; then
        echo "opea/llm-native built fail"
        exit 1
    else
        echo "opea/llm-native built successful"
    fi
}

function start_service() {
    LLM_NATIVE_MODEL="Qwen/Qwen2-7B-Instruct"
    llm_native_service_port=5070
    docker run -d \
        --name="test-comps-llm-native-server" \
        -p ${llm_native_service_port}:9000 \
        --runtime=habana \
        --cap-add=SYS_NICE \
        --ipc=host \
        -e http_proxy=${http_proxy} \
        -e https_proxy=${https_proxy} \
        -e LLM_NATIVE_MODEL=${LLM_NATIVE_MODEL} \
        -e HABANA_VISIBLE_DEVICES=all \
        -e OMPI_MCA_btl_vader_single_copy_mechanism=none \
        -e TOKENIZERS_PARALLELISM=false \
        --restart unless-stopped \
        --network bridge \
        opea/llm-native:comps

    sleep 3m
}

function validate_microservice() {
    llm_native_service_port=5070
    URL="http://${ip_address}:${llm_native_service_port}/v1/chat/completions"
    INPUT_DATA='{"query":"What is Deep Learning?"}'
    HTTP_RESPONSE=$(curl --silent --write-out "HTTPSTATUS:%{http_code}" -X POST -d "$INPUT_DATA" -H 'Content-Type: application/json' "$URL")
    HTTP_STATUS=$(echo $HTTP_RESPONSE | tr -d '\n' | sed -e 's/.*HTTPSTATUS://')
    RESPONSE_BODY=$(echo $HTTP_RESPONSE | sed -e 's/HTTPSTATUS\:.*//g')
    SERVICE_NAME="llm-native"

    # check response status
    if [ "$HTTP_STATUS" -ne "200" ]; then
        echo "[ $SERVICE_NAME ] HTTP status is not 200. Received status was $HTTP_STATUS"
        docker logs test-comps-llm-native-server >> ${LOG_PATH}/${SERVICE_NAME}.log
        exit 1
    else
        echo "[ $SERVICE_NAME ] HTTP status is 200. Checking content..."
    fi
    # check response body
    if [[ "$RESPONSE_BODY" != *'"text":"What'* ]]; then
        echo "[ $SERVICE_NAME ] Content does not match the expected result: $RESPONSE_BODY"
        docker logs test-comps-llm-native-server >> ${LOG_PATH}/${SERVICE_NAME}.log
        exit 1
    else
        echo "[ $SERVICE_NAME ] Content is as expected."
    fi
}

function stop_docker() {
    cid=$(docker ps -aq --filter "name=test-comps-llm-native*")
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
