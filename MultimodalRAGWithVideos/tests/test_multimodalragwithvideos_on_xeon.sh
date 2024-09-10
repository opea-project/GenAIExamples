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

WORKPATH=$(dirname "$PWD")
LOG_PATH="$WORKPATH/tests"
ip_address=$(hostname -I | awk '{print $1}')

function build_docker_images() {
    cd $WORKPATH/docker
    # git clone https://github.com/opea-project/GenAIComps.git



    echo "Build all the images with --no-cache, check docker_image_build.log for details..."
    service_list="multimodalragwithvideos bridgetower-embedding-server multimodal-embedding multimodal-retriever llava-server lvm multimodal-data-prep-service"
    docker compose -f docker_build_compose.yaml build ${service_list} --no-cache > ${LOG_PATH}/docker_image_build.log

    # docker pull ghcr.io/huggingface/tgi-gaudi:2.0.1
    # docker pull ghcr.io/huggingface/text-embeddings-inference:cpu-1.5

    docker images && sleep 1s
}

function start_services() {
    cd $WORKPATH/docker/xeon

    export EMBEDDING_MODEL_ID="BAAI/bge-base-en-v1.5"
    export LLM_MODEL_ID="Intel/neural-chat-7b-v3-3"
    export TEI_EMBEDDING_ENDPOINT="http://${ip_address}:6006"
    export TGI_LLM_ENDPOINT="http://${ip_address}:9009"
    export REDIS_URL="redis://${ip_address}:6379"
    export REDIS_HOST=${ip_address}
    export INDEX_NAME="rag-redis"
    export HUGGINGFACEHUB_API_TOKEN=${HUGGINGFACEHUB_API_TOKEN}
    export MEGA_SERVICE_HOST_IP=${ip_address}
    export EMBEDDING_SERVICE_HOST_IP=${ip_address}
    export RETRIEVER_SERVICE_HOST_IP=${ip_address}
    export LLM_SERVICE_HOST_IP=${ip_address}
    export BACKEND_SERVICE_ENDPOINT="http://${ip_address}:8888/v1/chatqna"
    export DATAPREP_SERVICE_ENDPOINT="http://${ip_address}:6007/v1/dataprep"
    export DATAPREP_GET_FILE_ENDPOINT="http://${ip_address}:6007/v1/dataprep/get_file"
    export DATAPREP_DELETE_FILE_ENDPOINT="http://${ip_address}:6007/v1/dataprep/delete_file"

    sed -i "s/backend_address/$ip_address/g" $WORKPATH/docker/ui/svelte/.env

    # Start Docker Containers
    docker compose -f compose_without_rerank.yaml up -d > ${LOG_PATH}/start_services_with_compose.log
    n=0
    until [[ "$n" -ge 100 ]]; do
        docker logs tgi-service > ${LOG_PATH}/tgi_service_start.log
        if grep -q Connected ${LOG_PATH}/tgi_service_start.log; then
            break
        fi
        sleep 5s
        n=$((n+1))
    done
}
