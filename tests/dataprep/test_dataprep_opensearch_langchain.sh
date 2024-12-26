#!/bin/bash
# Copyright (C) 2024 Intel Corporation
# SPDX-License-Identifier: Apache-2.0

set -x

WORKPATH=$(dirname "$PWD")
LOG_PATH="$WORKPATH/tests"
ip_address=$(hostname -I | awk '{print $1}')
dataprep_service_port="6007"
OPENSEARCH_INITIAL_ADMIN_PASSWORD="StRoNgOpEa0)"

function build_docker_images() {
    cd $WORKPATH
    echo $(pwd)
    docker build -t opea/dataprep-opensearch:latest --build-arg https_proxy=$https_proxy --build-arg http_proxy=$http_proxy -f comps/dataprep/opensearch/langchain/Dockerfile .
    if [ $? -ne 0 ]; then
        echo "opea/dataprep-opensearch built fail"
        exit 1
    else
        echo "opea/dataprep-opensearch built successful"
    fi
}

function start_service() {
    # Start OpenSearch vector db container
    docker run -d \
        --name test-comps-dataprep-opensearch-langchain \
        -e cluster.name=opensearch-cluster \
        -e node.name=opensearch-vector-db \
        -e discovery.seed_hosts=opensearch-vector-db \
        -e cluster.initial_master_nodes=opensearch-vector-db \
        -e bootstrap.memory_lock=true \
        -e "OPENSEARCH_JAVA_OPTS=-Xms512m -Xmx512m" \
        -e OPENSEARCH_INITIAL_ADMIN_PASSWORD=$OPENSEARCH_INITIAL_ADMIN_PASSWORD \
        --ulimit memlock=-1:-1 \
        --ulimit nofile=65536:65536 \
        -p 9200:9200 \
        -p 9600:9600 \
        opensearchproject/opensearch:latest

    # Start OpenSearch dataprep container
    OPENSEARCH_URL="http://${ip_address}:9200"
    echo $(OPENSEARCH_URL)
    INDEX_NAME="file-index"
    docker run -d \
        --name test-comps-dataprep-opensearch-langchain-server \
        -p 6007:6007 \
        -e https_proxy=$https_proxy \
        -e http_proxy=$http_proxy \
        -e OPENSEARCH_INITIAL_ADMIN_PASSWORD=$OPENSEARCH_INITIAL_ADMIN_PASSWORD \
        -e OPENSEARCH_URL=$OPENSEARCH_URL \
        -e INDEX_NAME=$INDEX_NAME \
        opea/dataprep-opensearch:latest

    sleep 2m
}

