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
    docker build --no-cache -t opea/dataprep-vdms:comps --build-arg https_proxy=$https_proxy --build-arg http_proxy=$http_proxy -f comps/dataprep/vdms/multimodal_langchain/Dockerfile .

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
    wget https://github.com/DAMO-NLP-SG/Video-LLaMA/raw/main/examples/silence_girl.mp4 -O silence_girl.mp4
    sleep 5

    # test /v1/dataprep upload file
    URL="http://$ip_address:$dataprep_service_port/v1/dataprep"

    response=$(http_proxy="" curl -s -w "\n%{http_code}" -X POST -F 'files=@./silence_girl.mp4' -H 'Content-Type: multipart/form-data' ${URL})
    CONTENT=$(echo "$response" | sed -e '$ d')
    HTTP_STATUS=$(echo "$response" | tail -n 1)

    if [ "$HTTP_STATUS" -eq 200 ]; then
        echo "[ dataprep-upload-videos ]  HTTP status is 200. Checking content..."
        if echo "$CONTENT" | grep "Videos ingested successfully"; then
            echo "[ dataprep-upload-videos ] Content is correct."
        else
            echo "[ dataprep-upload-videos ] Content is not correct. Received content was $CONTENT"
            docker logs test-comps-dataprep-vdms-server >> ${LOG_PATH}/dataprep-upload-videos.log
            docker logs test-comps-dataprep-vdms >> ${LOG_PATH}/dataprep-upload-videos_vdms.log
            exit 1
        fi
    else
        echo "[ dataprep-upload-videos ] HTTP status is not 200. Received status was $HTTP_STATUS"
        docker logs test-comps-dataprep-vdms-server >> ${LOG_PATH}/dataprep-get-videos.log
        docker logs test-comps-dataprep-vdms >> ${LOG_PATH}/dataprep-upload-videos_vdms.log
        exit 1
    fi

    sleep 1s
    rm ./silence_girl.mp4

    # test /v1/dataprep/get_videos
    URL="http://$ip_address:$dataprep_service_port/v1/dataprep/get_videos"

    response=$(http_proxy="" curl -s -w "\n%{http_code}" -X GET ${URL})
    CONTENT=$(echo "$response" | sed -e '$ d')
    HTTP_STATUS=$(echo "$response" | tail -n 1)

    if [ "$HTTP_STATUS" -eq 200 ]; then
        echo "[ dataprep-get-videos ] HTTP status is 200. Checking content..."
        if echo "$CONTENT" | grep "silence_girl"; then
            echo "[ dataprep-get-videos ] Content is correct."
        else
            echo "[ dataprep-get-videos ] Content is not correct. Received content was $CONTENT"
            docker logs test-comps-dataprep-vdms-server >> ${LOG_PATH}/dataprep-get-videos.log
            exit 1
        fi
    else
        echo "[ dataprep-get-videos ] HTTP status is not 200. Received status was $HTTP_STATUS"
        docker logs test-comps-dataprep-vdms-server >> ${LOG_PATH}/dataprep-get-videos.log
        exit 1
    fi

    # test /v1/dataprep/get_file/{filename}
    file_list=$CONTENT
    filename=$(echo $file_list | sed 's/^\[//;s/\]$//;s/,.*//;s/"//g')
    URL="http://$ip_address:$dataprep_service_port/v1/dataprep/get_file/${filename}"

    http_proxy="" wget ${URL}
    CONTENT=$(ls)
    if echo "$CONTENT" | grep "silence_girl"; then
        echo "[ download_file ] Content is correct."
    else
        echo "[ download_file ] Content is not correct. $CONTENT"
        docker logs test-comps-dataprep-vdms-server >> ${LOG_PATH}/download_file.log
        exit 1
    fi

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
