#!/bin/bash
# Copyright (C) 2024 Intel Corporation
# SPDX-License-Identifier: Apache-2.0

set -x

WORKPATH=$(dirname "$PWD")
LOG_PATH="$WORKPATH/tests"
ip_address=$(hostname -I | awk '{print $1}')

function build_docker_images() {
    cd $WORKPATH
    docker build --no-cache -t opea/retriever-elasticsearch:comps --build-arg https_proxy=$https_proxy --build-arg http_proxy=$http_proxy -f comps/retrievers/elasticsearch/langchain/Dockerfile .
    if [ $? -ne 0 ]; then
        echo "opea/retriever-elasticsearch built fail"
        exit 1
    else
        echo "opea/retriever-elasticsearch built successful"
    fi
}

function start_service() {
    # elasticsearch
    elasticsearch_port=9200
    docker run -d --name "test-comps-retriever-elasticsearch-vectorstore" -e ES_JAVA_OPTS="-Xms1g -Xmx1g" -e "discovery.type=single-node" -e "xpack.security.enabled=false"  -p $elasticsearch_port:9200 -p 9300:9300 docker.elastic.co/elasticsearch/elasticsearch:8.16.0
    export ES_CONNECTION_STRING="http://${ip_address}:${elasticsearch_port}"
    sleep 10s

    # elasticsearch retriever
    INDEX_NAME="test-elasticsearch"
    retriever_port=7000
    docker run -d --name="test-comps-retriever-elasticsearch-ms" -p $retriever_port:7000 --ipc=host -e http_proxy=$http_proxy -e https_proxy=$https_proxy -e ES_CONNECTION_STRING=$ES_CONNECTION_STRING -e INDEX_NAME=$INDEX_NAME opea/retriever-elasticsearch:comps
    sleep 15s

    bash ./tests/utils/wait-for-it.sh ${ip_address}:$retriever_port -s -t 100 -- echo "Retriever up"
    RETRIEVER_UP=$?
    if [ ${RETRIEVER_UP} -ne 0 ]; then
        echo "Could not start Retriever."
        return 1
    fi

    sleep 5s
    bash ./tests/utils/wait-for-it.sh ${ip_address}:$retriever_port -s -t 1 -- echo "Retriever still up"
    RETRIEVER_UP=$?
    if [ ${RETRIEVER_UP} -ne 0 ]; then
        echo "Retriever crashed."
        return 1
    fi
}

function validate_microservice() {
    retriever_port=7000
    test_embedding=$(python3 -c "import random; embedding = [random.uniform(-1, 1) for _ in range(768)]; print(embedding)")


    result=$(http_proxy=''
    curl http://${ip_address}:$retriever_port/v1/retrieval \
        -X POST \
        -d "{\"text\":\"test\",\"embedding\":${test_embedding}}" \
        -H 'Content-Type: application/json')
    if [[ $result == *"retrieved_docs"* ]]; then
        echo "Result correct."
    else
        echo "Result wrong. Received was $result"
        docker logs test-comps-retriever-elasticsearch-vectorstore >> ${LOG_PATH}/vectorstore.log
        docker logs test-comps-retriever-elasticsearch-tei-endpoint >> ${LOG_PATH}/tei-endpoint.log
        docker logs test-comps-retriever-elasticsearch-ms >> ${LOG_PATH}/retriever-elasticsearch.log
        exit 1
    fi
}

function stop_docker() {
    cid_retrievers=$(docker ps -aq --filter "name=test-comps-retriever-elasticsearch*")
    if [[ ! -z "$cid_retrievers" ]]; then
        docker stop $cid_retrievers && docker rm $cid_retrievers && sleep 1s
    fi
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
