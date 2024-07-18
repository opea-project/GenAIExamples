#!/bin/bash
# Copyright (C) 2024 Intel Corporation
# SPDX-License-Identifier: Apache-2.0

set -xe

WORKPATH=$(dirname "$PWD")
ip_address=$(hostname -I | awk '{print $1}')

function build_docker_images() {
    echo "Start building docker images for microservice"
    cd $WORKPATH
    docker pull ghcr.io/huggingface/tgi-gaudi:2.0.1
    docker build --no-cache -t opea/guardrails-tgi:latest --build-arg https_proxy=$https_proxy --build-arg http_proxy=$http_proxy -f comps/guardrails/langchain/docker/Dockerfile .
    echo "Docker images built"
}

function start_service() {
    echo "Starting microservice"
    export model_id="meta-llama/Meta-Llama-Guard-2-8B"
    export SAFETY_GUARD_ENDPOINT=http://${ip_address}:8088

    docker run -d --name="test-guardrails-langchain-tgi-server" -p 8088:80 --runtime=habana -e HF_TOKEN=$HF_TOKEN -e HABANA_VISIBLE_DEVICES=all -e OMPI_MCA_btl_vader_single_copy_mechanism=none --cap-add=sys_nice --ipc=host -e HTTPS_PROXY=$https_proxy -e HTTP_PROXY=$https_proxy ghcr.io/huggingface/tgi-gaudi:2.0.1 --model-id $model_id --max-input-length 1024 --max-total-tokens 2048
    sleep 4m
    docker run -d --name="test-guardrails-langchain-service" -p 9090:9090 --ipc=host -e http_proxy=$http_proxy -e https_proxy=$https_proxy -e no_proxy=$no_proxy -e SAFETY_GUARD_ENDPOINT=$SAFETY_GUARD_ENDPOINT -e HUGGINGFACEHUB_API_TOKEN=$HF_TOKEN opea/guardrails-tgi:latest
    sleep 10s

    echo "Microservice started"
}

function validate_microservice() {
    echo "Validate microservice started"
    echo "test 1 - violated policies"
    docker logs test-guardrails-langchain-tgi-server
    docker logs test-guardrails-langchain-service
    result=$(http_proxy= curl http://localhost:9090/v1/guardrails  -X POST   -d '{"text":"How do you buy a tiger in the US?","parameters":{"max_new_tokens":32}}'   -H 'Content-Type: application/json')
    if [[ $result == *"Violated"* ]]; then
        echo "Result correct."
    else
        echo "Result wrong."
        exit 1
    fi
    echo "test 2 - safe"
    result=$(http_proxy= curl http://localhost:9090/v1/guardrails  -X POST   -d '{"text":"How do you buy a car in the US?","parameters":{"max_new_tokens":32}}'   -H 'Content-Type: application/json')
        if [[ $result == *"car"* ]]; then
        echo "Result correct."
    else
        echo "Result wrong."
        exit 1
    fi

}

function stop_docker() {
    cid=$(docker ps -aq --filter "name=test-guardrails-langchain*")
    echo "Shutdown legacy containers "$cid
    if [[ ! -z "$cid" ]]; then docker stop $cid && docker rm $cid && sleep 1s; fi
}

function main() {

    stop_docker

    build_docker_images
    start_service

    validate_microservice

    stop_docker
    echo "cleanup container images and volumes"
    echo y | docker system prune 2>&1 > /dev/null

}

main
