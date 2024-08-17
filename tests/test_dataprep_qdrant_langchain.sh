#!/bin/bash
# Copyright (C) 2024 Intel Corporation
# SPDX-License-Identifier: Apache-2.0

set -x

WORKPATH=$(dirname "$PWD")
LOG_PATH="$WORKPATH/tests"
ip_address=$(hostname -I | awk '{print $1}')

function build_docker_images() {
    cd $WORKPATH

    # dataprep qdrant image
    docker build --no-cache -t opea/dataprep-qdrant:comps --build-arg https_proxy=$https_proxy --build-arg http_proxy=$http_proxy -f comps/dataprep/qdrant/docker/Dockerfile .
    if [ $? -ne 0 ]; then
        echo "opea/dataprep-qdrant built fail"
        exit 1
    else
        echo "opea/dataprep-qdrant built successful"
    fi
}

function start_service() {
    QDRANT_PORT=6360
    docker run -d --name="test-comps-dataprep-qdrant-langchain" -e http_proxy=$http_proxy -e https_proxy=$https_proxy -p $QDRANT_PORT:6333 -p 6334:6334 --ipc=host qdrant/qdrant
    tei_embedding_port=6361
    model="BAAI/bge-base-en-v1.5"
    docker run -d --name="test-comps-dataprep-qdrant-langchain-tei" -e http_proxy=$http_proxy -e https_proxy=$https_proxy -p $tei_embedding_port:80 -v ./data:/data --pull always ghcr.io/huggingface/text-embeddings-inference:cpu-1.5 --model-id $model
    dataprep_service_port=6362
    TEI_EMBEDDING_ENDPOINT="http://${ip_address}:${tei_embedding_port}"
    COLLECTION_NAME="rag-qdrant"
    docker run -d --name="test-comps-dataprep-qdrant-langchain-server" -e http_proxy=$http_proxy -e https_proxy=$https_proxy -e QDRANT_HOST=$ip_address -e QDRANT_PORT=$QDRANT_PORT -e COLLECTION_NAME=$COLLECTION_NAME -e TEI_ENDPOINT=$TEI_EMBEDDING_ENDPOINT -p ${dataprep_service_port}:6007 --ipc=host opea/dataprep-qdrant:comps
    sleep 1m
}

function validate_services() {
    local URL="$1"
    local EXPECTED_RESULT="$2"
    local SERVICE_NAME="$3"
    local DOCKER_NAME="$4"
    local INPUT_DATA="$5"

    if [[ $SERVICE_NAME == *"dataprep_upload_file"* ]]; then
        cd $LOG_PATH
        HTTP_RESPONSE=$(curl --silent --write-out "HTTPSTATUS:%{http_code}" -X POST -F 'files=@./dataprep_file.txt' -H 'Content-Type: multipart/form-data' "$URL")
    elif [[ $SERVICE_NAME == *"dataprep_upload_link"* ]]; then
        HTTP_RESPONSE=$(curl --silent --write-out "HTTPSTATUS:%{http_code}" -X POST -F 'link_list=["https://www.ces.tech/"]' "$URL")
    else
        HTTP_RESPONSE=$(curl --silent --write-out "HTTPSTATUS:%{http_code}" -X POST -d "$INPUT_DATA" -H 'Content-Type: application/json' "$URL")
    fi
    HTTP_STATUS=$(echo $HTTP_RESPONSE | tr -d '\n' | sed -e 's/.*HTTPSTATUS://')
    RESPONSE_BODY=$(echo $HTTP_RESPONSE | sed -e 's/HTTPSTATUS\:.*//g')

    docker logs ${DOCKER_NAME} >> ${LOG_PATH}/${SERVICE_NAME}.log

    # check response status
    if [ "$HTTP_STATUS" -ne "200" ]; then
        echo "[ $SERVICE_NAME ] HTTP status is not 200. Received status was $HTTP_STATUS"
        docker logs test-comps-dataprep-qdrant-langchain
        docker logs test-comps-dataprep-qdrant-langchain-tei
        docker logs test-comps-dataprep-qdrant-langchain-server
        exit 1
    else
        echo "[ $SERVICE_NAME ] HTTP status is 200. Checking content..."
    fi
    # check response body
    if [[ "$RESPONSE_BODY" != *"$EXPECTED_RESULT"* ]]; then
        echo "[ $SERVICE_NAME ] Content does not match the expected result: $RESPONSE_BODY"
        docker logs test-comps-dataprep-qdrant-langchain
        docker logs test-comps-dataprep-qdrant-langchain-tei
        docker logs test-comps-dataprep-qdrant-langchain-server
        exit 1
    else
        echo "[ $SERVICE_NAME ] Content is as expected."
    fi

    sleep 1s
}

function validate_microservice() {
    # tei for embedding service
    validate_services \
        "${ip_address}:6361/embed" \
        "[[" \
        "tei_embedding" \
        "test-comps-dataprep-qdrant-langchain-tei" \
        '{"inputs":"What is Deep Learning?"}'

    # dataprep upload file
    echo "Deep learning is a subset of machine learning that utilizes neural networks with multiple layers to analyze various levels of abstract data representations. It enables computers to identify patterns and make decisions with minimal human intervention by learning from large amounts of data." > $LOG_PATH/dataprep_file.txt
    validate_services \
        "${ip_address}:6362/v1/dataprep" \
        "Data preparation succeeded" \
        "dataprep_upload_file" \
        "test-comps-dataprep-qdrant-langchain-server"

    # dataprep upload link
    validate_services \
        "${ip_address}:6362/v1/dataprep" \
        "Data preparation succeeded" \
        "dataprep_upload_link" \
        "test-comps-dataprep-qdrant-langchain-server"

}

function stop_docker() {
    cid=$(docker ps -aq --filter "name=test-comps-dataprep-qdrant-langchain*")
    if [[ ! -z "$cid" ]]; then docker stop $cid && docker rm $cid && sleep 1s; fi

    rm $LOG_PATH/dataprep_file.txt
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
