#!/bin/bash
# Copyright (C) 2024 Intel Corporation
# SPDX-License-Identifier: Apache-2.0

set -x

WORKPATH=$(dirname "$PWD")
ip_address=$(hostname -I | awk '{print $1}')

function build_docker_images() {
    cd $WORKPATH
    echo $(pwd)
    docker build -t opea/wav2lip:comps -f comps/third_parties/wav2lip/src/Dockerfile .
    if [ $? -ne 0 ]; then
        echo "opea/wav2lip built fail"
        exit 1
    else
        echo "opea/wav2lip built successful"
    fi
    docker build --no-cache -t opea/animation:comps -f comps/animation/src/Dockerfile .
    if [ $? -ne 0 ]; then
        echo "opea/animation built fail"
        exit 1
    else
        echo "opea/animation built successful"
    fi
}

function start_service() {
    unset http_proxy
    # Set env vars
    export ip_address=$(hostname -I | awk '{print $1}')
    export DEVICE="cpu"
    export WAV2LIP_PORT=7860
    export ANIMATION_PORT=9066
    export INFERENCE_MODE='wav2lip+gfpgan'
    export CHECKPOINT_PATH='/usr/local/lib/python3.11/site-packages/Wav2Lip/checkpoints/wav2lip_gan.pth'
    export FACE="/home/user/comps/animation/src/assets/img/avatar1.jpg"
    export AUDIO='None'
    export FACESIZE=96
    export OUTFILE="/home/user/comps/animation/src/assets/outputs/result.mp4"
    export GFPGAN_MODEL_VERSION=1.4 # latest version, can roll back to v1.3 if needed
    export UPSCALE_FACTOR=1
    export FPS=10

    docker run -d --name="test-comps-animation-wav2lip" -v $WORKPATH/comps/animation/src/assets:/home/user/comps/animation/src/assets -e http_proxy=$http_proxy -e https_proxy=$https_proxy -e DEVICE=$DEVICE -e INFERENCE_MODE=$INFERENCE_MODE -e CHECKPOINT_PATH=$CHECKPOINT_PATH -e FACE=$FACE -e AUDIO=$AUDIO -e FACESIZE=$FACESIZE -e OUTFILE=$OUTFILE -e GFPGAN_MODEL_VERSION=$GFPGAN_MODEL_VERSION -e UPSCALE_FACTOR=$UPSCALE_FACTOR -e FPS=$FPS -e WAV2LIP_PORT=$WAV2LIP_PORT -p 7860:7860 --ipc=host opea/wav2lip:comps
    docker run -d --name="test-comps-animation" -v $WORKPATH/comps/animation/src/assets:/home/user/comps/animation/src/assets -e WAV2LIP_ENDPOINT=http://$ip_address:7860 -e http_proxy=$http_proxy -e https_proxy=$https_proxy -p 9066:9066 --ipc=host opea/animation:comps
    sleep 3m
}

function validate_microservice() {
    cd $WORKPATH
    result=$(http_proxy="" curl http://localhost:9066/v1/animation -X POST -H "Content-Type: application/json" -d @comps/animation/src/assets/audio/sample_question.json)
    if [[ $result == *"result.mp4"* ]]; then
        echo "Result correct."
    else
        echo "Result wrong."
        docker logs test-comps-animation-wav2lip
        docker logs test-comps-animation
        exit 1
    fi
}

function stop_docker() {
    cid=$(docker ps -aq --filter "name=test-comps-animation*")
    if [[ ! -z "$cid" ]]; then docker stop $cid && docker rm $cid && sleep 1s; fi
}

function main() {
    stop_docker

    build_docker_images

    start_service

    validate_microservice

    stop_docker

    echo y | docker builder prune --all
    echo y | docker image prune

}

main
