#!/bin/bash
# Copyright (C) 2024 Intel Corporation
# SPDX-License-Identifier: Apache-2.0

set -xe

WORKPATH=$(dirname "$PWD")
ip_address=$(hostname -I | awk '{print $1}')

function build_docker_images() {
    cd $WORKPATH
    echo $(pwd)
    docker build -t opea/speecht5:latest -f comps/tts/speecht5/Dockerfile .
    docker build -t opea/tts:latest -f comps/tts/Dockerfile .
}

function start_service() {
    unset http_proxy
    docker run -d --name="test-comps-tts-speecht5" -e http_proxy=$http_proxy -e https_proxy=$https_proxy -p 7055:7055 --ipc=host opea/speecht5:latest
    docker run -d --name="test-comps-tts" -e TTS_ENDPOINT=http://$ip_address:7055 -e http_proxy=$http_proxy -e https_proxy=$https_proxy -p 9088:9088 --ipc=host opea/tts:latest
    sleep 3m
}

function validate_microservice() {
    result=$(http_proxy="" curl http://localhost:9088/v1/audio/speech -XPOST -d '{"text": "Who are you?"}' -H 'Content-Type: application/json')
    if [[ $result == *"AAA"* ]]; then
        echo "Result correct."
    else
        echo "Result wrong."
        exit 1
    fi

}

function stop_docker() {
    cid=$(docker ps -aq --filter "name=test-comps-tts*")
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
