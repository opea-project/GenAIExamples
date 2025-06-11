#!/bin/bash
# Copyright (C) 2024 Intel Corporation
# SPDX-License-Identifier: Apache-2.0

set -e
source ./common.sh

IMAGE_REPO=${IMAGE_REPO:-"opea"}
IMAGE_TAG=${IMAGE_TAG:-"latest"}
echo "REGISTRY=IMAGE_REPO=${IMAGE_REPO}"
echo "TAG=IMAGE_TAG=${IMAGE_TAG}"
export REGISTRY=${IMAGE_REPO}
export TAG=${IMAGE_TAG}

WORKPATH=$(dirname "$PWD")
LOG_PATH="$WORKPATH/tests"

ip_address=$(hostname -I | awk '{print $1}')
HOST_IP=$ip_address

COMPOSE_FILE="compose_vllm_multi-arc.yaml"
EC_RAG_SERVICE_PORT=16010

MODEL_PATH="/home/media/qwen"
# MODEL_PATH="$WORKPATH/models"
DOC_PATH="$WORKPATH/tests"
UI_UPLOAD_PATH="$WORKPATH/tests"

HF_ENDPOINT=https://hf-mirror.com
NGINX_PORT=8086
NGINX_PORT_0=8100
NGINX_PORT_1=8100
VLLM_SERVICE_PORT_0=8100
TENSOR_PARALLEL_SIZE=1
SELECTED_XPU_0=0
vLLM_ENDPOINT="http://${HOST_IP}:${NGINX_PORT}"
CONTAINER_COUNT="single_container"
LLM_MODEL=Qwen/Qwen2-7B-Instruct
LLM_MODEL_PATH=$MODEL_PATH
NGINX_CONFIG_PATH="$WORKPATH/nginx/nginx.conf"

function build_docker_images() {
    opea_branch=${opea_branch:-"main"}
    cd $WORKPATH/docker_image_build
    git clone --depth 1 --branch ${opea_branch} https://github.com/opea-project/GenAIComps.git
    pushd GenAIComps
    echo "GenAIComps test commit is $(git rev-parse HEAD)"
    docker build --no-cache -t ${REGISTRY}/comps-base:${TAG} --build-arg https_proxy=$https_proxy --build-arg http_proxy=$http_proxy -f Dockerfile .
    popd && sleep 1s

    echo "Pull intelanalytics/ipex-llm-serving-xpu image"
    docker pull intelanalytics/ipex-llm-serving-xpu:0.8.3-b18

    echo "Build all the images with --no-cache, check docker_image_build.log for details..."
    docker compose -f build.yaml build --no-cache > ${LOG_PATH}/docker_image_build.log

    docker images && sleep 1s
}

function start_services() {
    cd $WORKPATH/docker_compose/intel/gpu/arc
    source set_env.sh
    envsubst < $WORKPATH/nginx/nginx.conf.template > $WORKPATH/nginx/nginx.conf
    # Start Docker Containers
    docker compose -f $COMPOSE_FILE --profile $CONTAINER_COUNT up -d > ${LOG_PATH}/start_services_with_compose.log
    echo "ipex-llm-serving-xpu is booting, please wait."
    n=0
    until [[ "$n" -ge 100 ]]; do
        docker logs ipex-llm-serving-xpu-container-0 > ${LOG_PATH}/ipex-llm-serving-xpu-container.log 2>&1
        if grep -q "Starting vLLM API server on http://0.0.0.0:" ${LOG_PATH}/ipex-llm-serving-xpu-container.log; then
            break
        fi
        sleep 6s
        n=$((n+1))
    done
}

function validate_services() {
    local URL="$1"
    local EXPECTED_RESULT="$2"
    local SERVICE_NAME="$3"
    local DOCKER_NAME="$4"
    local INPUT_DATA="$5"

    echo "[ $SERVICE_NAME ] Validating $SERVICE_NAME service..."
    local RESPONSE=$(curl -s -w "%{http_code}" -o ${LOG_PATH}/${SERVICE_NAME}.log -X POST -d "$INPUT_DATA" -H 'Content-Type: application/json' "$URL")
    while [ ! -f ${LOG_PATH}/${SERVICE_NAME}.log ]; do
        sleep 1
    done
    local HTTP_STATUS="${RESPONSE: -3}"
    local CONTENT=$(cat ${LOG_PATH}/${SERVICE_NAME}.log)

    if [ "$HTTP_STATUS" -eq 200 ]; then
        echo "[ $SERVICE_NAME ] HTTP status is 200. Checking content..."


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

function validate_rag() {
    cd $WORKPATH/tests

    # setup pipeline
    validate_services \
        "${HOST_IP}:${EC_RAG_SERVICE_PORT}/v1/settings/pipelines" \
        "active" \
        "pipeline" \
        "edgecraftrag-server" \
        '@configs/test_pipeline_ipex_vllm.json'

    # add data
    validate_services \
        "${HOST_IP}:${EC_RAG_SERVICE_PORT}/v1/data" \
        "Done" \
        "data" \
        "edgecraftrag-server" \
        '@configs/test_data.json'

    # query
    validate_services \
        "${HOST_IP}:${EC_RAG_SERVICE_PORT}/v1/chatqna" \
        "1234567890" \
        "query" \
        "ipex-llm-serving-xpu-container-0" \
        '{"messages":"What is the test id?"}'
}

function validate_megaservice() {
    # Curl the Mega Service
    validate_services \
        "${HOST_IP}:16011/v1/chatqna" \
        "1234567890" \
        "query" \
        "ipex-llm-serving-xpu-container-0" \
        '{"messages":"What is the test id?"}'
}

function stop_docker() {
    cd $WORKPATH/docker_compose/intel/gpu/arc
    docker compose -f $COMPOSE_FILE down
}


function main() {
    mkdir -p $LOG_PATH

    echo "::group::stop_docker"
    stop_docker
    echo "::endgroup::"

    echo "::group::build_docker_images"
    if [[ "$IMAGE_REPO" == "opea" ]]; then build_docker_images; fi
    echo "::endgroup::"

    echo "::group::start_services"
    start_services
    echo "::endgroup::"

    echo "::group::validate_rag"
    validate_rag
    echo "::endgroup::"

    echo "::group::validate_megaservice"
    validate_megaservice
    echo "::endgroup::"

    echo "::group::stop_docker"
    stop_docker
    echo y | docker system prune
    echo "::endgroup::"

}

main
