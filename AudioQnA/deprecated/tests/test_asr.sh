#!/bin/bash
# Copyright (C) 2024 Intel Corporation
# SPDX-License-Identifier: Apache-2.0

set -xe

function test_env_setup() {
    WORKPATH=$(dirname "$PWD")/audio/docker
    LOG_PATH=$(dirname "$PWD")/tests/asr.log
    ASR_CONTAINER_NAME="test-audioqna-asr"
    cd $WORKPATH
}

function start_asr_service() {
    cd $WORKPATH
    docker build . --build-arg http_proxy=${http_proxy} --build-arg https_proxy=${http_proxy} -f Dockerfile_asr -t intel/gen-ai-examples:$ASR_CONTAINER_NAME
    docker run -d --name=$ASR_CONTAINER_NAME -e http_proxy=$http_proxy -e https_proxy=$https_proxy -p 8018:8008 intel/gen-ai-examples:$ASR_CONTAINER_NAME
    sleep 1m
}

function run_tests() {
    cd $WORKPATH
    rm -f sample.wav
    wget https://github.com/intel/intel-extension-for-transformers/raw/main/intel_extension_for_transformers/neural_chat/assets/audio/sample.wav
    http_proxy= curl -F 'file=@sample.wav' http://localhost:8018/v1/audio/transcriptions > $LOG_PATH
    rm -f sample.wav
}

function check_response() {
    cd $WORKPATH
    echo "Checking response"
    local status=false
    if [[ -f $LOG_PATH ]] && [[ $(grep -c "who is pat gelsinger" $LOG_PATH) != 0 ]]; then
        status=true
    fi

    if [ $status == false ]; then
        echo "Response check failed"
        exit 1
    else
        echo "Response check succeed"
    fi
}

function docker_stop() {
    local container_name=$1
    cid=$(docker ps -aq --filter "name=$container_name")
    if [[ ! -z "$cid" ]]; then docker stop $cid && docker rm $cid; fi
}



function main() {
    test_env_setup
    docker_stop $ASR_CONTAINER_NAME && sleep 5s
    start_asr_service
    run_tests
    docker_stop $ASR_CONTAINER_NAME && sleep 5s
    echo y | docker system prune
    check_response
}

main
