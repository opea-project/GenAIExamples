#!/bin/bash
# Copyright (C) 2024 Intel Corporation
# SPDX-License-Identifier: Apache-2.0

set -xe

WORKPATH=$(dirname "$PWD")
ip_address=$(hostname -I | awk '{print $1}')
function build_docker_images() {
    cd $WORKPATH

    # build dataprep image for pinecone
    docker build -t opea/dataprep-pinecone:latest --build-arg https_proxy=$https_proxy --build-arg http_proxy=$http_proxy -f $WORKPATH/comps/dataprep/pinecone/docker/Dockerfile .
}

function start_service() {
    export PINECONE_API_KEY=$PINECONE_KEY
    export PINECONE_INDEX_NAME="test-index"
    export HUGGINGFACEHUB_API_TOKEN=$HF_TOKEN

    docker run -d --name="dataprep-pinecone" -p 6007:6007 -p 6008:6008 -p 6009:6009 --ipc=host -e http_proxy=$http_proxy -e https_proxy=$https_proxy -e no_proxy=$no_proxy -e PINECONE_API_KEY=$PINECONE_API_KEY -e PINECONE_INDEX_NAME=$PINECONE_INDEX_NAME opea/dataprep-pinecone:latest

    sleep 1m
}

function validate_microservice() {
    URL="http://$ip_address:6007/v1/dataprep"
    echo 'The OPEA platform includes: Detailed framework of composable building blocks for state-of-the-art generative AI systems including LLMs, data stores, and prompt engines' > ./dataprep_file.txt
    curl --noproxy $ip_address --location --request POST \
      --form 'files=@./dataprep_file.txt' $URL

    DELETE_URL="http://$ip_address:6009/v1/dataprep/delete_file"
    curl --noproxy $ip_address --location --request POST \
      -d '{"file_path": "all"}' -H 'Content-Type: application/json' $DELETE_URL
}

function stop_docker() {
    cid=$(docker ps -aq --filter "name=vectorstore-pinecone*")
    if [[ ! -z "$cid" ]]; then docker stop $cid && docker rm $cid && sleep 1s; fi

    cid=$(docker ps -aq --filter "name=dataprep-pinecone*")
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
