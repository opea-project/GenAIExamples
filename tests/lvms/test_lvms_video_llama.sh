#!/bin/bash
# Copyright (C) 2024 Intel Corporation
# SPDX-License-Identifier: Apache-2.0

set -xe

WORKPATH=$(dirname "$PWD")
LOG_PATH="$WORKPATH/tests"
ip_address=$(hostname -I | awk '{print $1}')

function build_docker_images() {
    cd $WORKPATH
    echo $(pwd)
    docker build --no-cache --build-arg https_proxy=$https_proxy --build-arg http_proxy=$http_proxy -t opea/lvm-video-llama:comps --build-arg https_proxy=$https_proxy --build-arg http_proxy=$http_proxy -f comps/lvms/src/integrations/dependency/video-llama/Dockerfile .
    if $? ; then
        echo "opea/lvm-video-llama built fail"
        exit 1
    else
        echo "opea/lvm-video-llama built successful"
    fi
    docker build --no-cache --build-arg https_proxy=$https_proxy --build-arg http_proxy=$http_proxy -t opea/lvm:comps --build-arg https_proxy=$https_proxy --build-arg http_proxy=$http_proxy  -f comps/lvms/src/Dockerfile .
    if $? ; then
        echo "opea/lvm built fail"
        exit 1
    else
        echo "opea/lvm built successful"
    fi

}

function start_service() {
    cd $WORKPATH
    unset http_proxy
    dependency_port=5051
    server_port=5052
    export LVM_ENDPOINT=http://$ip_address:$dependency_port

    docker run -d --name="test-comps-lvm-video-llama-dependency" -p $dependency_port:9009 \
        --ipc=host \
        -e http_proxy=$http_proxy \
        -e https_proxy=$https_proxy \
        -e no_proxy=$no_proxy \
        -e llm_download="True" \
        opea/lvm-video-llama:comps

    # check whether lvm dependency is fully ready
    n=0
    until [[ "$n" -ge 100 ]] || [[ $ready == true ]]; do
        docker logs test-comps-lvm-video-llama-dependency &> ${LOG_PATH}/lvm-video-llama-dependency.log
        n=$((n+1))
        if grep -q "Uvicorn running on" ${LOG_PATH}/lvm-video-llama-dependency.log; then
            break
        fi
        sleep 5s
    done
    sleep 5s

    docker run -d --name="test-comps-lvm-video-llama" -e LVM_COMPONENT_NAME="OPEA_VIDEO_LLAMA_LVM" -p $server_port:9399 \
        --ipc=host \
        -e http_proxy=$http_proxy \
        -e https_proxy=$https_proxy \
        -e no_proxy=$no_proxy \
        -e LVM_ENDPOINT=$LVM_ENDPOINT \
        opea/lvm:comps

    echo "Waiting for the LVM service to start"

    # check whether lvm service is fully ready
    n=0
    until [[ "$n" -ge 100 ]] || [[ $ready == true ]]; do
        docker logs test-comps-lvm-video-llama &> ${LOG_PATH}/lvm-video-llama.log
        n=$((n+1))
        if grep -q "Uvicorn running on" ${LOG_PATH}/lvm-video-llama.log; then
            break
        fi
        sleep 5s
    done
    sleep 5s
}

function validate_microservice() {

    server_port=5052
    result=$(http_proxy="" curl http://localhost:$server_port/v1/lvm -X POST -d '{"video_url":"silence_girl.mp4","chunk_start": 0,"chunk_duration": 7,"prompt":"What is the person doing?","max_new_tokens": 50}' -H 'Content-Type: application/json')

    if [[ $result == *"silence"* ]]; then
        echo "Result correct."
    else
        echo "Result wrong."
        docker logs test-comps-lvm-video-llama-dependency &> ${LOG_PATH}/lvm-video-llama-dependency.log
        docker logs test-comps-lvm-video-llama &> ${LOG_PATH}/lvm-video-llama.log
        exit 1
    fi
}

function stop_docker() {
    cid=$(docker ps -aq --filter "name=test-comps-lvm-video-llama*")
    if [[ ! -z "$cid" ]]; then docker stop $cid && docker rm $cid && sleep 1s; fi
    if docker volume ls | grep -q video-llama-model; then
        docker volume rm video-llama-model || echo "Volume video-llama-model does not exist.";
    fi

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
