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
    docker build --no-cache -t opea/langchain-mosec:comps --build-arg http_proxy=$http_proxy --build-arg https_proxy=$https_proxy -f comps/embeddings/langchain-mosec/mosec-docker/Dockerfile .
    if $? ; then
        echo "opea/langchain-mosec built fail"
        exit 1
    else
        echo "opea/langchain-mosec built successful"
    fi
    # dataprep milvus image
    docker build --no-cache -t opea/dataprep-milvus:comps --build-arg https_proxy=$https_proxy --build-arg http_proxy=$http_proxy -f comps/dataprep/milvus/docker/Dockerfile .
    if $? ; then
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
    wget https://raw.githubusercontent.com/milvus-io/milvus/v2.4.6/configs/milvus.yaml
    wget https://github.com/milvus-io/milvus/releases/download/v2.4.6/milvus-standalone-docker-compose.yml -O docker-compose.yml
    sed '/- \${DOCKER_VOLUME_DIRECTORY:-\.}\/volumes\/milvus:\/var\/lib\/milvus/a \ \ \ \ \ \ - \${DOCKER_VOLUME_DIRECTORY:-\.}\/milvus.yaml:\/milvus\/configs\/milvus.yaml' -i docker-compose.yml
    docker compose up -d

    # set service ports
    mosec_embedding_port=5021
    dataprep_service_port=5022
    dataprep_file_service_port=5023
    dataprep_del_service_port=5024

    # start mosec embedding service
    docker run -d --name="test-comps-dataprep-milvus-mosec-server" -p $mosec_embedding_port:8000 -e http_proxy=$http_proxy -e https_proxy=$https_proxy opea/langchain-mosec:comps

    # start dataprep service
    MOSEC_EMBEDDING_ENDPOINT="http://${ip_address}:${mosec_embedding_port}"
    MILVUS=${ip_address}
    docker run -d --name="test-comps-dataprep-milvus-server" -p ${dataprep_service_port}:6010 -p ${dataprep_file_service_port}:6011 -p ${dataprep_del_service_port}:6012 -e http_proxy=$http_proxy -e https_proxy=$https_proxy -e no_proxy=$no_proxy -e MOSEC_EMBEDDING_ENDPOINT=${MOSEC_EMBEDDING_ENDPOINT} -e MILVUS=${MILVUS} --ipc=host opea/dataprep-milvus:comps
    sleep 1m
}

function validate_microservice() {
    cd $LOG_PATH

    # test /v1/dataprep
    dataprep_service_port=5022
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
            docker logs test-comps-dataprep-milvus-server >> ${LOG_PATH}/dataprep.log
            exit 1
        fi
    else
        echo "[ dataprep ] HTTP status is not 200. Received status was $HTTP_STATUS"
        docker logs test-comps-dataprep-milvus-server >> ${LOG_PATH}/dataprep.log
        exit 1
    fi

    # test /v1/dataprep/get_file
    dataprep_file_service_port=5023
    URL="http://${ip_address}:$dataprep_file_service_port/v1/dataprep/get_file"
    HTTP_STATUS=$(curl -s -o /dev/null -w "%{http_code}" -X POST -H 'Content-Type: application/json' "$URL")
    if [ "$HTTP_STATUS" -eq 200 ]; then
        echo "[ dataprep - file ] HTTP status is 200. Checking content..."
        local CONTENT=$(curl -s -X POST -H 'Content-Type: application/json' "$URL" | tee ${LOG_PATH}/dataprep_file.log)

        if echo "$CONTENT" | grep -q '{"name":'; then
            echo "[ dataprep - file ] Content is as expected."
        else
            echo "[ dataprep - file ] Content does not match the expected result: $CONTENT"
            docker logs test-comps-dataprep-milvus-server >> ${LOG_PATH}/dataprep_file.log
            exit 1
        fi
    else
        echo "[ dataprep - file ] HTTP status is not 200. Received status was $HTTP_STATUS"
        docker logs test-comps-dataprep-milvus-server >> ${LOG_PATH}/dataprep_file.log
        exit 1
    fi

    # test /v1/dataprep/delete_file
    dataprep_del_service_port=5024
    URL="http://${ip_address}:$dataprep_del_service_port/v1/dataprep/delete_file"
    HTTP_STATUS=$(curl -s -o /dev/null -w "%{http_code}" -X POST -d '{"file_path": "dataprep_file.txt"}' -H 'Content-Type: application/json' "$URL")
    if [ "$HTTP_STATUS" -eq 200 ]; then
        echo "[ dataprep - del ] HTTP status is 200."
        docker logs test-comps-dataprep-milvus-server >> ${LOG_PATH}/dataprep_del.log
    else
        echo "[ dataprep - del ] HTTP status is not 200. Received status was $HTTP_STATUS"
        docker logs test-comps-dataprep-milvus-server >> ${LOG_PATH}/dataprep_del.log
        exit 1
    fi
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
