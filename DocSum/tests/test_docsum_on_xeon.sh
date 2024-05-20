#!/bin/bash
# Copyright (C) 2024 Intel Corporation
# SPDX-License-Identifier: Apache-2.0

set -x

WORKPATH=$(dirname "$PWD")
LOG_PATH="$WORKPATH/tests"
ip_name=$(echo $(hostname) | tr '[a-z]-' '[A-Z]_')_$(echo 'IP')
ip_address=$(eval echo '$'$ip_name)

function build_docker_images() {
    cd $WORKPATH
    git clone https://github.com/opea-project/GenAIComps.git
    cd GenAIComps

    docker build -t opea/gen-ai-comps:llm-docsum-server --build-arg https_proxy=$https_proxy --build-arg http_proxy=$http_proxy -f comps/llms/docsum/langchain/docker/Dockerfile .

    cd $WORKPATH/microservice/xeon
    docker build --no-cache -t opea/gen-ai-comps:docsum-megaservice-server --build-arg https_proxy=$https_proxy --build-arg http_proxy=$http_proxy -f docker/Dockerfile .

    cd $WORKPATH/ui
    docker build --no-cache -t opea/gen-ai-comps:docsum-ui-server --build-arg https_proxy=$https_proxy --build-arg http_proxy=$http_proxy -f docker/Dockerfile .

    docker images
}

function start_services() {
    cd $WORKPATH/microservice/xeon

    export LLM_MODEL_ID="Intel/neural-chat-7b-v3-3"
    export TGI_LLM_ENDPOINT="http://${ip_address}:8008"
    export HUGGINGFACEHUB_API_TOKEN=${HUGGINGFACEHUB_API_TOKEN}
    export MEGA_SERVICE_HOST_IP=${ip_address}
    export BACKEND_SERVICE_ENDPOINT="http://${ip_address}:8888/v1/docsum"

    # Start Docker Containers
    # TODO: Replace the container name with a test-specific name
    docker compose -f docker_compose.yaml up -d

    sleep 2m # Waits 2 minutes
}

function validate_microservices() {
    # Check if the microservices are running correctly.
    # TODO: Any results check required??
    curl http://${ip_address}:8008/generate \
        -X POST \
        -d '{"inputs":"What is Deep Learning?","parameters":{"max_new_tokens":17, "do_sample": true}}' \
        -H 'Content-Type: application/json' > ${LOG_PATH}/generate.log
    exit_code=$?
    if [ $exit_code -ne 0 ]; then
        echo "Microservice failed, please check the logs in artifacts!"
        docker logs tgi_service >> ${LOG_PATH}/generate.log
        exit 1
    fi
    sleep 5s

    curl http://${ip_address}:9000/v1/chat/docsum \
        -X POST \
        -d '{"query":"Text Embeddings Inference (TEI) is a toolkit for deploying and serving open source text embeddings and sequence classification models. TEI enables high-performance extraction for the most popular models, including FlagEmbedding, Ember, GTE and E5."}' \
        -H 'Content-Type: application/json' > ${LOG_PATH}/completions.log
    exit_code=$?
    if [ $exit_code -ne 0 ]; then
        echo "Microservice failed, please check the logs in artifacts!"
        docker logs llm-docsum-server >> ${LOG_PATH}/completions.log
        exit 1
    fi
    sleep 5s
}

function validate_megaservice() {
    # Curl the Mega Service
    curl http://${ip_address}:8888/v1/docsum -H "Content-Type: application/json" -d '{
        "model": "Intel/neural-chat-7b-v3-3",
        "messages": "Text Embeddings Inference (TEI) is a toolkit for deploying and serving open source text embeddings and sequence classification models. TEI enables high-performance extraction for the most popular models, including FlagEmbedding, Ember, GTE and E5."}' > ${LOG_PATH}/curl_megaservice.log

    echo "Checking response results, make sure the output is reasonable. "
    local status=false
    if [[ -f $LOG_PATH/curl_megaservice.log ]] && \
    [[ $(grep -c " flexible" $LOG_PATH/curl_megaservice.log) != 0 ]] && \
    [[ $(grep -c " tool" $LOG_PATH/curl_megaservice.log) != 0 ]] && \
    [[ $(grep -c "kit" $LOG_PATH/curl_megaservice.log) != 0 ]]; then
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
    cd $WORKPATH/microservice/xeon
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