function validate_microservice() {
    cd $LOG_PATH

    # test /v1/dataprep upload file
    URL="http://${ip_address}:$dataprep_service_port/v1/dataprep"
    echo "Deep learning is a subset of machine learning that utilizes neural networks with multiple layers to analyze various levels of abstract data representations. It enables computers to identify patterns and make decisions with minimal human intervention by learning from large amounts of data." > $LOG_PATH/dataprep_file.txt
    HTTP_RESPONSE=$(curl --silent --write-out "HTTPSTATUS:%{http_code}" -X POST -F 'files=@./dataprep_file.txt' -H 'Content-Type: multipart/form-data' -k -u admin:$OPENSEARCH_INITIAL_ADMIN_PASSWORD "$URL")
    HTTP_STATUS=$(echo $HTTP_RESPONSE | tr -d '\n' | sed -e 's/.*HTTPSTATUS://')
    RESPONSE_BODY=$(echo $HTTP_RESPONSE | sed -e 's/HTTPSTATUS\:.*//g')
    SERVICE_NAME="dataprep - upload - file"

    if [ "$HTTP_STATUS" -ne "200" ]; then
        echo "[ $SERVICE_NAME ] HTTP status is not 200. Received status was $HTTP_STATUS"
        docker logs test-comps-dataprep-opensearch-langchain-server >> ${LOG_PATH}/dataprep_upload_file.log
        exit 1
    else
        echo "[ $SERVICE_NAME ] HTTP status is 200. Checking content..."
    fi
    if [[ "$RESPONSE_BODY" != *"Data preparation succeeded"* ]]; then
        echo "[ $SERVICE_NAME ] Content does not match the expected result: $RESPONSE_BODY"
        docker logs test-comps-dataprep-opensearch-langchain-server >> ${LOG_PATH}/dataprep_upload_file.log
        exit 1
    else
        echo "[ $SERVICE_NAME ] Content is as expected."
    fi


    # test /v1/dataprep upload link
    URL="http://${ip_address}:$dataprep_service_port/v1/dataprep"
    HTTP_RESPONSE=$(curl --silent --write-out "HTTPSTATUS:%{http_code}" -X POST -F 'link_list=["https://www.ces.tech/"]' -k -u admin:$OPENSEARCH_INITIAL_ADMIN_PASSWORD "$URL")
    HTTP_STATUS=$(echo $HTTP_RESPONSE | tr -d '\n' | sed -e 's/.*HTTPSTATUS://')
    RESPONSE_BODY=$(echo $HTTP_RESPONSE | sed -e 's/HTTPSTATUS\:.*//g')
    SERVICE_NAME="dataprep - upload - link"


    if [ "$HTTP_STATUS" -ne "200" ]; then
        echo "[ $SERVICE_NAME ] HTTP status is not 200. Received status was $HTTP_STATUS"
        docker logs test-comps-dataprep-opensearch-langchain-server >> ${LOG_PATH}/dataprep_upload_link.log
        exit 1
    else
        echo "[ $SERVICE_NAME ] HTTP status is 200. Checking content..."
    fi
    if [[ "$RESPONSE_BODY" != *"Data preparation succeeded"* ]]; then
        echo "[ $SERVICE_NAME ] Content does not match the expected result: $RESPONSE_BODY"
        docker logs test-comps-dataprep-opensearch-langchain-server >> ${LOG_PATH}/dataprep_upload_link.log
        exit 1
    else
        echo "[ $SERVICE_NAME ] Content is as expected."
    fi

    # test /v1/dataprep/get_file
    URL="http://${ip_address}:$dataprep_service_port/v1/dataprep/get_file"
    HTTP_RESPONSE=$(curl --silent --write-out "HTTPSTATUS:%{http_code}" -X POST -k -u admin:$OPENSEARCH_INITIAL_ADMIN_PASSWORD "$URL")
    HTTP_STATUS=$(echo $HTTP_RESPONSE | tr -d '\n' | sed -e 's/.*HTTPSTATUS://')
    RESPONSE_BODY=$(echo $HTTP_RESPONSE | sed -e 's/HTTPSTATUS\:.*//g')
    SERVICE_NAME="dataprep - get"

    if [ "$HTTP_STATUS" -ne "200" ]; then
        echo "[ $SERVICE_NAME ] HTTP status is not 200. Received status was $HTTP_STATUS"
        docker logs test-comps-dataprep-opensearch-langchain-server >> ${LOG_PATH}/dataprep_file.log
        exit 1
    else
        echo "[ $SERVICE_NAME ] HTTP status is 200. Checking content..."
    fi
    if [[ "$RESPONSE_BODY" -ne "null" ]]; then
        echo "[ $SERVICE_NAME ] Content does not match the expected result: $RESPONSE_BODY"
        docker logs test-comps-dataprep-opensearch-langchain-server >> ${LOG_PATH}/dataprep_file.log
        exit 1
    else
        echo "[ $SERVICE_NAME ] Content is as expected."
    fi

    # test /v1/dataprep/delete_file
    URL="http://${ip_address}:$dataprep_service_port/v1/dataprep/delete_file"
    HTTP_RESPONSE=$(curl --silent --write-out "HTTPSTATUS:%{http_code}" -X POST -d '{"file_path": "dataprep_file.txt"}' -H 'Content-Type: application/json' -k -u admin:$OPENSEARCH_INITIAL_ADMIN_PASSWORD "$URL")
    HTTP_STATUS=$(echo $HTTP_RESPONSE | tr -d '\n' | sed -e 's/.*HTTPSTATUS://')
    RESPONSE_BODY=$(echo $HTTP_RESPONSE | sed -e 's/HTTPSTATUS\:.*//g')
    SERVICE_NAME="dataprep - del"

    # check response status
    if [ "$HTTP_STATUS" -ne "404" ]; then
        echo "[ $SERVICE_NAME ] HTTP status is not 404. Received status was $HTTP_STATUS"
        docker logs test-comps-dataprep-opensearch-langchain-server >> ${LOG_PATH}/dataprep_del.log
        exit 1
    else
        echo "[ $SERVICE_NAME ] HTTP status is 404. Checking content..."
    fi
    # check response body
    if [[ "$RESPONSE_BODY" != *'{"detail":"Single file deletion is not implemented yet"}'* ]]; then
        echo "[ $SERVICE_NAME ] Content does not match the expected result: $RESPONSE_BODY"
        docker logs test-comps-dataprep-opensearch-langchain-server >> ${LOG_PATH}/dataprep_del.log
        exit 1
    else
        echo "[ $SERVICE_NAME ] Content is as expected."
    fi
}

function stop_service() {
    cid=$(docker ps -aq --filter "name=test-comps-dataprep-opensearch-langchain*")
    if [[ ! -z "$cid" ]]; then docker stop $cid && docker rm $cid && sleep 1s; fi

}

function main() {
    stop_service

    build_docker_images
    start_service

    validate_microservice

    stop_service
    # echo y | docker system prune
}

main
