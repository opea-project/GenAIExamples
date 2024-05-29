#!/bin/bash
# Copyright (C) 2024 Intel Corporation
# SPDX-License-Identifier: Apache-2.0

set -xe

WORKPATH=$(dirname "$PWD")
ip_address=$(hostname -I | awk '{print $1}')

function build_docker_images() {
    cd $WORKPATH
    docker build --no-cache -t opea/llm-tgi:comps -f comps/llms/text-generation/tgi/Dockerfile .
}

function start_service() {
    tgi_endpoint_port=5004
    export your_hf_llm_model="Intel/neural-chat-7b-v3-3"
    # Remember to set HUGGINGFACEHUB_API_TOKEN before invoking this test!
    export HUGGINGFACEHUB_API_TOKEN=${HUGGINGFACEHUB_API_TOKEN}
    docker run -d --name="test-comps-llm-tgi-endpoint" -p $tgi_endpoint_port:80 -v ./data:/data --shm-size 1g ghcr.io/huggingface/text-generation-inference:1.4 --model-id ${your_hf_llm_model}
    export TGI_LLM_ENDPOINT="http://${ip_address}:${tgi_endpoint_port}"

    tei_service_port=5005
    unset http_proxy
    docker run -d --name="test-comps-llm-tgi-server" -p ${tei_service_port}:9000 --ipc=host -e http_proxy=$http_proxy -e https_proxy=$https_proxy -e TGI_LLM_ENDPOINT=$TGI_LLM_ENDPOINT -e HUGGINGFACEHUB_API_TOKEN=$HUGGINGFACEHUB_API_TOKEN opea/llm-tgi:comps

    # check whether tgi is fully ready
    n=0
    until [[ "$n" -ge 100 ]] || [[ $ready == true ]]; do
        docker logs test-comps-llm-tgi-endpoint > test-comps-llm-tgi-endpoint.log
        n=$((n+1))
        if grep -q Connected test-comps-llm-tgi-endpoint.log; then
            break
        fi
        sleep 5s
    done
    # rm -f test-comps-llm-tgi-endpoint.log
    sleep 5s
}

function validate_microservice() {
    tei_service_port=5005
    http_proxy="" curl http://${ip_address}:${tei_service_port}/v1/chat/completions \
        -X POST \
        -d '{"query":"What is Deep Learning?"}' \
        -H 'Content-Type: application/json'
}

function stop_docker() {
    cid=$(docker ps -aq --filter "name=test-comps-llm-*")
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
