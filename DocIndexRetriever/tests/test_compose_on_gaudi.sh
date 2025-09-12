#!/bin/bash
# Copyright (C) 2024 Intel Corporation
# SPDX-License-Identifier: Apache-2.0

set -e
IMAGE_REPO=${IMAGE_REPO:-"opea"}
IMAGE_TAG=${IMAGE_TAG:-"latest"}
echo "REGISTRY=IMAGE_REPO=${IMAGE_REPO}"
echo "TAG=IMAGE_TAG=${IMAGE_TAG}"
export REGISTRY=${IMAGE_REPO}
export TAG=${IMAGE_TAG}
export MODEL_CACHE=${model_cache:-"./data"}

WORKPATH=$(dirname "$PWD")
LOG_PATH="$WORKPATH/tests"
ip_address=$(hostname -I | awk '{print $1}')

function build_docker_images() {
    echo "Building Docker Images...."
    cd $WORKPATH/docker_image_build
    if [ ! -d "GenAIComps" ] ; then
        git clone --single-branch --branch "${opea_branch:-"main"}" https://github.com/opea-project/GenAIComps.git
    fi
    pushd GenAIComps
    echo "GenAIComps test commit is $(git rev-parse HEAD)"
    docker build --no-cache -t ${REGISTRY}/comps-base:${TAG} --build-arg https_proxy=$https_proxy --build-arg http_proxy=$http_proxy -f Dockerfile .
    popd && sleep 1s

    echo "Build all the images with --no-cache, check docker_image_build.log for details..."
    docker compose -f build.yaml build --no-cache > ${LOG_PATH}/docker_image_build.log

    docker images && sleep 1s
}

function start_services() {
    echo "Starting Docker Services...."
    cd $WORKPATH/docker_compose/intel/hpu/gaudi
    export no_proxy="localhost,127.0.0.1,$ip_address"
    source ./set_env.sh

    # Start Docker Containers
    docker compose up -d
    sleep 1m
    echo "Docker services started!"
}

function validate() {
    local CONTENT="$1"
    local EXPECTED_RESULT="$2"
    local SERVICE_NAME="$3"

    if echo "$CONTENT" | grep -q "$EXPECTED_RESULT"; then
        echo "[ $SERVICE_NAME ] Content is as expected: $CONTENT"
        echo 0
    else
        echo "[ $SERVICE_NAME ] Content does not match the expected result: $CONTENT"
        echo 1
    fi
}

function validate_megaservice() {
    echo "=========Ingest data=================="
    local CONTENT=$(curl -X POST "http://${ip_address}:6007/v1/dataprep/ingest" \
     -H "Content-Type: multipart/form-data" \
     -F 'link_list=["https://opea.dev"]')
    local EXIT_CODE=$(validate "$CONTENT" "Data preparation succeeded" "dataprep-redis-service-gaudi")
    echo "$EXIT_CODE"
    local EXIT_CODE="${EXIT_CODE:0-1}"
    echo "return value is $EXIT_CODE"
    if [ "$EXIT_CODE" == "1" ]; then
        docker logs dataprep-redis-server | tee -a ${LOG_PATH}/dataprep-redis-service-gaudi.log
        return 1
    fi

    # Curl the Mega Service
    echo "==============Testing retriever service================="
    local CONTENT=$(http_proxy="" curl http://${ip_address}:8889/v1/retrievaltool -X POST -H "Content-Type: application/json" -d '{
     "messages": "Explain the OPEA project?"
    }')

    local EXIT_CODE=$(validate "$CONTENT" "OPEA" "doc-index-retriever-service-gaudi")

    echo "$EXIT_CODE"
    local EXIT_CODE="${EXIT_CODE:0-1}"
    echo "return value is $EXIT_CODE"
    if [ "$EXIT_CODE" == "1" ]; then
        docker logs tei-embedding-gaudi-server | tee -a ${LOG_PATH}/doc-index-retriever-service-gaudi.log
        docker logs retriever-redis-server | tee -a ${LOG_PATH}/doc-index-retriever-service-gaudi.log
        docker logs reranking-tei-gaudi-server | tee -a ${LOG_PATH}/doc-index-retriever-service-gaudi.log
        docker logs doc-index-retriever-server | tee -a ${LOG_PATH}/doc-index-retriever-service-gaudi.log
        exit 1
    fi

}

function stop_docker() {
    cd $WORKPATH/docker_compose/intel/hpu/gaudi
    container_list=$(cat compose.yaml | grep container_name | cut -d':' -f2)
    for container_name in $container_list; do
        cid=$(docker ps -aq --filter "name=$container_name")
        echo "Stopping container $container_name"
        if [[ ! -z "$cid" ]]; then docker rm $cid -f && sleep 1s; fi
    done
}

function main() {

    echo "::group::stop_docker"
    stop_docker
    echo "::endgroup::"

    echo "::group::build_docker_images"
    if [[ "$IMAGE_REPO" == "opea" ]]; then build_docker_images; fi
    echo "::endgroup::"

    echo "::group::start_services"
    start_services
    echo "::endgroup::"

    echo "::group::validate_megaservice"
    validate_megaservice
    echo "::endgroup::"

    echo "::group::stop_docker"
    stop_docker
    echo "::endgroup::"

    docker system prune -f

}

main
