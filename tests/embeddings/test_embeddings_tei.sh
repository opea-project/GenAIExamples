#!/bin/bash
# Copyright (C) 2024 Intel Corporation
# SPDX-License-Identifier: Apache-2.0

set -x

WORKPATH=$(dirname "$PWD")
ip_address=$(hostname -I | awk '{print $1}')

function build_docker_images() {
    cd $WORKPATH
    echo $(pwd)
    docker build --no-cache -t opea/embedding:comps -f comps/embeddings/src/Dockerfile .
    if [ $? -ne 0 ]; then
        echo "opea/embedding built fail"
        exit 1
    else
        echo "opea/embedding built successful"
    fi
}

function start_service() {
    tei_endpoint=5001
    model="BAAI/bge-base-en-v1.5"
    unset http_proxy
    docker run -d --name="test-comps-embedding-endpoint" -p $tei_endpoint:80 -v ./data:/data --pull always ghcr.io/huggingface/text-embeddings-inference:cpu-1.5 --model-id $model
    sleep 3m
    export TEI_EMBEDDING_ENDPOINT="http://${ip_address}:${tei_endpoint}"
    tei_service_port=5002
    docker run -d --name="test-comps-embedding-server" -e LOGFLAG=True -e http_proxy=$http_proxy -e https_proxy=$https_proxy -p ${tei_service_port}:6000 --ipc=host -e TEI_EMBEDDING_ENDPOINT=$TEI_EMBEDDING_ENDPOINT -e EMBEDDING_COMPONENT_NAME="OPEA_TEI_EMBEDDING" opea/embedding:comps
    sleep 15
}

function validate_service() {
    local INPUT_DATA="$1"
    tei_service_port=5002
    result=$(http_proxy="" curl http://${ip_address}:$tei_service_port/v1/embeddings \
        -X POST \
        -d "$INPUT_DATA" \
        -H 'Content-Type: application/json')
    if [[ $result == *"embedding"* ]]; then
        echo "Result correct."
    else
        echo "Result wrong. Received was $result"
        docker logs test-comps-embedding-endpoint
        docker logs test-comps-embedding-server
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

function validate_microservice_with_openai() {
    tei_service_port=5002
    python3 ${WORKPATH}/tests/utils/validate_svc_with_openai.py $ip_address $tei_service_port "embedding"
    if [ $? -ne 0 ]; then
        docker logs test-comps-embedding-endpoint
        docker logs test-comps-embedding-server
        exit 1
    fi
}

function stop_docker() {
    cid=$(docker ps -aq --filter "name=test-comps-embedding-*")
    if [[ ! -z "$cid" ]]; then docker stop $cid && docker rm $cid && sleep 1s; fi
}

function main() {

    stop_docker

    build_docker_images
    start_service

    validate_microservice
    validate_microservice_with_openai

    stop_docker
    echo y | docker system prune

}

main
