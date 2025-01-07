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
    docker build -t opea/dataprep-redis:comps --build-arg https_proxy=$https_proxy --build-arg http_proxy=$http_proxy -f comps/dataprep/src/Dockerfile .
    if [ $? -ne 0 ]; then
        echo "opea/dataprep-redis built fail"
        exit 1
    else
        echo "opea/dataprep-redis built successful"
    fi
}

function start_service() {
    REDIS_PORT=6380
    docker run -d --name="test-comps-dataprep-redis-langchain" -e http_proxy=$http_proxy -e https_proxy=$https_proxy -p $REDIS_PORT:6379 -p 8002:8001 --ipc=host redis/redis-stack:7.2.0-v9

    embed_port=5439
    embed_model="BAAI/bge-base-en-v1.5"
    docker run -d -p $embed_port:80 -v ./data:/data --name test-comps-dataprep-redis-langchain-tei-server -e http_proxy=$http_proxy -e https_proxy=$https_proxy --pull always ghcr.io/huggingface/text-embeddings-inference:cpu-1.5 --model-id $embed_model
    export TEI_EMBEDDING_ENDPOINT="http://${ip_address}:${embed_port}"

    export dataprep_service_port=5013
    REDIS_URL="redis://${ip_address}:${REDIS_PORT}"
    export INDEX_NAME="rag_redis"
    export HF_TOKEN=${HF_TOKEN}
    docker run -d --name="test-comps-dataprep-redis-langchain-server" -e http_proxy=$http_proxy -e https_proxy=$https_proxy -e REDIS_URL=$REDIS_URL -e REDIS_HOST=$ip_address -e REDIS_PORT=$REDIS_PORT -e TEI_EMBEDDING_ENDPOINT=${TEI_EMBEDDING_ENDPOINT} -e INDEX_NAME=$INDEX_NAME -e HUGGINGFACEHUB_API_TOKEN=${HF_TOKEN} -e LOGFLAG=true -e DATAPREP_COMPONENT_NAME="OPEA_DATAPREP_REDIS" -p ${dataprep_service_port}:5000 --ipc=host opea/dataprep-redis:comps
    sleep 1m
}

