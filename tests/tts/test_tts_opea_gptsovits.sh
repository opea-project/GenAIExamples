#!/bin/bash
# Copyright (C) 2024 Intel Corporation
# SPDX-License-Identifier: Apache-2.0

set -x

WORKPATH=$(dirname "$PWD")
ip_address=$(hostname -I | awk '{print $1}')

function build_docker_images() {
    cd $WORKPATH
    echo $(pwd)
    docker build --no-cache --build-arg https_proxy=$https_proxy --build-arg http_proxy=$http_proxy -t opea/gpt-sovits:comps -f comps/tts/src/integrations/dependency/gpt-sovits/Dockerfile .
    if [ $? -ne 0 ]; then
        echo "opea/gpt-sovits built fail"
        exit 1
    else
        echo "opea/gpt-sovits built successful"
    fi

    docker build --no-cache --build-arg https_proxy=$https_proxy --build-arg http_proxy=$http_proxy -t opea/tts:comps -f comps/tts/src/Dockerfile .
    if [ $? -ne 0 ]; then
        echo "opea/tts built fail"
        exit 1
    else
        echo "opea/tts built successful"
    fi

}

function start_service() {
    unset http_proxy
    docker run -d --name="test-comps-tts-gpt-sovits" -e http_proxy=$http_proxy -e https_proxy=$https_proxy -p 9880:9880 --ipc=host opea/gpt-sovits:comps
    sleep 2m
    docker run -d --name="test-comps-tts" -e TTS_ENDPOINT=http://$ip_address:9880 -e http_proxy=$http_proxy -e https_proxy=$https_proxy -e TTS_COMPONENT_NAME="OPEA_GPTSOVITS_TTS" -p 5016:9088 --ipc=host opea/tts:comps
    sleep 15
}

function validate_microservice() {
    http_proxy="" curl localhost:5016/v1/audio/speech -XPOST -d '{"input":"Hello, who are you? 你好。"}' -H 'Content-Type: application/json' --output speech.mp3

    if [[ $(file speech.mp3) == *"RIFF"* ]]; then
        echo "Result correct."
    else
        echo "Result wrong."
        docker logs test-comps-tts-gpt-sovits
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
