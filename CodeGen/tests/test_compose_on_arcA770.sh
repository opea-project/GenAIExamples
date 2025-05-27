#! /usr/bin/env bash

# Copyright (C) 2025 Intel Corporation
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
COMPOSE_PATH="${WORKPATH}/docker_compose/intel/gpu/arc"

source $WORKPATH/docker_compose/intel/set_env.sh
export LLM_MODEL_LOCAL_PATH=${LLM_MODEL_ID}
#export TENSOR_PARALLEL_SIZE=2

function start_services() {
    local llm_container_name="vllm-service"

    cd ${COMPOSE_PATH}

    # Start Docker Containers
    docker compose up -d | tee ${LOG_PATH}/start_services_with_compose.log

    n=0
    until [[ "$n" -ge 100 ]]; do
        docker logs ${llm_container_name} > ${LOG_PATH}/llm_service_start.log 2>&1
        if grep "Started server process" ${LOG_PATH}/llm_service_start.log; then
            break
        fi
        sleep 5s
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
    sleep 5s
}


function validate_microservices() {
   validate_services \
        "localhost:9009/v1/chat/completions" \
        "completion_tokens" \
        "vllm-service" \
        "vllm-service" \
        '{"model": "Qwen/Qwen2.5-Coder-7B-Instruct", "messages": [{"role": "user", "content": "What is Deep Learning?"}], "max_tokens": 256}'
}

function stop_docker() {
    cd ${COMPOSE_PATH}
    docker compose down
    docker system prune -f
}

function main() {
    echo "::group::stop_docker"
    stop_docker
    echo "::endgroup::"

    trap stop_docker EXIT

    echo "::group::start_services"
    start_services
    echo "::endgroup::"

    echo "::group::validate_microservices"
    validate_microservices
    echo "::endgroup::"
}

main
