#!/bin/bash
# Copyright (C) 2024 Intel Corporation
# SPDX-License-Identifier: Apache-2.0

set -x

WORKPATH=$(dirname "$PWD")
ip_address=$(hostname -I | awk '{print $1}')

function build_docker_images() {
    cd $WORKPATH
    echo $(pwd)
    docker build --no-cache --build-arg https_proxy=$https_proxy --build-arg http_proxy=$http_proxy -t opea/gpt-sovits:comps -f comps/tts/gpt-sovits/Dockerfile .
    if [ $? -ne 0 ]; then
        echo "opea/gpt-sovits built fail"
        exit 1
    else
        echo "opea/gpt-sovits built successful"
    fi
}

function start_service() {
    unset http_proxy
    docker run -d --name="test-comps-gpt-sovits" -e http_proxy=$http_proxy -e https_proxy=$https_proxy -p 9880:9880 --ipc=host opea/gpt-sovits:comps
    sleep 2m
}

function validate_microservice() {
    http_proxy="" curl http://localhost:9880/v1/audio/speech -XPOST -d '{"input":"你好呀，你是谁. Hello, who are you?"}' -H 'Content-Type: application/json' --output speech.mp3
    file_size=$(stat --format="%s" speech.mp3)
    if [[ $file_size -gt 0 ]]; then
        echo "Result correct."
    else
        echo "Result wrong."
        docker logs test-comps-gpt-sovits
        exit 1
    fi
}

function stop_docker() {
    cid=$(docker ps -aq --filter "name=test-comps-gpt-sovits*")
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
