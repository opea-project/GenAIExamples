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
    # langchain mosec embedding image
    docker build --no-cache -t opea/langchain-mosec:comps --build-arg http_proxy=$http_proxy --build-arg https_proxy=$https_proxy -f comps/embeddings/mosec/langchain/dependency/Dockerfile .
    if [ $? -ne 0 ]; then
        echo "opea/langchain-mosec built fail"
        exit 1
    else
        echo "opea/langchain-mosec built successful"
    fi
    # dataprep milvus image
    docker build --no-cache -t opea/dataprep-milvus:comps --build-arg https_proxy=$https_proxy --build-arg http_proxy=$http_proxy -f comps/dataprep/milvus/langchain/Dockerfile .
    if [ $? -ne 0 ]; then
        echo "opea/dataprep-milvus built fail"
        exit 1
    else
        echo "opea/dataprep-milvus built successful"
    fi
}

function start_service() {
    # start milvus vector db
    mkdir $WORKPATH/milvus
    cd $WORKPATH/milvus
    wget https://raw.githubusercontent.com/milvus-io/milvus/v2.4.9/configs/milvus.yaml
    wget https://github.com/milvus-io/milvus/releases/download/v2.4.9/milvus-standalone-docker-compose.yml -O docker-compose.yml
    sed '/- \${DOCKER_VOLUME_DIRECTORY:-\.}\/volumes\/milvus:\/var\/lib\/milvus/a \ \ \ \ \ \ - \${DOCKER_VOLUME_DIRECTORY:-\.}\/milvus.yaml:\/milvus\/configs\/milvus.yaml' -i docker-compose.yml
    docker compose up -d

    # set service ports
    mosec_embedding_port=5021
    dataprep_service_port=5022

    # start mosec embedding service
    docker run -d --name="test-comps-dataprep-milvus-mosec-server" -p $mosec_embedding_port:8000 -e http_proxy=$http_proxy -e https_proxy=$https_proxy opea/langchain-mosec:comps

    # start dataprep service
    MOSEC_EMBEDDING_ENDPOINT="http://${ip_address}:${mosec_embedding_port}"
    MILVUS=${ip_address}
    docker run -d --name="test-comps-dataprep-milvus-server" -p ${dataprep_service_port}:6010 -e http_proxy=$http_proxy -e https_proxy=$https_proxy -e no_proxy=$no_proxy -e MOSEC_EMBEDDING_ENDPOINT=${MOSEC_EMBEDDING_ENDPOINT} -e MILVUS=${MILVUS} -e LOGFLAG=true --ipc=host opea/dataprep-milvus:comps
    sleep 1m
}

function validate_service() {
    local URL="$1"
    local EXPECTED_RESULT="$2"
    local SERVICE_NAME="$3"
    local DOCKER_NAME="$4"
    local INPUT_DATA="$5"

    if [[ $SERVICE_NAME == *"dataprep_upload_file"* ]]; then
        cd $LOG_PATH
        HTTP_RESPONSE=$(curl --silent --write-out "HTTPSTATUS:%{http_code}" -X POST -F 'files=@./dataprep_file.txt' -H 'Content-Type: multipart/form-data' "$URL")
    elif [[ $SERVICE_NAME == *"dataprep_upload_link"* ]]; then
        HTTP_RESPONSE=$(curl --silent --write-out "HTTPSTATUS:%{http_code}" -X POST -F 'link_list=["https://www.ces.tech/"]' -F "chunk_size=500" "$URL")
    elif [[ $SERVICE_NAME == *"dataprep_get"* ]]; then
        HTTP_RESPONSE=$(curl --silent --write-out "HTTPSTATUS:%{http_code}" -X POST -H 'Content-Type: application/json' "$URL")
    elif [[ $SERVICE_NAME == *"dataprep_del"* ]]; then
        HTTP_RESPONSE=$(curl --silent --write-out "HTTPSTATUS:%{http_code}" -X POST -d '{"file_path": "all"}' -H 'Content-Type: application/json' "$URL")
    else
        HTTP_RESPONSE=$(curl --silent --write-out "HTTPSTATUS:%{http_code}" -X POST -d "$INPUT_DATA" -H 'Content-Type: application/json' "$URL")
    fi
    HTTP_STATUS=$(echo $HTTP_RESPONSE | tr -d '\n' | sed -e 's/.*HTTPSTATUS://')
    RESPONSE_BODY=$(echo $HTTP_RESPONSE | sed -e 's/HTTPSTATUS\:.*//g')

    docker logs ${DOCKER_NAME} >> ${LOG_PATH}/${SERVICE_NAME}.log

    # check response status
    if [ "$HTTP_STATUS" -ne "200" ]; then
        echo "[ $SERVICE_NAME ] HTTP status is not 200. Received status was $HTTP_STATUS"
        #####################
        if [[ $SERVICE_NAME == *"dataprep_upload_link"* ]]; then
            docker logs test-comps-dataprep-milvus-mosec-server >> ${LOG_PATH}/mosec-embedding.log
        fi
        exit 1
    else
        echo "[ $SERVICE_NAME ] HTTP status is 200. Checking content..."
    fi
    # check response body
    if [[ "$RESPONSE_BODY" != *"$EXPECTED_RESULT"* ]]; then
        echo "[ $SERVICE_NAME ] Content does not match the expected result: $RESPONSE_BODY"
        exit 1
    else
        echo "[ $SERVICE_NAME ] Content is as expected."
    fi

    sleep 5s
}

function validate_microservice() {
    cd $LOG_PATH
    dataprep_service_port=5022

    # test /v1/dataprep/delete_file
    validate_service \
        "http://${ip_address}:${dataprep_service_port}/v1/dataprep/delete_file" \
        '{"status":true}' \
        "dataprep_del" \
        "test-comps-dataprep-milvus-server"

    # test /v1/dataprep upload file
    echo "Deep learning is a subset of machine learning that utilizes neural networks with multiple layers to analyze various levels of abstract data representations. It enables computers to identify patterns and make decisions with minimal human intervention by learning from large amounts of data." > $LOG_PATH/dataprep_file.txt
    validate_service \
        "http://${ip_address}:${dataprep_service_port}/v1/dataprep" \
        "Data preparation succeeded" \
        "dataprep_upload_file" \
        "test-comps-dataprep-milvus-server"

    # test /v1/dataprep upload link
    validate_service \
        "http://${ip_address}:${dataprep_service_port}/v1/dataprep" \
        "Data preparation succeeded" \
        "dataprep_upload_link" \
        "test-comps-dataprep-milvus-server"

    # test /v1/dataprep/get_file
    validate_service \
        "http://${ip_address}:${dataprep_service_port}/v1/dataprep/get_file" \
        '{"name":' \
        "dataprep_get" \
        "test-comps-dataprep-milvus-server"

}

function stop_docker() {
    cd $WORKPATH
    rm -rf milvus/
    cid=$(docker ps -aq --filter "name=test-comps-dataprep-milvus*")
    if [[ ! -z "$cid" ]]; then docker stop $cid && docker rm $cid && sleep 1s; fi
    cid=$(docker ps -aq --filter "name=milvus-*")
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
