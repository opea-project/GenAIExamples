#!/bin/bash
# Copyright (C) 2024 Intel Corporation
# SPDX-License-Identifier: Apache-2.0

set -x

WORKPATH=$(dirname "$PWD")
ip_address=$(hostname -I | awk '{print $1}')

function build_docker_images() {
    cd $WORKPATH
    echo $(pwd)
    docker build --no-cache --build-arg https_proxy=$https_proxy --build-arg http_proxy=$http_proxy -t opea/speecht5-gaudi:comps -f comps/tts/src/integrations/dependency/speecht5/Dockerfile.intel_hpu .
    if [ $? -ne 0 ]; then
        echo "opea/speecht5-gaudi built fail"
        exit 1
    else
        echo "opea/speecht5-gaudi built successful"
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
    docker run -d --name="test-comps-tts-speecht5" --runtime=habana -e HABANA_VISIBLE_DEVICES=all -e OMPI_MCA_btl_vader_single_copy_mechanism=none --cap-add=sys_nice -e http_proxy=$http_proxy -e https_proxy=$https_proxy -p 5017:7055 --ipc=host opea/speecht5-gaudi:comps
    sleep 3m
    docker run -d --name="test-comps-tts" -e TTS_ENDPOINT=http://$ip_address:5017 -e http_proxy=$http_proxy -e https_proxy=$https_proxy -p 5016:9088 --ipc=host opea/tts:comps
    sleep 15
}

function validate_microservice() {
    http_proxy="" curl localhost:5016/v1/audio/speech -XPOST -d '{"input":"Hello, who are you?"}' -H 'Content-Type: application/json' --output speech.mp3

    if [[ $(file speech.mp3) == *"RIFF"* ]]; then
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
