#!/bin/bash
# Copyright (C) 2024 Intel Corporation
# SPDX-License-Identifier: Apache-2.0

set -x

WORKPATH=$(dirname "$PWD")
ip_address=$(hostname -I | awk '{print $1}')

function build_docker_images() {
    cd $WORKPATH
    docker build --no-cache --build-arg https_proxy=$https_proxy --build-arg http_proxy=$http_proxy -t opea/llm-tgi:comps -f comps/llms/text-generation/tgi/Dockerfile .
    if [ $? -ne 0 ]; then
        echo "opea/llm-tgi built fail"
        exit 1
    else
        echo "opea/llm-tgi built successful"
    fi
}

function start_service() {
    tgi_endpoint_port=5004
    export your_hf_llm_model=$1
    # Remember to set HF_TOKEN before invoking this test!
    export HF_TOKEN=${HF_TOKEN}
    docker run -d --name="test-comps-llm-tgi-endpoint" -p $tgi_endpoint_port:80 -v ./data:/data --shm-size 1g -e HF_TOKEN=${HF_TOKEN} ghcr.io/huggingface/text-generation-inference:2.1.0 --model-id ${your_hf_llm_model} --max-input-tokens 1024 --max-total-tokens 2048
    export TGI_LLM_ENDPOINT="http://${ip_address}:${tgi_endpoint_port}"

    tei_service_port=5005
    unset http_proxy
    docker run -d --name="test-comps-llm-tgi-server" -p ${tei_service_port}:9000 --ipc=host -e http_proxy=$http_proxy -e https_proxy=$https_proxy -e TGI_LLM_ENDPOINT=$TGI_LLM_ENDPOINT -e HUGGINGFACEHUB_API_TOKEN=$HF_TOKEN opea/llm-tgi:comps

    # check whether tgi is fully ready
    n=0
    until [[ "$n" -ge 100 ]] || [[ $ready == true ]]; do
        docker logs test-comps-llm-tgi-endpoint > ${WORKPATH}/tests/test-comps-llm-tgi-endpoint.log
        n=$((n+1))
        if grep -q Connected ${WORKPATH}/tests/test-comps-llm-tgi-endpoint.log; then
            break
        fi
        sleep 5s
    done
    sleep 5s
}

function validate_microservice() {
    tei_service_port=5005
    result=$(http_proxy="" curl http://${ip_address}:${tei_service_port}/v1/chat/completions \
        -X POST \
        -d '{"query":"What is Deep Learning?", "max_new_tokens": 128}' \
        -H 'Content-Type: application/json')
    if [[ $result == *"DONE"* ]]; then
        echo "Result correct."
    else
        echo "Result wrong. Received was $result"
        docker logs test-comps-llm-tgi-endpoint
        docker logs test-comps-llm-tgi-server
        exit 1
    fi
}

function stop_docker() {
    cid=$(docker ps -aq --filter "name=test-comps-llm-*")
    if [[ ! -z "$cid" ]]; then docker stop $cid && docker rm $cid && sleep 1s; fi
}

function main() {

    stop_docker
    build_docker_images

    llm_models=(
    Intel/neural-chat-7b-v3-3
    meta-llama/Llama-2-7b-chat-hf
    meta-llama/Meta-Llama-3-8B-Instruct
    microsoft/Phi-3-mini-4k-instruct
    )
    for model in "${llm_models[@]}"; do
      start_service "${model}"
      validate_microservice
      stop_docker
    done

    echo y | docker system prune

}

main
