#!/bin/bash
# Copyright (C) 2024 Intel Corporation
# SPDX-License-Identifier: Apache-2.0

set -x

WORKPATH=$(dirname "$PWD")
ip_address=$(hostname -I | awk '{print $1}')

function build_docker_images() {
    cd $WORKPATH
    echo $(pwd)
    docker build --no-cache -t opea/speecht5:comps -f comps/tts/speecht5/dependency/Dockerfile .
    if [ $? -ne 0 ]; then
        echo "opea/speecht5 built fail"
        exit 1
    else
        echo "opea/speecht5 built successful"
    fi
    docker build --no-cache -t opea/tts:comps -f comps/tts/speecht5/Dockerfile .
    if [ $? -ne 0 ]; then
        echo "opea/tts built fail"
        exit 1
    else
        echo "opea/tts built successful"
    fi
}

function start_service() {
    unset http_proxy
    docker run -d --name="test-comps-tts-speecht5" -e http_proxy=$http_proxy -e https_proxy=$https_proxy -p 5017:7055 --ipc=host opea/speecht5:comps
    docker run -d --name="test-comps-tts" -e TTS_ENDPOINT=http://$ip_address:5017 -e http_proxy=$http_proxy -e https_proxy=$https_proxy -p 5016:9088 --ipc=host opea/tts:comps
    sleep 3m
}

function validate_microservice() {
    result=$(http_proxy="" curl http://localhost:5016/v1/audio/speech -XPOST -d '{"text": "Who are you?"}' -H 'Content-Type: application/json')
    if [[ $result == *"Ukl"* ]]; then
        echo "Result correct."
    else
        echo "Result wrong."
        docker logs test-comps-tts-speecht5
        docker logs test-comps-tts
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
