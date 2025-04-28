#!/bin/bash
# Copyright (C) 2024 Advanced Micro Devices, Inc.
# SPDX-License-Identifier: Apache-2.0

set -xe
IMAGE_REPO=${IMAGE_REPO:-"opea"}
IMAGE_TAG=${IMAGE_TAG:-"latest"}
echo "REGISTRY=IMAGE_REPO=${IMAGE_REPO}"
echo "TAG=IMAGE_TAG=${IMAGE_TAG}"
export REGISTRY=${IMAGE_REPO}
export TAG=${IMAGE_TAG}

WORKPATH=$(dirname "$PWD")
LOG_PATH="$WORKPATH/tests"
ip_address=$(hostname -I | awk '{print $1}')
export PATH="~/miniconda3/bin:$PATH"

function build_docker_images() {
    opea_branch=${opea_branch:-"main"}

    cd $WORKPATH/docker_image_build
    git clone --depth 1 --branch ${opea_branch} https://github.com/opea-project/GenAIComps.git
    pushd GenAIComps
    echo "GenAIComps test commit is $(git rev-parse HEAD)"
    docker build --no-cache -t ${REGISTRY}/comps-base:${TAG} --build-arg https_proxy=$https_proxy --build-arg http_proxy=$http_proxy -f Dockerfile .
    popd && sleep 1s

    echo "Build all the images with --no-cache, check docker_image_build.log for details..."
    service_list="audioqna audioqna-ui whisper speecht5 vllm-rocm"
    docker compose -f build.yaml build ${service_list} --no-cache > ${LOG_PATH}/docker_image_build.log
    docker images && sleep 3s
}

function start_services() {
    cd $WORKPATH/docker_compose/amd/gpu/rocm/

    export host_ip=${ip_address}
    export external_host_ip=${ip_address}
    export HUGGINGFACEHUB_API_TOKEN=${HUGGINGFACEHUB_API_TOKEN}
    export HF_CACHE_DIR="./data"
    export LLM_MODEL_ID="Intel/neural-chat-7b-v3-3"
    export VLLM_SERVICE_PORT="8081"

    export MEGA_SERVICE_HOST_IP=${host_ip}
    export WHISPER_SERVER_HOST_IP=${host_ip}
    export SPEECHT5_SERVER_HOST_IP=${host_ip}
    export LLM_SERVER_HOST_IP=${host_ip}

    export WHISPER_SERVER_PORT=7066
    export SPEECHT5_SERVER_PORT=7055
    export LLM_SERVER_PORT=${VLLM_SERVICE_PORT}
    export BACKEND_SERVICE_PORT=3008
    export FRONTEND_SERVICE_PORT=5173

    export BACKEND_SERVICE_ENDPOINT=http://${external_host_ip}:${BACKEND_SERVICE_PORT}/v1/audioqna

    sed -i "s/backend_address/$ip_address/g" $WORKPATH/ui/svelte/.env

    # Start Docker Containers
    docker compose -f compose_vllm.yaml up -d > ${LOG_PATH}/start_services_with_compose.log
    n=0
    until [[ "$n" -ge 200 ]]; do
       docker logs audioqna-vllm-service >& $LOG_PATH/vllm_service_start.log
       if grep -q "Application startup complete" $LOG_PATH/vllm_service_start.log; then
           break
       fi
       sleep 10s
       n=$((n+1))
    done
}
function validate_megaservice() {
    response=$(http_proxy="" curl http://${ip_address}:${BACKEND_SERVICE_PORT}/v1/audioqna -XPOST -d '{"audio": "UklGRigAAABXQVZFZm10IBIAAAABAAEARKwAAIhYAQACABAAAABkYXRhAgAAAAEA", "max_tokens":64}' -H 'Content-Type: application/json')
    # always print the log
    docker logs whisper-service > $LOG_PATH/whisper-service.log
    docker logs speecht5-service > $LOG_PATH/tts-service.log
    docker logs audioqna-vllm-service > $LOG_PATH/audioqna-vllm-service.log
    docker logs audioqna-backend-server > $LOG_PATH/audioqna-backend-server.log
    echo "$response" | sed 's/^"//;s/"$//' | base64 -d > speech.mp3

    if [[ $(file speech.mp3) == *"RIFF"* ]]; then
        echo "Result correct."
    else
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
    docker system prune -f
    echo "::endgroup::"

}

main
