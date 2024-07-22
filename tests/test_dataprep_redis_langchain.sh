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
    docker build --no-cache -t opea/dataprep-redis:comps --build-arg https_proxy=$https_proxy --build-arg http_proxy=$http_proxy -f comps/dataprep/redis/langchain/docker/Dockerfile .
}

function start_service() {
    docker run -d --name="test-comps-dataprep-redis-langchain" -e http_proxy=$http_proxy -e https_proxy=$https_proxy -p 6380:6379 -p 8002:8001 --ipc=host redis/redis-stack:7.2.0-v9
    dataprep_service_port=5013
    dataprep_file_service_port=5016
    dataprep_del_service_port=5020
    REDIS_URL="redis://${ip_address}:6380"
    docker run -d --name="test-comps-dataprep-redis-langchain-server" -e http_proxy=$http_proxy -e https_proxy=$https_proxy -e REDIS_URL=$REDIS_URL -p ${dataprep_service_port}:6007 -p ${dataprep_file_service_port}:6008 -p ${dataprep_del_service_port}:6009 --ipc=host opea/dataprep-redis:comps
    sleep 1m
}

function validate_microservice() {
    cd $LOG_PATH

    # test /v1/dataprep
    dataprep_service_port=5013
    URL="http://${ip_address}:$dataprep_service_port/v1/dataprep"
    echo "Deep learning is a subset of machine learning that utilizes neural networks with multiple layers to analyze various levels of abstract data representations. It enables computers to identify patterns and make decisions with minimal human intervention by learning from large amounts of data." > $LOG_PATH/dataprep_file.txt
    HTTP_STATUS=$(curl -s -o /dev/null -w "%{http_code}" -X POST -F 'files=@./dataprep_file.txt' -H 'Content-Type: multipart/form-data' "$URL")
    if [ "$HTTP_STATUS" -eq 200 ]; then
        echo "[ dataprep ] HTTP status is 200. Checking content..."
        local CONTENT=$(curl -s -X POST -F 'files=@./dataprep_file.txt' -H 'Content-Type: multipart/form-data' "$URL" | tee ${LOG_PATH}/dataprep.log)

        if echo "$CONTENT" | grep -q "Data preparation succeeded"; then
            echo "[ dataprep ] Content is as expected."
        else
            echo "[ dataprep ] Content does not match the expected result: $CONTENT"
            docker logs test-comps-dataprep-redis-langchain-server >> ${LOG_PATH}/dataprep.log
            exit 1
        fi
    else
        echo "[ dataprep ] HTTP status is not 200. Received status was $HTTP_STATUS"
        docker logs test-comps-dataprep-redis-langchain-server >> ${LOG_PATH}/dataprep.log
        exit 1
    fi

    # test /v1/dataprep/get_file
    dataprep_file_service_port=5016
    URL="http://${ip_address}:$dataprep_file_service_port/v1/dataprep/get_file"
    HTTP_STATUS=$(curl -s -o /dev/null -w "%{http_code}" -X POST -H 'Content-Type: application/json' "$URL")
    if [ "$HTTP_STATUS" -eq 200 ]; then
        echo "[ dataprep - file ] HTTP status is 200. Checking content..."
        local CONTENT=$(curl -s -X POST -H 'Content-Type: application/json' "$URL" | tee ${LOG_PATH}/dataprep_file.log)

        if echo "$CONTENT" | grep -q '{"name":'; then
            echo "[ dataprep - file ] Content is as expected."
        else
            echo "[ dataprep - file ] Content does not match the expected result: $CONTENT"
            docker logs test-comps-dataprep-redis-langchain-server >> ${LOG_PATH}/dataprep_file.log
            exit 1
        fi
    else
        echo "[ dataprep - file ] HTTP status is not 200. Received status was $HTTP_STATUS"
        docker logs test-comps-dataprep-redis-langchain-server >> ${LOG_PATH}/dataprep_file.log
        exit 1
    fi

    # test /v1/dataprep/delete_file
    dataprep_file_service_port=5016
    URL="http://${ip_address}:$dataprep_del_service_port/v1/dataprep/delete_file"
    HTTP_STATUS=$(curl -s -o /dev/null -w "%{http_code}" -X POST -d '{"file_path": "dataprep_file.txt"}' -H 'Content-Type: application/json' "$URL")
    if [ "$HTTP_STATUS" -eq 200 ]; then
        echo "[ dataprep - del ] HTTP status is 200."
        docker logs test-comps-dataprep-redis-langchain-server >> ${LOG_PATH}/dataprep_del.log
    else
        echo "[ dataprep - del ] HTTP status is not 200. Received status was $HTTP_STATUS"
        docker logs test-comps-dataprep-redis-langchain-server >> ${LOG_PATH}/dataprep_del.log
        exit 1
    fi
}

function stop_docker() {
    cid=$(docker ps -aq --filter "name=test-comps-dataprep-redis-langchain*")
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
