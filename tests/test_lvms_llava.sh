#!/bin/bash
# Copyright (C) 2024 Intel Corporation
# SPDX-License-Identifier: Apache-2.0

set -x

WORKPATH=$(dirname "$PWD")
ip_address=$(hostname -I | awk '{print $1}')

function build_docker_images() {
    cd $WORKPATH
    echo $(pwd)
    docker build -t opea/llava:comps -f comps/lvms/llava/Dockerfile .
    docker build --no-cache -t opea/lvm:comps -f comps/lvms/Dockerfile .
}

function start_service() {
    unset http_proxy
    docker run -d --name="test-comps-lvm-llava" -e http_proxy=$http_proxy -e https_proxy=$https_proxy -p 8399:8399 --ipc=host opea/llava:comps
    docker run -d --name="test-comps-lvm" -e LVM_ENDPOINT=http://$ip_address:8399 -e http_proxy=$http_proxy -e https_proxy=$https_proxy -p 9399:9399 --ipc=host opea/lvm:comps
    sleep 8m
}

function validate_microservice() {

    result=$(http_proxy="" curl http://localhost:9399/v1/lvm -XPOST -d '{"image": "iVBORw0KGgoAAAANSUhEUgAAAAoAAAAKCAYAAACNMs+9AAAAFUlEQVR42mP8/5+hnoEIwDiqkL4KAcT9GO0U4BxoAAAAAElFTkSuQmCC", "prompt":"What is this?"}' -H 'Content-Type: application/json')
    if [[ $result == *"yellow"* ]]; then
        echo "Result correct."
    else
        echo "Result wrong."
        docker logs test-comps-lvm-llava
        docker logs test-comps-lvm
        exit 1
    fi

}

function stop_docker() {
    cid=$(docker ps -aq --filter "name=test-comps-lvm*")
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
