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
    opea_branch=${opea_branch:-"main"}

    cd $WORKPATH/docker_image_build
    git clone --depth 1 --branch ${opea_branch} https://github.com/opea-project/GenAIComps.git
    pushd GenAIComps
    echo "GenAIComps test commit is $(git rev-parse HEAD)"
    docker build --no-cache -t ${REGISTRY}/comps-base:${TAG} --build-arg https_proxy=$https_proxy --build-arg http_proxy=$http_proxy -f Dockerfile .
    popd && sleep 1s

    git clone https://github.com/vllm-project/vllm.git
    cd ./vllm/
    VLLM_VER=v0.9.0
    echo "Check out vLLM tag ${VLLM_VER}"
    git checkout ${VLLM_VER} &> /dev/null && cd ../

    echo "Build all the images with --no-cache, check docker_image_build.log for details..."
    service_list="audioqna audioqna-ui whisper speecht5 vllm"
    docker compose -f build.yaml build ${service_list} --no-cache > ${LOG_PATH}/docker_image_build.log

    docker images && sleep 1s
}

function start_services() {
    cd $WORKPATH/docker_compose/intel/cpu/xeon/
    export host_ip=${ip_address}
    source set_env.sh
    # sed -i "s/backend_address/$ip_address/g" $WORKPATH/ui/svelte/.env

    # Start Docker Containers
    docker compose up -d > ${LOG_PATH}/start_services_with_compose.log
    n=0
    until [[ "$n" -ge 200 ]]; do
       docker logs vllm-service > $LOG_PATH/vllm_service_start.log 2>&1
       if grep -q complete $LOG_PATH/vllm_service_start.log; then
           break
       fi
       sleep 5s
       n=$((n+1))
    done
}


function validate_megaservice() {
    response=$(http_proxy="" curl http://${ip_address}:3008/v1/audioqna -XPOST -d '{"audio": "UklGRigAAABXQVZFZm10IBIAAAABAAEARKwAAIhYAQACABAAAABkYXRhAgAAAAEA", "max_tokens":64}' -H 'Content-Type: application/json')
    # always print the log
    docker logs whisper-service > $LOG_PATH/whisper-service.log
    docker logs speecht5-service > $LOG_PATH/tts-service.log
    docker logs vllm-service > $LOG_PATH/vllm-service.log
    docker logs audioqna-xeon-backend-server > $LOG_PATH/audioqna-xeon-backend-server.log
    echo "$response" | sed 's/^"//;s/"$//' | base64 -d > speech.mp3

    if [[ $(file speech.mp3) == *"RIFF"* ]]; then
        echo "Result correct."
    else
        echo "Result wrong."
        exit 1
    fi

}

function stop_docker() {
    cd $WORKPATH/docker_compose/intel/cpu/xeon/
    docker compose -f compose.yaml stop && docker compose rm -f
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
    docker system prune -f
    echo "::endgroup::"

}

main
