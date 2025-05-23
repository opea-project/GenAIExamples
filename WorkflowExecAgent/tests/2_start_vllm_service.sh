#!/bin/bash
# Copyright (C) 2024 Intel Corporation
# SPDX-License-Identifier: Apache-2.0

set -e

WORKPATH=$(dirname "$PWD")
LOG_PATH="$WORKPATH/tests"
vllm_port=${vllm_port}
[[ -z "$vllm_port" ]] && vllm_port=8084
model=mistralai/Mistral-7B-Instruct-v0.3
export WORKDIR=$WORKPATH/../../
export HF_TOKEN=${HUGGINGFACEHUB_API_TOKEN}

function build_vllm_docker_image() {
    echo "Building the vllm docker images"
    cd $WORKPATH
    echo $WORKPATH
    if [ ! -d "./vllm" ]; then
        git clone https://github.com/vllm-project/vllm.git
        cd vllm
        VLLM_VER=v0.9.0
        echo "Check out vLLM tag ${VLLM_VER}"
        git checkout ${VLLM_VER} &> /dev/null
        git rev-parse HEAD
    else
        cd ./vllm
    fi
    docker build -f Dockerfile.cpu -t vllm-cpu-env --shm-size=100g .
    if [ $? -ne 0 ]; then
        echo "opea/vllm:cpu failed"
        exit 1
    else
        echo "opea/vllm:cpu successful"
    fi
}

function start_vllm_service() {
    echo "start vllm service"
    docker run -d -p ${vllm_port}:${vllm_port} --rm --network=host --name test-comps-vllm-service -v ~/.cache/huggingface:/root/.cache/huggingface -v ${WORKPATH}/tests/tool_chat_template_mistral_custom.jinja:/root/tool_chat_template_mistral_custom.jinja -e HF_TOKEN=$HF_TOKEN -e http_proxy=$http_proxy -e https_proxy=$https_proxy -it vllm-cpu-env --model ${model} --port ${vllm_port} --chat-template /root/tool_chat_template_mistral_custom.jinja --enable-auto-tool-choice --tool-call-parser mistral
    echo ${LOG_PATH}/vllm-service.log
    sleep 5s
    echo "Waiting vllm ready"
    n=0
    until [[ "$n" -ge 100 ]] || [[ $ready == true ]]; do
        docker logs test-comps-vllm-service &> ${LOG_PATH}/vllm-service.log
        n=$((n+1))
        if grep -q "Uvicorn running on" ${LOG_PATH}/vllm-service.log; then
            break
        fi
        if grep -q "No such container" ${LOG_PATH}/vllm-service.log; then
            echo "container test-comps-vllm-service not found"
            exit 1
        fi
        sleep 5s
    done
    sleep 5s
    echo "Service started successfully"
}

function main() {
    echo "==================== Build vllm docker image ===================="
    build_vllm_docker_image
    echo "==================== Build vllm docker image completed ===================="

    echo "==================== Start vllm docker service ===================="
    start_vllm_service
    echo "==================== Start vllm docker service completed ===================="
}

main
