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

COMPOSE_FILE="compose.yaml"
EC_RAG_SERVICE_PORT=16010

MODEL_PATH="/home/media/models"
# MODEL_PATH="$WORKPATH/models"
DOC_PATH="$WORKPATH/tests"
GRADIO_PATH="$WORKPATH/tests"

HF_ENDPOINT=https://hf-mirror.com


function build_docker_images() {
    cd $WORKPATH/docker_image_build
    echo "Build all the images with --no-cache, check docker_image_build.log for details..."
    docker compose -f build.yaml build --no-cache > ${LOG_PATH}/docker_image_build.log

    docker images && sleep 1s
}

function start_services() {
    export MODEL_PATH=${MODEL_PATH}
    export DOC_PATH=${DOC_PATH}
    export GRADIO_PATH=${GRADIO_PATH}
    export HOST_IP=${HOST_IP}
    export LLM_MODEL=${LLM_MODEL}
    export HF_ENDPOINT=${HF_ENDPOINT}
    export vLLM_ENDPOINT=${vLLM_ENDPOINT}
    export HUGGINGFACEHUB_API_TOKEN=${HUGGINGFACEHUB_API_TOKEN}
    export no_proxy="localhost, 127.0.0.1, 192.168.1.1"

    cd $WORKPATH/docker_compose/intel/gpu/arc

    # Start Docker Containers
    docker compose -f $COMPOSE_FILE up -d > ${LOG_PATH}/start_services_with_compose.log
    sleep 20
}

function validate_rag() {
    cd $WORKPATH/tests

    # setup pipeline
    validate_services \
        "${HOST_IP}:${EC_RAG_SERVICE_PORT}/v1/settings/pipelines" \
        "active" \
        "pipeline" \
        "edgecraftrag-server" \
        '@configs/test_pipeline_local_llm.json'

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
        "edgecraftrag-server" \
        '{"messages":"What is the test id?"}'
}

function validate_megaservice() {
    # Curl the Mega Service
    validate_services \
        "${HOST_IP}:16011/v1/chatqna" \
        "1234567890" \
        "query" \
        "edgecraftrag-server" \
        '{"messages":"What is the test id?"}'
}

function stop_docker() {
    cd $WORKPATH/docker_compose/intel/gpu/arc
    docker compose -f $COMPOSE_FILE down
}


function main() {
    mkdir -p $LOG_PATH

    stop_docker
    if [[ "$IMAGE_REPO" == "opea" ]]; then build_docker_images; fi
    start_services
    echo "EC_RAG service started" && sleep 1s

    validate_rag
    validate_megaservice

    stop_docker
    echo y | docker system prune

}

main
