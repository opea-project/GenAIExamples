#!/bin/bash
# Copyright (C) 2024 Intel Corporation
# SPDX-License-Identifier: Apache-2.0

set -xe

function test_env_setup() {
    WORKPATH=$(dirname "$PWD")
    LOG_PATH="$WORKPATH/tests/inference.log"
    CONTAINER_NAME="test-llava-gaudi-service"
    cd $WORKPATH
}

function launch_llava_service() {
    cd ${WORKPATH}
    cd serving/
    local port=8855
    docker build . --build-arg http_proxy=${http_proxy} --build-arg https_proxy=${http_proxy} -t intel/gen-ai-examples:${CONTAINER_NAME}
    docker run -d --name=${CONTAINER_NAME} -p ${port}:8000 -v ~/.cache/huggingface/hub/:/root/.cache/huggingface/hub/ -e http_proxy=$http_proxy -e https_proxy=$http_proxy \
    --runtime=habana -e HABANA_VISIBLE_DEVICES=all -e OMPI_MCA_btl_vader_single_copy_mechanism=none --cap-add=sys_nice --ipc=host intel/gen-ai-examples:${CONTAINER_NAME}

    sleep 3m
}

function run_tests() {
    cd $WORKPATH
    local port=8855
    curl localhost:${port}/health -v 2>&1 | tee $LOG_PATH
}

function check_response() {
    cd $WORKPATH
    echo "Checking response"
    local status=false
    if [[ -f $LOG_PATH ]] && [[ $(grep -c "200 OK" $LOG_PATH) != 0 ]]; then
        status=true
    fi

    if [ $status == false ]; then
        echo "Response check failed, please check the logs in artifacts!"
        exit 1
    else
        echo "Response check succeed!"
    fi
}

function docker_stop() {
    local container_name=$1
    cid=$(docker ps -aq --filter "name=$container_name")
    if [[ ! -z "$cid" ]]; then docker stop $cid && docker rm $cid; fi
}

function main() {
    test_env_setup
    docker_stop $CONTAINER_NAME && sleep 5s

    launch_llava_service

    run_tests
    check_response

    docker_stop $CONTAINER_NAME && sleep 5s
    echo y | docker system prune
}

main
