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
    service_list="translation translation-ui llm-textgen nginx vllm-rocm"
    docker compose -f build.yaml build ${service_list} --no-cache > ${LOG_PATH}/docker_image_build.log
    docker images && sleep 3s
}

function start_services() {
    cd $WORKPATH/docker_compose/amd/gpu/rocm/

    export host_ip=${ip_address}
    source set_env_vllm.sh

    sed -i "s/backend_address/$ip_address/g" $WORKPATH/ui/svelte/.env

    # Start Docker Containers
    docker compose -f compose_vllm.yaml up -d > ${LOG_PATH}/start_services_with_compose.log

    n=0
    # wait long for llm model download
    until [[ "$n" -ge 500 ]]; do
        docker logs translation-vllm-service > ${LOG_PATH}/translation-vllm-service_start.log 2>&1
        if grep -q "Application startup complete" ${LOG_PATH}/translation-vllm-service_start.log; then
            echo "vLLM check successful"
            break
        fi
        sleep 10s
        n=$((n+1))
    done

}

function validate_services() {
    local URL="$1"
    local EXPECTED_RESULT="$2"
    local SERVICE_NAME="$3"
    local DOCKER_NAME="$4"
    local INPUT_DATA="$5"

    local HTTP_STATUS=$(curl -s -o /dev/null -w "%{http_code}" -X POST -d "$INPUT_DATA" -H 'Content-Type: application/json' "$URL")
    if [ "$HTTP_STATUS" -eq 200 ]; then
        echo "[ $SERVICE_NAME ] HTTP status is 200. Checking content..."

        local CONTENT=$(curl -s -X POST -d "$INPUT_DATA" -H 'Content-Type: application/json' "$URL" | tee ${LOG_PATH}/${SERVICE_NAME}.log)

        if echo "$CONTENT" | grep -q "$EXPECTED_RESULT"; then
            echo "[ $SERVICE_NAME ] Content is as expected."
        else
            echo "[ $SERVICE_NAME ] Content does not match the expected result: $CONTENT"
            docker logs ${DOCKER_NAME} >> ${LOG_PATH}/${SERVICE_NAME}.log
            exit 1
        fi
    else
        echo "[ $SERVICE_NAME ] HTTP status is not 200. Received status was $HTTP_STATUS"
        docker logs ${DOCKER_NAME} >> ${LOG_PATH}/${SERVICE_NAME}.log
        exit 1
    fi
    sleep 1s
}

function validate_microservices() {
    # Check if the microservices are running correctly.

    # vLLM for llm service
    validate_services \
        "${ip_address}:${TRANSLATION_VLLM_SERVICE_PORT}/v1/completions" \
        "choices" \
        "translation-vllm-service" \
        "translation-vllm-service" \
        '{"model": "haoranxu/ALMA-13B", "prompt": "What is Deep Learning?", "max_tokens": 100, "temperature": 0}'

    # llm microservice
    validate_services \
        "${HOST_IP}:${TRANSLATION_LLM_PORT}/v1/chat/completions" \
        "data: " \
        "translation-llm" \
        "translation-llm-textgen-server" \
        '{"query":"Translate this from Chinese to English:\nChinese: 我爱机器翻译。\nEnglish:"}'
}

function validate_megaservice() {
    # Curl the Mega Service
    validate_services \
        "${HOST_IP}:${TRANSLATION_BACKEND_SERVICE_PORT}/v1/translation" \
        "translation" \
        "translation-backend-server" \
        "translation-backend-server" \
        '{"language_from": "Chinese","language_to": "English","source_language": "我爱机器翻译。"}'

    # test the megeservice via nginx
    validate_services \
        "${HOST_IP}:${TRANSLATION_NGINX_PORT}/v1/translation" \
        "translation" \
        "translation-nginx-server" \
        "translation-nginx-server" \
        '{"language_from": "Chinese","language_to": "English","source_language": "我爱机器翻译。"}'
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

    echo "::group::validate_microservices"
    validate_microservices
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
