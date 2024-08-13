#!/bin/bash
# Copyright (C) 2024 Intel Corporation
# SPDX-License-Identifier: Apache-2.0

set -x

WORKPATH=$(dirname "$PWD")
ip_address=$(hostname -I | awk '{print $1}')

function build_docker_images() {
    cd $WORKPATH
    echo $(pwd)
    docker build --no-cache -t opea/whisper:comps -f comps/asr/whisper/Dockerfile .
    docker build --no-cache -t opea/asr:comps -f comps/asr/Dockerfile .
}

function start_service() {
    unset http_proxy
    docker run -d --name="test-comps-asr-whisper" -e http_proxy=$http_proxy -e https_proxy=$https_proxy -p 7066:7066 --ipc=host opea/whisper:comps
    docker run -d --name="test-comps-asr" -e ASR_ENDPOINT=http://$ip_address:7066 -e http_proxy=$http_proxy -e https_proxy=$https_proxy -p 9089:9099 --ipc=host opea/asr:comps
    sleep 3m
}

function validate_microservice() {
    result=$(http_proxy="" curl http://localhost:9089/v1/audio/transcriptions -XPOST -d '{"byte_str": "UklGRigAAABXQVZFZm10IBIAAAABAAEARKwAAIhYAQACABAAAABkYXRhAgAAAAEA"}' -H 'Content-Type: application/json')
    if [[ $result == *"you"* ]]; then
        echo "Result correct."
    else
        echo "Result wrong."
        docker logs test-comps-asr-whisper
        docker logs test-comps-asr
        exit 1
    fi

}

function stop_docker() {
    cid=$(docker ps -aq --filter "name=test-comps-asr*")
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
