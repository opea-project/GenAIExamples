#!/bin/bash
# Copyright (C) 2024 Intel Corporation
# SPDX-License-Identifier: Apache-2.0

set -xe

WORKPATH=$(dirname "$PWD")
ip_address=$(hostname -I | awk '{print $1}')
function build_docker_images() {
    cd $WORKPATH

    # piull pgvector image
    docker pull pgvector/pgvector:0.7.0-pg16

    # build dataprep image for pgvector
    docker build -t opea/dataprep-pgvector:latest --build-arg https_proxy=$https_proxy --build-arg http_proxy=$http_proxy -f $WORKPATH/comps/dataprep/pgvector/langchain/docker/Dockerfile .
}

function start_service() {
    export POSTGRES_USER=testuser
    export POSTGRES_PASSWORD=testpwd
    export POSTGRES_DB=vectordb

    docker run --name vectorstore-postgres -e POSTGRES_USER=${POSTGRES_USER} -e POSTGRES_HOST_AUTH_METHOD=trust -e POSTGRES_DB=${POSTGRES_DB} -e POSTGRES_PASSWORD=${POSTGRES_PASSWORD} -p 5432:5432 -d -v $WORKPATH/comps/vectorstores/langchain/pgvector/init.sql:/docker-entrypoint-initdb.d/init.sql pgvector/pgvector:0.7.0-pg16

    sleep 10s

    docker run -d --name="dataprep-pgvector" -p 6007:6007 --ipc=host -e http_proxy=$http_proxy -e https_proxy=$https_proxy -e PG_CONNECTION_STRING=postgresql+psycopg2://${POSTGRES_USER}:${POSTGRES_PASSWORD}@$ip_address:5432/${POSTGRES_DB} opea/dataprep-pgvector:latest

    sleep 3m
}

function validate_microservice() {
    URL="http://$ip_address:6007/v1/dataprep"
    echo 'The OPEA platform includes: Detailed framework of composable building blocks for state-of-the-art generative AI systems including LLMs, data stores, and prompt engines' > ./dataprep_file.txt
    curl --noproxy $ip_address --location --request POST \
      --form 'files=@./dataprep_file.txt' $URL
}

function stop_docker() {
    cid=$(docker ps -aq --filter "name=vectorstore-postgres*")
    if [[ ! -z "$cid" ]]; then docker stop $cid && docker rm $cid && sleep 1s; fi

    cid=$(docker ps -aq --filter "name=dataprep-pgvector*")
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
