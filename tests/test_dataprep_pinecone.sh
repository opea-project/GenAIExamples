#!/bin/bash
# Copyright (C) 2024 Intel Corporation
# SPDX-License-Identifier: Apache-2.0

set -x

WORKPATH=$(dirname "$PWD")
ip_address=$(hostname -I | awk '{print $1}')
function build_docker_images() {
    cd $WORKPATH

    # build dataprep image for pinecone
    docker build --no-cache -t opea/dataprep-pinecone:comps --build-arg https_proxy=$https_proxy --build-arg http_proxy=$http_proxy -f $WORKPATH/comps/dataprep/pinecone/docker/Dockerfile .
    if $? ; then
        echo "opea/dataprep-pinecone built fail"
        exit 1
    else
        echo "opea/dataprep-pinecone built successful"
    fi
}

function start_service() {
    export PINECONE_API_KEY=$PINECONE_KEY
    export PINECONE_INDEX_NAME="test-index"
    export HUGGINGFACEHUB_API_TOKEN=$HF_TOKEN

    docker run -d --name="test-comps-dataprep-pinecone" -p 5039:6007 -p 5040:6008 -p 5041:6009 --ipc=host -e http_proxy=$http_proxy -e https_proxy=$https_proxy -e no_proxy=$no_proxy -e PINECONE_API_KEY=$PINECONE_API_KEY -e PINECONE_INDEX_NAME=$PINECONE_INDEX_NAME opea/dataprep-pinecone:comps

    sleep 1m
}

function validate_microservice() {
    URL="http://$ip_address:5039/v1/dataprep"
    echo 'The OPEA platform includes: Detailed framework of composable building blocks for state-of-the-art generative AI systems including LLMs, data stores, and prompt engines' > ./dataprep_file.txt
    result=$(curl --noproxy $ip_address --location --request POST \
      --form 'files=@./dataprep_file.txt' $URL)
    if [[ $result == *"200"* ]]; then
        echo "Result correct."
    else
        echo "Result wrong. Received was $result"
        docker logs test-comps-dataprep-pinecone
        exit 1
    fi
    DELETE_URL="http://$ip_address:5041/v1/dataprep/delete_file"
    result=$(curl --noproxy $ip_address --location --request POST \
      -d '{"file_path": "all"}' -H 'Content-Type: application/json' $DELETE_URL)
    if [[ $result == *"true"* ]]; then
        echo "Result correct."
    else
        echo "Result wrong. Received was $result"
        docker logs test-comps-dataprep-pinecone
        exit 1
    fi
}

function stop_docker() {
    cid=$(docker ps -aq --filter "name=vectorstore-pinecone*")
    if [[ ! -z "$cid" ]]; then docker stop $cid && docker rm $cid && sleep 1s; fi

    cid=$(docker ps -aq --filter "name=test-comps-dataprep-pinecone*")
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