function validate_microservice() {
    cd $LOG_PATH
    export dataprep_service_port=5013

    # test /v1/dataprep/delete
    URL="http://${ip_address}:$dataprep_service_port/v1/dataprep/delete"
    HTTP_RESPONSE=$(curl --silent --write-out "HTTPSTATUS:%{http_code}" -X POST -d '{"file_path": "all"}' -H 'Content-Type: application/json' "$URL")
    HTTP_STATUS=$(echo $HTTP_RESPONSE | tr -d '\n' | sed -e 's/.*HTTPSTATUS://')
    RESPONSE_BODY=$(echo $HTTP_RESPONSE | sed -e 's/HTTPSTATUS\:.*//g')
    SERVICE_NAME="dataprep - del"

    if [ "$HTTP_STATUS" -ne "200" ]; then
        echo "[ $SERVICE_NAME ] HTTP status is not 200. Received status was $HTTP_STATUS"
        docker logs test-comps-dataprep-redis-langchain-server >> ${LOG_PATH}/dataprep_del.log
        exit 1
    else
        echo "[ $SERVICE_NAME ] HTTP status is 200. Checking content..."
    fi
    # check response body
    if [[ "$RESPONSE_BODY" != *'{"status":true}'* ]]; then
        echo "[ $SERVICE_NAME ] Content does not match the expected result: $RESPONSE_BODY"
        docker logs test-comps-dataprep-redis-langchain-server >> ${LOG_PATH}/dataprep_del.log
        exit 1
    else
        echo "[ $SERVICE_NAME ] Content is as expected."
    fi

    # test /v1/dataprep/ingest upload file
    URL="http://${ip_address}:$dataprep_service_port/v1/dataprep/ingest"
    echo "Deep learning is a subset of machine learning that utilizes neural networks with multiple layers to analyze various levels of abstract data representations. It enables computers to identify patterns and make decisions with minimal human intervention by learning from large amounts of data." > $LOG_PATH/dataprep_file.txt
    HTTP_RESPONSE=$(curl --silent --write-out "HTTPSTATUS:%{http_code}" -X POST -F 'files=@./dataprep_file.txt' -H 'Content-Type: multipart/form-data' "$URL")
    HTTP_STATUS=$(echo $HTTP_RESPONSE | tr -d '\n' | sed -e 's/.*HTTPSTATUS://')
    RESPONSE_BODY=$(echo $HTTP_RESPONSE | sed -e 's/HTTPSTATUS\:.*//g')
    SERVICE_NAME="dataprep - upload - file"

    if [ "$HTTP_STATUS" -ne "200" ]; then
        echo "[ $SERVICE_NAME ] HTTP status is not 200. Received status was $HTTP_STATUS"
        docker logs test-comps-dataprep-redis-langchain-server >> ${LOG_PATH}/dataprep_upload_file.log
        exit 1
    else
        echo "[ $SERVICE_NAME ] HTTP status is 200. Checking content..."
    fi
    if [[ "$RESPONSE_BODY" != *"Data preparation succeeded"* ]]; then
        echo "[ $SERVICE_NAME ] Content does not match the expected result: $RESPONSE_BODY"
        docker logs test-comps-dataprep-redis-langchain-server >> ${LOG_PATH}/dataprep_upload_file.log
        exit 1
    else
        echo "[ $SERVICE_NAME ] Content is as expected."
    fi

    # test /v1/dataprep/ingest upload link
    URL="http://${ip_address}:$dataprep_service_port/v1/dataprep/ingest"
    HTTP_RESPONSE=$(curl --silent --write-out "HTTPSTATUS:%{http_code}" -X POST -F 'link_list=["https://www.ces.tech/"]' "$URL")
    HTTP_STATUS=$(echo $HTTP_RESPONSE | tr -d '\n' | sed -e 's/.*HTTPSTATUS://')
    RESPONSE_BODY=$(echo $HTTP_RESPONSE | sed -e 's/HTTPSTATUS\:.*//g')
    SERVICE_NAME="dataprep - upload - link"


    if [ "$HTTP_STATUS" -ne "200" ]; then
        echo "[ $SERVICE_NAME ] HTTP status is not 200. Received status was $HTTP_STATUS"
        docker logs test-comps-dataprep-redis-langchain-server >> ${LOG_PATH}/dataprep_upload_link.log
        exit 1
    else
        echo "[ $SERVICE_NAME ] HTTP status is 200. Checking content..."
    fi
    if [[ "$RESPONSE_BODY" != *"Data preparation succeeded"* ]]; then
        echo "[ $SERVICE_NAME ] Content does not match the expected result: $RESPONSE_BODY"
        docker logs test-comps-dataprep-redis-langchain-server >> ${LOG_PATH}/dataprep_upload_link.log
        exit 1
    else
        echo "[ $SERVICE_NAME ] Content is as expected."
    fi

    # test /v1/dataprep/get
    URL="http://${ip_address}:$dataprep_service_port/v1/dataprep/get"
    HTTP_RESPONSE=$(curl --silent --write-out "HTTPSTATUS:%{http_code}" -X POST "$URL")
    HTTP_STATUS=$(echo $HTTP_RESPONSE | tr -d '\n' | sed -e 's/.*HTTPSTATUS://')
    RESPONSE_BODY=$(echo $HTTP_RESPONSE | sed -e 's/HTTPSTATUS\:.*//g')
    SERVICE_NAME="dataprep - get"

    if [ "$HTTP_STATUS" -ne "200" ]; then
        echo "[ $SERVICE_NAME ] HTTP status is not 200. Received status was $HTTP_STATUS"
        docker logs test-comps-dataprep-redis-langchain-server >> ${LOG_PATH}/dataprep_file.log
        exit 1
    else
        echo "[ $SERVICE_NAME ] HTTP status is 200. Checking content..."
    fi
    if [[ "$RESPONSE_BODY" != *'{"name":'* ]]; then
        echo "[ $SERVICE_NAME ] Content does not match the expected result: $RESPONSE_BODY"
        docker logs test-comps-dataprep-redis-langchain-server >> ${LOG_PATH}/dataprep_file.log
        exit 1
    else
        echo "[ $SERVICE_NAME ] Content is as expected."
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
