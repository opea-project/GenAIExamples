#!/bin/bash
# Copyright (C) 2024 Intel Corporation
# SPDX-License-Identifier: Apache-2.0

set -xe

WORKPATH=$(dirname "$PWD")
ip_address=$(hostname -I | awk '{print $1}')

function build_docker_images() {
    cd $WORKPATH
    docker build --no-cache \
          -t opea/reranking:comps \
          --build-arg https_proxy=$https_proxy \
          --build-arg http_proxy=$http_proxy \
          --build-arg SERVICE=videoqna \
          -f comps/rerankings/src/Dockerfile .
    if [ $? -ne 0 ]; then
        echo "opea/reranking built fail"
        exit 1
    else
        echo "opea/reranking built successful"
    fi
}

function start_service() {
    docker run -d --name "test-comps-reranking-server" \
        -p 5037:8000 \
        --ipc=host \
        -e no_proxy=${no_proxy} \
        -e http_proxy=${http_proxy} \
        -e https_proxy=${https_proxy} \
        -e CHUNK_DURATION=${CHUNK_DURATION} \
        -e RERANK_COMPONENT_NAME="OPEA_VIDEO_RERANKING" \
        -e FILE_SERVER_ENDPOINT=${FILE_SERVER_ENDPOINT} \
        opea/reranking:comps


    until docker logs test-comps-reranking-server 2>&1 | grep -q "Uvicorn running on"; do
        sleep 2
    done
}

function validate_microservice() {
    result=$(\
    http_proxy="" \
    curl -X 'POST' \
        "http://${ip_address}:5037/v1/reranking" \
        -H 'accept: application/json' \
        -H 'Content-Type: application/json' \
        -d '{
        "retrieved_docs": [
            {"doc": [{"text": "this is the retrieved text"}]}
        ],
        "initial_query": "this is the query",
        "top_n": 1,
        "metadata": [
            {"other_key": "value", "video":"top_video_name", "timestamp":"20"},
            {"other_key": "value", "video":"second_video_name", "timestamp":"40"},
            {"other_key": "value", "video":"top_video_name", "timestamp":"20"}
        ]
        }')
    if [[ $result == *"this is the query"* ]]; then
        echo "Result correct for the positive case."
    else
        echo "Result wrong for the positive case. Received was $result"
        exit 1
    fi

    # Add test for negative case
    result=$(\
    http_proxy="" \
    curl -X 'POST' \
        "http://${ip_address}:5037/v1/reranking" \
        -H 'accept: application/json' \
        -H 'Content-Type: application/json' \
        -d '{
        "retrieved_docs": [
            {"doc": [{"text": "this is the retrieved text"}]}
        ],
        "initial_query": "this is the query",
        "top_n": 1,
        "metadata": [{"other_key": "value", "video":"top_video_name_bad_format.avi", "timestamp":"20"}]}')
    if [[ $result == *"Invalid file extension"* ]]; then
        echo "Result correct for the negative case."
    else
        echo "Result wrong for the negative case. Received was $result"
        exit 1
    fi
}

function stop_docker() {
    cid=$(docker ps -aq --filter "name=test-comps-reranking*")
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
