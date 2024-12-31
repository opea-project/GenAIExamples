#!/bin/bash
# Copyright (C) 2024 Intel Corporation
# SPDX-License-Identifier: Apache-2.0

set -x

WORKPATH=$(dirname "$PWD")
ip_address=$(hostname -I | awk '{print $1}')

function build_docker_images() {
    cd $WORKPATH
    echo $(pwd)
    docker build --no-cache -t opea/whisper-gaudi:comps --build-arg https_proxy=$https_proxy --build-arg http_proxy=$http_proxy -f comps/asr/src/integrations/dependency/whisper/Dockerfile.intel_hpu .

    if [ $? -ne 0 ]; then
        echo "opea/whisper-gaudi built fail"
        exit 1
    else
        echo "opea/whisper-gaudi built successful"
    fi

    docker build --no-cache -t opea/asr:comps --build-arg https_proxy=$https_proxy --build-arg http_proxy=$http_proxy -f comps/asr/src/Dockerfile .

    if [ $? -ne 0 ]; then
        echo "opea/asr built fail"
        exit 1
    else
        echo "opea/asr built successful"
    fi
}

function start_service() {
    unset http_proxy
    docker run -d --name="test-comps-asr-whisper-gaudi" --runtime=habana -e HABANA_VISIBLE_DEVICES=all -e OMPI_MCA_btl_vader_single_copy_mechanism=none --cap-add=sys_nice -e http_proxy=$http_proxy -e https_proxy=$https_proxy -e no_proxy=$no_proxy -p 7067:7066 --ipc=host opea/whisper-gaudi:comps
    sleep 3m
    docker run -d --name="test-comps-asr" -e ASR_ENDPOINT=http://$ip_address:7067 -e http_proxy=$http_proxy -e https_proxy=$https_proxy -e no_proxy=$no_proxy -p 9089:9099 --ipc=host opea/asr:comps
    sleep 15
}

function validate_microservice() {
    wget https://github.com/intel/intel-extension-for-transformers/raw/main/intel_extension_for_transformers/neural_chat/assets/audio/sample.wav
    result=$(http_proxy="" curl http://localhost:9089/v1/audio/transcriptions -H "Content-Type: multipart/form-data" -F file="@./sample.wav" -F model="openai/whisper-small")
    if [[ $result == *"who is"* ]]; then
        echo "Result correct."
    else
        echo "Result wrong."
        docker logs test-comps-asr-whisper-gaudi
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
