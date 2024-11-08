#!/bin/bash
# Copyright (C) 2024 Intel Corporation
# SPDX-License-Identifier: Apache-2.0

set -x

WORKPATH=$(dirname "$PWD")
LOG_PATH="$WORKPATH/tests"
ip_address=$(hostname -I | awk '{print $1}')

function build_docker_images() {
    cd $WORKPATH
    echo $(pwd)
    docker build --no-cache -t opea/lvm-llava:comps -f comps/lvms/llava/dependency/Dockerfile .
    if [ $? -ne 0 ]; then
        echo "opea/lvm-llava built fail"
        exit 1
    else
        echo "opea/lvm-llava built successful"
    fi
    docker build --no-cache -t opea/lvm-llava-svc:comps -f comps/lvms/llava/Dockerfile .
    if [ $? -ne 0 ]; then
        echo "opea/lvm-llava-svc built fail"
        exit 1
    else
        echo "opea/lvm-llava-svc built successful"
    fi
}

function start_service() {
    unset http_proxy
    lvm_port=5051
    docker run -d --name="test-comps-lvm-llava" -e http_proxy=$http_proxy -e https_proxy=$https_proxy -p 5028:8399 --ipc=host opea/lvm-llava:comps
    docker run -d --name="test-comps-lvm-llava-svc" -e LVM_ENDPOINT=http://$ip_address:5028 -e http_proxy=$http_proxy -e https_proxy=$https_proxy -p $lvm_port:9399 --ipc=host opea/lvm-llava-svc:comps
    sleep 8m
}

function validate_microservice() {

    lvm_port=5051
    result=$(http_proxy="" curl http://localhost:$lvm_port/v1/lvm -XPOST -d '{"image": "iVBORw0KGgoAAAANSUhEUgAAAAoAAAAKCAYAAACNMs+9AAAAFUlEQVR42mP8/5+hnoEIwDiqkL4KAcT9GO0U4BxoAAAAAElFTkSuQmCC", "prompt":"What is this?"}' -H 'Content-Type: application/json')
    if [[ $result == *"yellow"* ]]; then
        echo "Result correct."
    else
        echo "Result wrong."
        docker logs test-comps-lvm-llava >> ${LOG_PATH}/llava-dependency.log
        docker logs test-comps-lvm-llava-svc >> ${LOG_PATH}/llava-server.log
        exit 1
    fi

    result=$(http_proxy="" curl http://localhost:$lvm_port/v1/lvm -XPOST -d '{"retrieved_docs": [], "initial_query": "What is this?", "top_n": 1, "metadata": [{"b64_img_str": "iVBORw0KGgoAAAANSUhEUgAAAAoAAAAKCAYAAACNMs+9AAAAFUlEQVR42mP8/5+hnoEIwDiqkL4KAcT9GO0U4BxoAAAAAElFTkSuQmCC", "transcript_for_inference": "yellow image", "video_id": "8c7461df-b373-4a00-8696-9a2234359fe0", "time_of_frame_ms":"37000000", "source_video":"WeAreGoingOnBullrun_8c7461df-b373-4a00-8696-9a2234359fe0.mp4"}]}' -H 'Content-Type: application/json')
    if [[ $result == *"yellow"* ]]; then
        echo "Result correct."
    else
        echo "Result wrong."
        docker logs test-comps-lvm-llava >> ${LOG_PATH}/llava-dependency.log
        docker logs test-comps-lvm-llava-svc >> ${LOG_PATH}/llava-server.log
        exit 1
    fi

    result=$(http_proxy="" curl http://localhost:$lvm_port/v1/lvm -XPOST -d '{"retrieved_docs": [], "initial_query": "What is this?", "top_n": 1, "metadata": [{"b64_img_str": "iVBORw0KGgoAAAANSUhEUgAAAAoAAAAKCAYAAACNMs+9AAAAFUlEQVR42mP8/5+hnoEIwDiqkL4KAcT9GO0U4BxoAAAAAElFTkSuQmCC", "transcript_for_inference": "yellow image", "video_id": "8c7461df-b373-4a00-8696-9a2234359fe0", "time_of_frame_ms":"37000000", "source_video":"WeAreGoingOnBullrun_8c7461df-b373-4a00-8696-9a2234359fe0.mp4"}], "chat_template":"The caption of the image is: '\''{context}'\''. {question}"}' -H 'Content-Type: application/json')
    if [[ $result == *"yellow"* ]]; then
        echo "Result correct."
    else
        echo "Result wrong."
        docker logs test-comps-lvm-llava >> ${LOG_PATH}/llava-dependency.log
        docker logs test-comps-lvm-llava-svc >> ${LOG_PATH}/llava-server.log
        exit 1
    fi

    # Test the LVM with text only (no image)
    result=$(http_proxy="" curl http://localhost:$lvm_port/v1/lvm -XPOST -d '{"image": "", "prompt":"What is deep learning?"}' -H 'Content-Type: application/json')
    if [[ $result == *"Deep learning is"* ]]; then
        echo "Result correct."
    else
        echo "Result wrong."
        docker logs test-comps-lvm-llava >> ${LOG_PATH}/llava-dependency.log
        docker logs test-comps-lvm-llava-svc >> ${LOG_PATH}/llava-server.log
        exit 1
    fi

}

function stop_docker() {
    cid=$(docker ps -aq --filter "name=test-comps-*")
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
