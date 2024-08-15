#!/bin/bash
# Copyright (C) 2024 Intel Corporation
# SPDX-License-Identifier: Apache-2.0

set -x

WORKPATH=$(dirname "$PWD")
ip_address=$(hostname -I | awk '{print $1}')

function build_docker_images() {
    echo "Start building docker images for microservice"
    cd $WORKPATH
    docker build --no-cache -t opea/guardrails-pii-detection:comps --build-arg https_proxy=$https_proxy --build-arg http_proxy=$http_proxy -f comps/guardrails/pii_detection/docker/Dockerfile .
    if $? ; then
        echo "opea/guardrails-pii-detection built fail"
        exit 1
    else
        echo "opea/guardrails-pii-detection built successful"
    fi
}

function start_service() {
    echo "Starting microservice"
    docker run -d --runtime=runc --name="test-comps-guardrails-pii-detection-endpoint" -p 6357:6357 --ipc=host -e http_proxy=$http_proxy -e https_proxy=$https_proxy opea/guardrails-pii-detection:comps
    sleep 5
    echo "Microservice started"
}

function validate_microservice() {
    echo "Validate microservice started"
    export PATH="${HOME}/miniforge3/bin:$PATH"
    source activate
    echo "test 1 - single task - ner"
    result=$(python comps/guardrails/pii_detection/test.py --test_text --batch_size 1 --ip_addr $ip_address --strategy ner)
    if [[ $result == *"An error occurred"* ]]; then
        echo "Result wrong. Received was $result"
        docker logs test-comps-guardrails-pii-detection-endpoint
        exit 1
    else
        echo "Result correct."
    fi
    echo "test 2 - 20 tasks in parallel - ner"
    result=$(python comps/guardrails/pii_detection/test.py --test_text --batch_size 20 --ip_addr $ip_address --strategy ner)
    if [[ $result == *"An error occurred"* ]]; then
        echo "Result wrong. Received was $result"
        docker logs test-comps-guardrails-pii-detection-endpoint
        exit 1
    else
        echo "Result correct."
    fi
    echo "test 3 - single task - ml"
    result=$(python comps/guardrails/pii_detection/test.py --test_text --batch_size 1 --ip_addr $ip_address --strategy ml)
    if [[ $result == *"An error occurred"* ]]; then
        echo "Result wrong. Received was $result"
        docker logs test-comps-guardrails-pii-detection-endpoint
        exit 1
    else
        echo "Result correct."
    fi
    echo "test 4 - 20 tasks in parallel - ml"
    result=$(python comps/guardrails/pii_detection/test.py --test_text --batch_size 20 --ip_addr $ip_address --strategy ml)
    if [[ $result == *"An error occurred"* ]]; then
        echo "Result wrong. Received was $result"
        docker logs test-comps-guardrails-pii-detection-endpoint
        exit 1
    else
        echo "Result correct."
    fi
    echo "Validate microservice completed"
}

function stop_docker() {
    cid=$(docker ps -aq --filter "name=test-comps-guardrails-pii-detection-endpoint")
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
