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
    docker build --no-cache -t opea/dataprep-vdms:comps --build-arg https_proxy=$https_proxy --build-arg http_proxy=$http_proxy -f comps/dataprep/vdms/langchain/Dockerfile .

    if [ $? -ne 0 ]; then
        echo "opea/dataprep-vdms built fail"
        exit 1
    else
        echo "opea/dataprep-vdms built successful"
    fi
    docker pull intellabs/vdms:latest
}

function start_service() {
    VDMS_PORT=5043
    docker run -d --name="test-comps-dataprep-vdms" -p $VDMS_PORT:55555 intellabs/vdms:latest
    dataprep_service_port=5013
    COLLECTION_NAME="test-comps"
    docker run -d --name="test-comps-dataprep-vdms-server" -e COLLECTION_NAME=$COLLECTION_NAME -e no_proxy=$no_proxy -e http_proxy=$http_proxy -e https_proxy=$https_proxy -e VDMS_HOST=$ip_address -e VDMS_PORT=$VDMS_PORT -p ${dataprep_service_port}:6007 --ipc=host opea/dataprep-vdms:comps
    sleep 30s
}

function validate_microservice() {
    cd $LOG_PATH

    echo "Deep learning is a subset of machine learning that utilizes neural networks with multiple layers to analyze various levels of abstract data representations. It enables computers to identify patterns and make decisions with minimal human intervention by learning from large amounts of data." > $LOG_PATH/dataprep_file.txt

    dataprep_service_port=5013

    URL="http://$ip_address:$dataprep_service_port/v1/dataprep"
    HTTP_STATUS=$(http_proxy="" curl -s -o /dev/null -w "%{http_code}" -X POST -F 'files=@./dataprep_file.txt' -H 'Content-Type: multipart/form-data' ${URL} )
    if [ "$HTTP_STATUS" -eq 200 ]; then
        echo "[ dataprep-upload-file ] HTTP status is 200. Checking content..."
        local CONTENT=$(http_proxy="" curl -s -X POST -F 'files=@./dataprep_file.txt' -H 'Content-Type: multipart/form-data' ${URL} | tee ${LOG_PATH}/dataprep-upload-file.log)
        if echo "$CONTENT" | grep "Data preparation succeeded"; then
            echo "[ dataprep-upload-file ] Content is correct."
        else
            echo "[ dataprep-upload-file ] Content is not correct. Received content was $CONTENT"
            docker logs test-comps-dataprep-vdms-server >> ${LOG_PATH}/dataprep-upload-file.log
            docker logs test-comps-dataprep-vdms >> ${LOG_PATH}/dataprep-upload-file_vdms.log
            exit 1
        fi
    else
        echo "[ dataprep-upload-file ] HTTP status is not 200. Received status was $HTTP_STATUS"
        docker logs test-comps-dataprep-vdms-server >> ${LOG_PATH}/dataprep-upload-file.log
        docker logs test-comps-dataprep-vdms >> ${LOG_PATH}/dataprep-upload-file_vdms.log
        exit 1
    fi
    rm ./dataprep_file.txt

}

function stop_docker() {
    cid=$(docker ps -aq --filter "name=test-comps-dataprep-vdms*")
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
