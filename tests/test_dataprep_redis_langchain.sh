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
    docker build --no-cache -t opea/dataprep-redis:comps --build-arg https_proxy=$https_proxy --build-arg http_proxy=$http_proxy -f comps/dataprep/redis/langchain/docker/Dockerfile .
}

function start_service() {
    docker run -d --name="test-comps-dataprep-redis" -e http_proxy=$http_proxy -e https_proxy=$https_proxy -p 6379:6379 -p 8001:8001 --ipc=host redis/redis-stack:7.2.0-v9
    dataprep_service_port=5013
    REDIS_URL="redis://${ip_address}:6379"
    docker run -d --name="test-comps-dataprep-redis-server" -e http_proxy=$http_proxy -e https_proxy=$https_proxy -e REDIS_URL=$REDIS_URL -p ${dataprep_service_port}:6007 --ipc=host opea/dataprep-redis:comps
    sleep 1m
}

function validate_microservice() {
    cd $LOG_PATH
    dataprep_service_port=5013
    URL="http://${ip_address}:$dataprep_service_port/v1/dataprep"
    echo "Deep learning is a subset of machine learning that utilizes neural networks with multiple layers to analyze various levels of abstract data representations. It enables computers to identify patterns and make decisions with minimal human intervention by learning from large amounts of data." > $LOG_PATH/dataprep_file.txt
    HTTP_STATUS=$(curl -s -o /dev/null -w "%{http_code}" -X POST -F 'files=@./dataprep_file.txt' -H 'Content-Type: multipart/form-data' "$URL")
    if [ "$HTTP_STATUS" -eq 200 ]; then
        echo "[ dataprep ] HTTP status is 200. Checking content..."
        local CONTENT=$(curl -s -X POST -F 'files=@./dataprep_file.txt' -H 'Content-Type: multipart/form-data' "$URL" | tee ${LOG_PATH}/dataprep.log)

        if echo 'Data preparation succeeded' | grep -q "$EXPECTED_RESULT"; then
            echo "[ dataprep ] Content is as expected."
        else
            echo "[ dataprep ] Content does not match the expected result: $CONTENT"
            docker logs test-comps-dataprep-redis-server >> ${LOG_PATH}/dataprep.log
            exit 1
        fi
    else
        echo "[ dataprep ] HTTP status is not 200. Received status was $HTTP_STATUS"
        docker logs test-comps-dataprep-redis-server >> ${LOG_PATH}/dataprep.log
        exit 1
    fi
    rm -rf $LOG_PATH/dataprep_file.txt
}

function stop_docker() {
    cid=$(docker ps -aq --filter "name=test-comps-dataprep-redis*")
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
