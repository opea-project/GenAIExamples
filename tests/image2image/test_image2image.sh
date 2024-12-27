#!/bin/bash
# Copyright (C) 2024 Intel Corporation
# SPDX-License-Identifier: Apache-2.0

set -x

WORKPATH=$(dirname "$PWD")
ip_address=$(hostname -I | awk '{print $1}')

function build_docker_images() {
    cd $WORKPATH
    echo $(pwd)
    docker build --no-cache -t opea/image2image:latest -f comps/image2image/src/Dockerfile .
    if [ $? -ne 0 ]; then
        echo "opea/image2image built fail"
        exit 1
    else
        echo "opea/image2image built successful"
    fi
}

function start_service() {
    unset http_proxy
    docker run -d --name="test-comps-image2image" -e http_proxy=$http_proxy -e https_proxy=$https_proxy -e MODEL=stabilityai/stable-diffusion-xl-refiner-1.0 -p 9389:9389 --ipc=host opea/image2image:latest
    sleep 30s
}

function validate_microservice() {
    result=$(http_proxy="" curl http://localhost:9389/v1/image2image -XPOST -d '{"image": "https://huggingface.co/datasets/patrickvonplaten/images/resolve/main/aa_xl/000000009.png", "prompt":"a photo of an astronaut riding a horse on mars", "num_images_per_prompt":1}' -H 'Content-Type: application/json')
    if [[ $result == *"images"* ]]; then
        echo "Result correct."
    else
        echo "Result wrong."
        docker logs test-comps-image2image
        exit 1
    fi

}

function stop_docker() {
    cid=$(docker ps -aq --filter "name=test-comps-image2image*")
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
