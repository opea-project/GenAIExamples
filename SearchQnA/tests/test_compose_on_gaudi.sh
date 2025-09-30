#!/bin/bash
# Copyright (C) 2024 Intel Corporation
# SPDX-License-Identifier: Apache-2.0

set -xe
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
    opea_branch=${opea_branch:-"main"}
    cd $WORKPATH/docker_image_build
    git clone --depth 1 --branch ${opea_branch} https://github.com/opea-project/GenAIComps.git
    pushd GenAIComps
    echo "GenAIComps test commit is $(git rev-parse HEAD)"
    docker build --no-cache -t ${REGISTRY}/comps-base:${TAG} --build-arg https_proxy=$https_proxy --build-arg http_proxy=$http_proxy -f Dockerfile .
    popd && sleep 1s

    echo "Build all the images with --no-cache, check docker_image_build.log for details..."
    service_list="searchqna searchqna-ui embedding web-retriever reranking llm-textgen nginx"
    docker compose -f build.yaml build ${service_list} --no-cache > ${LOG_PATH}/docker_image_build.log

    docker images && sleep 1s
}

function start_services() {

    cd $WORKPATH/docker_compose/intel/
    export RERANK_TYPE="tei"
    export BACKEND_SERVICE_ENDPOINT="http://${ip_address}:3008/v1/searchqna"
    export host_ip=${ip_address}
    export LOGFLAG=true
    export no_proxy="localhost,127.0.0.1,$ip_address"
    source ./set_env.sh
    cd hpu/gaudi

    sed -i "s/backend_address/$ip_address/g" $WORKPATH/ui/svelte/.env

    # Start Docker Containers
    docker compose up -d > ${LOG_PATH}/start_services_with_compose.log

    sleep 10s
}


function validate_megaservice() {
    result=$(curl http://${ip_address}:3008/v1/searchqna -X POST -d '{"messages": "What is the capital of China?", "stream": "False"}' -H 'Content-Type: application/json')
    echo $result

    docker logs web-retriever-server > ${LOG_PATH}/web-retriever-server.log
    docker logs searchqna-gaudi-backend-server > ${LOG_PATH}/searchqna-gaudi-backend-server.log
    docker logs tei-embedding-gaudi-server > ${LOG_PATH}/tei-embedding-gaudi-server.log
    docker logs embedding-gaudi-server > ${LOG_PATH}/embedding-gaudi-server.log

    if [[ $result == *"capital"* ]]; then
        echo "Result correct."
    else
        echo "Result wrong."
        exit 1
    fi

}

function stop_docker() {
    cd $WORKPATH/docker_compose/intel/hpu/gaudi
    docker compose stop && docker compose rm -f
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
