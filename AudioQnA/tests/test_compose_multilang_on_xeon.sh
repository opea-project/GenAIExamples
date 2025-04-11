#!/bin/bash
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
LOG_PATH="$WORKPATH/tests"
ip_address=$(hostname -I | awk '{print $1}')

function build_docker_images() {
    opea_branch=${opea_branch:-"main"}
    # If the opea_branch isn't main, replace the git clone branch in Dockerfile.
    if [[ "${opea_branch}" != "main" ]]; then
        cd $WORKPATH
        OLD_STRING="RUN git clone --depth 1 https://github.com/opea-project/GenAIComps.git"
        NEW_STRING="RUN git clone --depth 1 --branch ${opea_branch} https://github.com/opea-project/GenAIComps.git"
        find . -type f -name "Dockerfile*" | while read -r file; do
            echo "Processing file: $file"
            sed -i "s|$OLD_STRING|$NEW_STRING|g" "$file"
        done
    fi

    cd $WORKPATH/docker_image_build
    git clone --depth 1 --branch ${opea_branch} https://github.com/opea-project/GenAIComps.git

    git clone https://github.com/vllm-project/vllm.git
    cd ./vllm/
    VLLM_VER="v0.8.3"
    echo "Check out vLLM tag ${VLLM_VER}"
    git checkout ${VLLM_VER} &> /dev/null && cd ../

    echo "Build all the images with --no-cache, check docker_image_build.log for details..."
    service_list="audioqna-multilang audioqna-ui whisper gpt-sovits vllm"
    docker compose -f build.yaml build ${service_list} --no-cache > ${LOG_PATH}/docker_image_build.log

    docker images && sleep 1s
}

function start_services() {
    cd $WORKPATH/docker_compose/intel/cpu/xeon/
    export HUGGINGFACEHUB_API_TOKEN=${HUGGINGFACEHUB_API_TOKEN}
    export LLM_MODEL_ID=meta-llama/Meta-Llama-3-8B-Instruct

    export MEGA_SERVICE_HOST_IP=${ip_address}
    export WHISPER_SERVER_HOST_IP=${ip_address}
    export GPT_SOVITS_SERVER_HOST_IP=${ip_address}
    export LLM_SERVER_HOST_IP=${ip_address}

    export WHISPER_SERVER_PORT=7066
    export GPT_SOVITS_SERVER_PORT=9880
    export LLM_SERVER_PORT=3006

    export BACKEND_SERVICE_ENDPOINT=http://${ip_address}:3008/v1/audioqna
    export host_ip=${ip_address}

    # sed -i "s/backend_address/$ip_address/g" $WORKPATH/ui/svelte/.env

    # Start Docker Containers
    docker compose -f compose_multilang.yaml up -d > ${LOG_PATH}/start_services_with_compose.log
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
    docker logs gpt-sovits-service > $LOG_PATH/tts-service.log
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
    docker compose -f compose_multilang.yaml stop && docker compose rm -f
}

function main() {

    stop_docker
    if [[ "$IMAGE_REPO" == "opea" ]]; then build_docker_images; fi
    start_services

    validate_megaservice

    stop_docker
    echo y | docker system prune

}

main
