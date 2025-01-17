#!/bin/bash
# Copyright (C) 2024 Intel Corporation
# SPDX-License-Identifier: Apache-2.0

set -x

WORKPATH=$(dirname "$PWD")
LOG_PATH="$WORKPATH/tests"
ip_address=$(hostname -I | awk '{print $1}')
function build_docker_images() {
    cd $WORKPATH
    docker build --no-cache -t opea/retriever-pgvector:comps --build-arg https_proxy=$https_proxy --build-arg http_proxy=$http_proxy -f comps/retrievers/src/Dockerfile .
    if [ $? -ne 0 ]; then
        echo "opea/retriever-pgvector built fail"
        exit 1
    else
        echo "opea/retriever-pgvector built successful"
    fi
}

function start_service() {
    # pgvector
    export POSTGRES_USER=testuser
    export POSTGRES_PASSWORD=testpwd
    export POSTGRES_DB=vectordb

    pgvector_port=5079
    docker run --name test-comps-retriever-pgvector-vectorstore -e POSTGRES_USER=${POSTGRES_USER} -e POSTGRES_HOST_AUTH_METHOD=trust -e POSTGRES_DB=${POSTGRES_DB} -e POSTGRES_PASSWORD=${POSTGRES_PASSWORD} -d -v $WORKPATH/comps/third_parties/pgvector/src/init.sql:/docker-entrypoint-initdb.d/init.sql -p $pgvector_port:5432 pgvector/pgvector:0.7.0-pg16
    sleep 10s

    # pgvector retriever
    docker run -d --name="test-comps-retriever-pgvector-ms" -p 5003:7000 --ipc=host -e http_proxy=$http_proxy -e https_proxy=$https_proxy -e PG_CONNECTION_STRING=postgresql+psycopg2://${POSTGRES_USER}:${POSTGRES_PASSWORD}@$ip_address:$pgvector_port/${POSTGRES_DB} -e RETRIEVER_COMPONENT_NAME="OPEA_RETRIEVER_PGVECTOR" -e LOGFLAG=true opea/retriever-pgvector:comps
    sleep 1m
}

function validate_microservice() {
    retriever_port=5003
    test_embedding=$(python -c "import random; embedding = [random.uniform(-1, 1) for _ in range(768)]; print(embedding)")


    result=$(http_proxy=''
    curl http://${ip_address}:$retriever_port/v1/retrieval \
        -X POST \
        -d "{\"text\":\"test\",\"embedding\":${test_embedding}}" \
        -H 'Content-Type: application/json')
    if [[ $result == *"retrieved_docs"* ]]; then
        echo "Result correct."
    else
        echo "Result wrong. Received was $result"
        docker logs test-comps-retriever-pgvector-vectorstore >> ${LOG_PATH}/vectorstore.log
        docker logs test-comps-retriever-pgvector-ms >> ${LOG_PATH}/retriever-pgvector.log
        exit 1
    fi
}

function stop_docker() {
    cid_retrievers=$(docker ps -aq --filter "name=test-comps-retriever-pgvector*")
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
