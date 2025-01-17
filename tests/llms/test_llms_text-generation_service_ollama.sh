#!/bin/bash
# Copyright (C) 2024 Intel Corporation
# SPDX-License-Identifier: Apache-2.0

set -x

WORKPATH=$(dirname "$PWD")
LOG_PATH="$WORKPATH/tests"
ip_address=$(hostname -I | awk '{print $1}')
ollama_endpoint_port=11435
llm_port=9000

function build_docker_images() {
    cd $WORKPATH
    docker build --no-cache --build-arg https_proxy=$https_proxy --build-arg http_proxy=$http_proxy -t opea/llm:comps -f comps/llms/src/text-generation/Dockerfile .
    if [ $? -ne 0 ]; then
        echo "opea/llm built fail"
        exit 1
    else
        echo "opea/llm built successful"
    fi
}

function start_service() {
    export llm_model=$1
    docker run -d --name="test-comps-llm-ollama-endpoint" -e https_proxy=$https_proxy -p $ollama_endpoint_port:11434 ollama/ollama
    export LLM_ENDPOINT="http://${ip_address}:${ollama_endpoint_port}"

    sleep 5s
    docker exec test-comps-llm-ollama-endpoint ollama pull $llm_model
    sleep 20s

    unset http_proxy
    docker run -d --name="test-comps-llm-ollama-server" -p $llm_port:9000 --ipc=host -e LOGFLAG=True -e http_proxy=$http_proxy -e https_proxy=$https_proxy -e LLM_ENDPOINT=$LLM_ENDPOINT -e LLM_MODEL_ID=$llm_model opea/llm:comps
    sleep 20s
}

function validate_microservice() {
    result=$(http_proxy="" curl http://${ip_address}:${llm_port}/v1/chat/completions \
        -X POST \
        -d '{"messages": [{"role": "user", "content": "What is Deep Learning?"}]}' \
        -H 'Content-Type: application/json')
    if [[ $result == *"content"* ]]; then
        echo "Result correct."
    else
        echo "Result wrong. Received was $result"
        docker logs test-comps-llm-ollama-endpoint >> ${LOG_PATH}/llm-ollama.log
        docker logs test-comps-llm-ollama-server >> ${LOG_PATH}/llm-server.log
        exit 1
    fi
}

function stop_docker() {
    cid=$(docker ps -aq --filter "name=test-comps-llm-ollama*")
    if [[ ! -z "$cid" ]]; then docker stop $cid && docker rm $cid && sleep 1s; fi
}

function main() {

    stop_docker
    build_docker_images

    pip install --no-cache-dir openai

    llm_models=(
    llama3.2:1b
    )
    for model in "${llm_models[@]}"; do
      start_service "${model}"
      validate_microservice
      stop_docker
    done

    echo y | docker system prune

}

main
