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
export HF_TOKEN=${HF_TOKEN}
export LLM_ENDPOINT_PORT=8008
export LLM_ENDPOINT="http://0.0.0.0:${LLM_ENDPOINT_PORT}"
export BROWSER_USE_AGENT_PORT=8022
export LLM_MODEL_ID="Qwen/Qwen2.5-VL-32B-Instruct"
export MAX_TOTAL_TOKENS=131072
export NUM_CARDS=4

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
    docker compose -f build.yaml build --no-cache --build-arg https_proxy=$https_proxy --build-arg http_proxy=$http_proxy > ${LOG_PATH}/docker_image_build.log

    docker images && sleep 1s
}

function start_services() {
    cd $WORKPATH/docker_compose/intel/hpu/gaudi
    source set_env.sh

    # Start Docker Containers
    docker compose -f compose.yaml up -d --quiet-pull > ${LOG_PATH}/start_services_with_compose.log
    n=0
    until [[ "$n" -ge 200 ]]; do
        echo "n=$n"
        docker logs vllm-gaudi-server > vllm_service_start.log 2>&1
        if grep -q "Application startup complete" vllm_service_start.log; then
            break
        fi
        sleep 5s
        n=$((n+1))
    done
}

function validate_service() {
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
    # vllm for llm service
    validate_service \
        "${ip_address}:${LLM_ENDPOINT_PORT}/v1/chat/completions" \
        "content" \
        "vllm-llm" \
        "vllm-gaudi-server" \
        '{"model": "'${LLM_MODEL_ID}'", "messages": [{"role": "user", "content": "What is Deep Learning?"}], "max_tokens":17}'
}

function validate_megaservice() {
    # start web server for testing
    cd $WORKPATH/tests/webarena
    bash shopping_admin.sh start

    # Curl the Mega Service
    validate_service \
        "${ip_address}:${BROWSER_USE_AGENT_PORT}/v1/browser_use_agent" \
        "\"is_success\":true" \
        "browser-use-agent" \
        "browser-use-agent-server" \
        '{"task_prompt": "Navigate to http://'${ip_address}':8084/admin and login with the credentials: username: admin, password: admin1234. Then, find out What are the top-3 best-selling product in 2022?"}'
}

function stop_docker() {
    cd $WORKPATH/docker_compose/intel/hpu/gaudi
    docker compose -f compose.yaml down

    cd $WORKPATH/tests/webarena
    bash shopping_admin.sh stop
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
    sleep 30
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
