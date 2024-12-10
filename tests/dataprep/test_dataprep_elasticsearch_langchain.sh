#!/bin/bash
# Copyright (C) 2024 Intel Corporation
# SPDX-License-Identifier: Apache-2.0

set -x

WORKPATH=$(dirname "$PWD")
LOG_PATH="$WORKPATH/tests"
ip_address=$(hostname -I | awk '{print $1}')
dataprep_service_port=6011

function build_docker_images() {
    cd $WORKPATH
    echo $WORKPATH
    # piull elasticsearch image
    docker pull docker.elastic.co/elasticsearch/elasticsearch:8.16.0

    # build dataprep image for elasticsearch
    docker build --no-cache -t opea/dataprep-elasticsearch:comps --build-arg https_proxy=$https_proxy --build-arg http_proxy=$http_proxy -f $WORKPATH/comps/dataprep/elasticsearch/langchain/Dockerfile .
    if [ $? -ne 0 ]; then
        echo "opea/dataprep-elasticsearch built fail"
        exit 1
    else
        echo "opea/dataprep-elasticsearch built successful"
    fi
}

function start_service() {
    # elasticsearch
    elasticsearch_port=9200
    docker run -d --name test-comps-vectorstore-elasticsearch -e ES_JAVA_OPTS="-Xms1g -Xmx1g" -e "discovery.type=single-node" -e "xpack.security.enabled=false"  -p $elasticsearch_port:9200 -p 9300:9300 docker.elastic.co/elasticsearch/elasticsearch:8.16.0
    export ES_CONNECTION_STRING="http://${ip_address}:${elasticsearch_port}"
    sleep 10s

    # data-prep
    INDEX_NAME="test-elasticsearch"
    docker run -d --name="test-comps-dataprep-elasticsearch" -p $dataprep_service_port:6011 --ipc=host -e http_proxy=$http_proxy -e https_proxy=$https_proxy -e ES_CONNECTION_STRING=$ES_CONNECTION_STRING -e INDEX_NAME=$INDEX_NAME opea/dataprep-elasticsearch:comps
    sleep 15s

    bash ./tests/utils/wait-for-it.sh $ip_address:$dataprep_service_port -s -t 100 -- echo "Dataprep service up"
    DATAPREP_UP=$?
    if [ ${DATAPREP_UP} -ne 0 ]; then
        echo "Could not start Dataprep service."
        return 1
    fi

    sleep 5s
    bash ./tests/utils/wait-for-it.sh ${ip_address}:$dataprep_service_port -s -t 1 -- echo "Dataprep service still up"
    DATAPREP_UP=$?
    if [ ${DATAPREP_UP} -ne 0 ]; then
        echo "Dataprep service crashed."
        return 1
    fi
}

function validate_microservice() {
    cd $LOG_PATH

    # test /v1/dataprep
    URL="http://${ip_address}:$dataprep_service_port/v1/dataprep"
    echo "Deep learning is a subset of machine learning that utilizes neural networks with multiple layers to analyze various levels of abstract data representations. It enables computers to identify patterns and make decisions with minimal human intervention by learning from large amounts of data." > $LOG_PATH/dataprep_file.txt

    HTTP_STATUS=$(curl -s -o /dev/null -w "%{http_code}" -X POST -F 'files=@./dataprep_file.txt' -H 'Content-Type: multipart/form-data' "$URL")
    if [ "$HTTP_STATUS" -eq 200 ]; then
        echo "[ dataprep ] HTTP status is 200. Checking content..."
        cp ./dataprep_file.txt ./dataprep_file2.txt
        local CONTENT=$(curl -s -X POST -F 'files=@./dataprep_file2.txt' -H 'Content-Type: multipart/form-data' "$URL" | tee ${LOG_PATH}/dataprep.log)

        if echo "$CONTENT" | grep -q "Data preparation succeeded"; then
            echo "[ dataprep ] Content is as expected."
        else
            echo "[ dataprep ] Content does not match the expected result: $CONTENT"
            docker logs test-comps-dataprep-elasticsearch >> ${LOG_PATH}/dataprep.log
            exit 1
        fi
    else
        echo "[ dataprep ] HTTP status is not 200. Received status was $HTTP_STATUS"
        docker logs test-comps-dataprep-elasticsearch >> ${LOG_PATH}/dataprep.log
        exit 1
    fi

    # test /v1/dataprep/get_file
    URL="http://${ip_address}:$dataprep_service_port/v1/dataprep/get_file"
    HTTP_STATUS=$(curl -s -o /dev/null -w "%{http_code}" -X POST -H 'Content-Type: application/json' "$URL")
    if [ "$HTTP_STATUS" -eq 200 ]; then
        echo "[ dataprep - file ] HTTP status is 200. Checking content..."
        local CONTENT=$(curl -s -X POST -H 'Content-Type: application/json' "$URL" | tee ${LOG_PATH}/dataprep_file.log)

        if echo "$CONTENT" | grep -q '{"name":'; then
            echo "[ dataprep - file ] Content is as expected."
        else
            echo "[ dataprep - file ] Content does not match the expected result: $CONTENT"
            docker logs test-comps-dataprep-elasticsearch >> ${LOG_PATH}/dataprep_file.log
            exit 1
        fi
    else
        echo "[ dataprep - file ] HTTP status is not 200. Received status was $HTTP_STATUS"
        docker logs test-comps-dataprep-elasticsearch >> ${LOG_PATH}/dataprep_file.log
        exit 1
    fi

    # test /v1/dataprep/delete_file
    URL="http://${ip_address}:$dataprep_service_port/v1/dataprep/delete_file"
    HTTP_STATUS=$(curl -s -o /dev/null -w "%{http_code}" -X POST -d '{"file_path": "dataprep_file.txt"}' -H 'Content-Type: application/json' "$URL")
    if [ "$HTTP_STATUS" -eq 200 ]; then
        echo "[ dataprep - del ] HTTP status is 200."
        docker logs test-comps-dataprep-elasticsearch >> ${LOG_PATH}/dataprep_del.log
    else
        echo "[ dataprep - del ] HTTP status is not 200. Received status was $HTTP_STATUS"
        docker logs test-comps-dataprep-elasticsearch >> ${LOG_PATH}/dataprep_del.log
        exit 1
    fi
}

function stop_docker() {
    cid=$(docker ps -aq --filter "name=test-comps-vectorstore-elasticsearch*")
    if [[ ! -z "$cid" ]]; then docker stop $cid && docker rm $cid && sleep 1s; fi

    cid=$(docker ps -aq --filter "name=test-comps-dataprep-elasticsearch*")
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
