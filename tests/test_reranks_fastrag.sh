#!/bin/bash
# Copyright (C) 2024 Intel Corporation
# SPDX-License-Identifier: Apache-2.0

set -x

WORKPATH=$(dirname "$PWD")
ip_address=$(hostname -I | awk '{print $1}')
function build_docker_images() {
    cd $WORKPATH
    docker build --no-cache --build-arg https_proxy=$https_proxy --build-arg http_proxy=$http_proxy -t opea/reranking-fastrag:comps -f comps/reranks/fastrag/docker/Dockerfile .
    if [ $? -ne 0 ]; then
        echo "opea/reranking-fastrag built fail"
        exit 1
    else
        echo "opea/reranking-fastrag built successful"
    fi
}

function start_service() {
    export EMBED_MODEL="Intel/bge-small-en-v1.5-rag-int8-static"
    fastrag_service_port=5020
    unset http_proxy
    docker run -d --name="test-comps-reranking-fastrag-server" -p ${fastrag_service_port}:8000 --ipc=host -e http_proxy=$http_proxy -e https_proxy=$https_proxy -e EMBED_MODEL=$EMBED_MODEL opea/reranking-fastrag:comps
    sleep 3m
}

function validate_microservice() {
    fastrag_service_port=5020
    result=$(http_proxy="" curl http://${ip_address}:${fastrag_service_port}/v1/reranking\
        -X POST \
        -d '{"initial_query":"What is Deep Learning?", "retrieved_docs": [{"text":"Deep Learning is not..."}, {"text":"Deep learning is..."}]}' \
        -H 'Content-Type: application/json')
    if [[ $result == *"reranked_docs"* ]]; then
        echo "Result correct."
    else
        echo "Result wrong. Received was $result"
        docker logs test-comps-reranking-fastrag-server
        exit 1
    fi
}

function stop_docker() {
    cid=$(docker ps -aq --filter "name=test-comps-rerank*")
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
