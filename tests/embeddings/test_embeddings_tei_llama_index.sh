#!/bin/bash
# Copyright (C) 2024 Intel Corporation
# SPDX-License-Identifier: Apache-2.0

set -x

WORKPATH=$(dirname "$PWD")
LOG_PATH="$WORKPATH/tests"
ip_address=$(hostname -I | awk '{print $1}')

function build_docker_images() {
    cd $WORKPATH
    echo $(pwd)
    docker build --no-cache -t opea/embedding-tei-llama-index:comps --build-arg https_proxy=$https_proxy --build-arg http_proxy=$http_proxy -f comps/embeddings/tei/llama_index/Dockerfile .
    if [ $? -ne 0 ]; then
        echo "opea/embedding-tei-llama-index built fail"
        exit 1
    else
        echo "opea/embedding-tei-llama-index built successful"
    fi
}

function start_service() {
    tei_endpoint=5001
    model="BAAI/bge-base-en-v1.5"
    docker run -d --name="test-comps-embedding-tei-llama-index-endpoint" -p $tei_endpoint:80 -v ./data:/data -e http_proxy=$http_proxy -e https_proxy=$https_proxy --pull always ghcr.io/huggingface/text-embeddings-inference:cpu-1.5 --model-id $model
    export TEI_EMBEDDING_ENDPOINT="http://${ip_address}:${tei_endpoint}"
    tei_service_port=5034
    docker run -d --name="test-comps-embedding-tei-llama-index-server" -e LOGFLAG=True  -e http_proxy=$http_proxy -e https_proxy=$https_proxy -p ${tei_service_port}:6000 --ipc=host -e TEI_EMBEDDING_ENDPOINT=$TEI_EMBEDDING_ENDPOINT  opea/embedding-tei-llama-index:comps
    sleep 3m
}

function validate_service() {
    local INPUT_DATA="$1"

    tei_service_port=5034
    URL="http://${ip_address}:$tei_service_port/v1/embeddings"
    docker logs test-comps-embedding-tei-llama-index-server >> ${LOG_PATH}/embedding.log
    HTTP_STATUS=$(curl -s -o /dev/null -w "%{http_code}" -X POST -d "$INPUT_DATA" -H 'Content-Type: application/json' "$URL")
    if [ "$HTTP_STATUS" -eq 200 ]; then
        echo "[ embedding - llama_index ] HTTP status is 200. Checking content..."
        local CONTENT=$(curl -s -X POST -d "$INPUT_DATA" -H 'Content-Type: application/json' "$URL" | tee ${LOG_PATH}/embedding.log)

        if echo '"text":"What is Deep Learning?","embedding":\[' | grep -q "$EXPECTED_RESULT"; then
            echo "[ embedding - llama_index ] Content is as expected."
        else
            echo "[ embedding - llama_index ] Content does not match the expected result: $CONTENT"
            docker logs test-comps-embedding-tei-llama-index-server >> ${LOG_PATH}/embedding.log
            exit 1
        fi
    else
        echo "[ embedding - llama_index ] HTTP status is not 200. Received status was $HTTP_STATUS"
        docker logs test-comps-embedding-tei-llama-index-server >> ${LOG_PATH}/embedding.log
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
    cid=$(docker ps -aq --filter "name=test-comps-embedding-*")
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
