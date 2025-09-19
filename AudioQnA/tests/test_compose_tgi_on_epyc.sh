#!/bin/bash
# Copyright (C) 2025 Advanced Micro Devices, Inc.
# Copyright (C) 2025 Intel Corporation
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
mkdir -p "$WORKPATH/tests/logs"
LOG_PATH="$WORKPATH/tests/logs"
ip_address=$(hostname -I | awk '{print $1}')

function build_docker_images() {
    echo $WORKPATH
    opea_branch=${opea_branch:-"main"}

    cd $WORKPATH/docker_image_build
    git clone --depth 1 --branch ${opea_branch} https://github.com/opea-project/GenAIComps.git
    pushd GenAIComps
    echo "GenAIComps test commit is $(git rev-parse HEAD)"
    docker build --no-cache -t ${REGISTRY}/comps-base:${TAG} --build-arg https_proxy=$https_proxy --build-arg http_proxy=$http_proxy -f Dockerfile .
    popd && sleep 1s

    echo "Build all the images with --no-cache, check docker_image_build.log for details..."
    service_list="audioqna audioqna-ui whisper speecht5"
    docker compose -f build.yaml build ${service_list} --no-cache > ${LOG_PATH}/docker_image_build.log

    docker images && sleep 1s
}

function start_services() {
    echo $WORKPATH
    cd $WORKPATH/docker_compose/amd/cpu/epyc/
    export no_proxy="localhost,127.0.0.1,$ip_address"
    source set_env.sh
    # Start Docker Containers
    docker compose -f compose_tgi.yaml up -d > ${LOG_PATH}/start_services_with_compose.log
    n=0
    until [[ "$n" -ge 200 ]]; do
       docker logs tgi-service > $LOG_PATH/tgi_service_start.log
       if grep -q Connected $LOG_PATH/tgi_service_start.log; then
           break
       fi
       sleep 5s
       n=$((n+1))
    done
}


function validate_megaservice() {
    sleep 20
    response=$(http_proxy="" curl http://${ip_address}:3008/v1/audioqna -XPOST -d '{"audio": "UklGRigAAABXQVZFZm10IBIAAAABAAEARKwAAIhYAQACABAAAABkYXRhAgAAAAEA", "max_tokens":64}' -H 'Content-Type: application/json')
    # always print the log
    docker logs whisper-service > $LOG_PATH/whisper-service.log
    docker logs speecht5-service > $LOG_PATH/tts-service.log
    docker logs tgi-service > $LOG_PATH/tgi-service.log
    docker logs audioqna-epyc-backend-server > $LOG_PATH/audioqna-epyc-backend-server.log
    echo "$response" | sed 's/^"//;s/"$//' | base64 -d > speech.mp3

    if [[ $(file speech.mp3) == *"RIFF"* ]]; then
        echo "Result correct."
    else
        echo "Result wrong."
        exit 1
    fi

}


function stop_docker() {
    cd $WORKPATH/docker_compose/amd/cpu/epyc/
    docker compose -f compose_tgi.yaml stop && docker compose rm -f
}

function main() {

    echo "::group::stop_docker"
    stop_docker
    docker system prune -f
    echo "::endgroup::"
    sleep 3s

    echo "::group::build_docker_images"
    if [[ "$IMAGE_REPO" == "opea" ]]; then build_docker_images; fi
    echo "::endgroup::"
    sleep 3s

    echo "::group::start_services"
    start_services
    echo "::endgroup::"
    sleep 60s

    echo "::group::validate_megaservice"
    validate_megaservice
    echo "::endgroup::"
    sleep 3s

    echo "::group::stop_docker"
    stop_docker
    docker system prune -f
    echo "::endgroup::"

}

main
