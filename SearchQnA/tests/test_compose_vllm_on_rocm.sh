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
export MODEL_PATH=${model_cache:-"./data"}

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
    service_list="searchqna searchqna-ui embedding web-retriever reranking llm-textgen vllm-rocm nginx"
    docker compose -f build.yaml build ${service_list} --no-cache > ${LOG_PATH}/docker_image_build.log

    docker images && sleep 3s
}

function start_services() {
    cd $WORKPATH/docker_compose/amd/gpu/rocm/

    export HOST_IP=${ip_address}
    # export SEARCH_BACKEND_SERVICE_PORT=3008
    source ./set_env_vllm.sh

    sed -i "s/backend_address/$ip_address/g" $WORKPATH/ui/svelte/.env

    # Start Docker Containers
    docker compose -f compose_vllm.yaml up -d > ${LOG_PATH}/start_services_with_compose.log
    n=0
    until [[ "$n" -ge 100 ]]; do
        docker logs search-vllm-service >& $LOG_PATH/search-vllm-service_start.log
        if grep -q "Application startup complete" $LOG_PATH/search-vllm-service_start.log; then
            break
        fi
        sleep 10s
        n=$((n+1))
    done
}


function validate_megaservice() {
    result=$(http_proxy="" curl http://${HOST_IP}:${SEARCH_BACKEND_SERVICE_PORT}/v1/searchqna -XPOST -d '{"messages": "What is black myth wukong?", "stream": "False"}' -H 'Content-Type: application/json')
    echo $result

    if [[ $result == *"the"* ]]; then
        docker logs search-web-retriever-server
        docker logs search-backend-server
        echo "Result correct."
    else
        docker logs search-web-retriever-server
        docker logs search-backend-server
        echo "Result wrong."
        exit 1
    fi

}

function stop_docker() {
    cd $WORKPATH/docker_compose/amd/gpu/rocm/
    docker compose -f compose_vllm.yaml stop && docker compose -f compose_vllm.yaml rm -f
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
