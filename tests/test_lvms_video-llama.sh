#!/bin/bash
# Copyright (C) 2024 Intel Corporation
# SPDX-License-Identifier: Apache-2.0

set -xe

WORKPATH=$(dirname "$PWD")
ip_address=$(hostname -I | awk '{print $1}')

function build_docker_images() {
    cd $WORKPATH
    echo $(pwd)
    docker build --no-cache -t opea/video-llama-lvm-server:latest --build-arg https_proxy=$https_proxy --build-arg http_proxy=$http_proxy -f comps/lvms/video-llama/server/docker/Dockerfile .
    if $? ; then
        echo "opea/video-llama-lvm-server built fail"
        exit 1
    else
        echo "opea/video-llama-lvm-server built successful"
    fi
    docker build --no-cache -t opea/lvm-video-llama:latest --build-arg https_proxy=$https_proxy --build-arg http_proxy=$http_proxy  -f comps/lvms/video-llama/Dockerfile .
    if $? ; then
        echo "opea/lvm-video-llama built fail"
        exit 1
    else
        echo "opea/lvm-video-llama built successful"
    fi

}

function start_service() {
    cd $WORKPATH
    unset http_proxy
    export LVM_ENDPOINT=http://$ip_address:5030

    docker run -d --name="test-comps-lvm-video-llama" -p 5030:9009 \
        --ipc=host \
        -e http_proxy=$http_proxy \
        -e https_proxy=$https_proxy \
        -e no_proxy=$no_proxy \
        -e llm_download="True" \
        -v "/home/$USER/.cache:/home/user/.cache" \
        -v video-llama-model:/home/user/model \
        opea/video-llama-lvm-server:latest

    docker run -d --name="test-comps-lvm" -p 5031:9000 \
        --ipc=host \
        -e http_proxy=$http_proxy \
        -e https_proxy=$https_proxy \
        -e no_proxy=$no_proxy \
        -e LVM_ENDPOINT=$LVM_ENDPOINT \
        opea/lvm-video-llama:latest

    echo "Waiting for the LVM service to start"
    until docker logs test-comps-lvm 2>&1 | grep -q "Uvicorn running on"; do
    sleep 5
    done

    echo "Waiting for the Video-Llama service to start, downloading model..."
    until docker logs test-comps-lvm-video-llama 2>&1 | grep -q "Uvicorn running on"; do
    sleep 5m
    done
}

function validate_microservice() {

    result=$(http_proxy="" curl http://localhost:5031/v1/lvm -X POST -d '{"video_url":"silence_girl.mp4","chunk_start": 0,"chunk_duration": 7,"prompt":"What is the person doing?","max_new_tokens": 50}' -H 'Content-Type: application/json')

    if [[ $result == *"silence"* ]]; then
        echo "Result correct."
    else
        echo "Result wrong."
        exit 1
    fi
}

function stop_docker() {
    cid=$(docker ps -aq --filter "name=test-comps-lvm*")
    if [[ ! -z "$cid" ]]; then docker stop $cid && docker rm $cid && sleep 1s; fi
    if docker volume ls | grep -q video-llama-model; then docker volume rm video-llama-model; fi

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
