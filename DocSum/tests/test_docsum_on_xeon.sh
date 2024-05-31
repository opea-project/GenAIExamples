#!/bin/bash
# Copyright (C) 2024 Intel Corporation
# SPDX-License-Identifier: Apache-2.0

set -x

WORKPATH=$(dirname "$PWD")
LOG_PATH="$WORKPATH/tests"
ip_address=$(hostname -I | awk '{print $1}')

function build_docker_images() {
    cd $WORKPATH
    git clone https://github.com/opea-project/GenAIComps.git
    cd GenAIComps

    docker build --no-cache -t opea/llm-docsum-tgi:latest --build-arg https_proxy=$https_proxy --build-arg http_proxy=$http_proxy -f comps/llms/summarization/tgi/Dockerfile .

    cd $WORKPATH/docker
    docker build --no-cache -t opea/docsum:latest --build-arg https_proxy=$https_proxy --build-arg http_proxy=$http_proxy -f Dockerfile .

    cd $WORKPATH/docker/ui
    docker build --no-cache -t opea/docsum-ui:latest --build-arg https_proxy=$https_proxy --build-arg http_proxy=$http_proxy -f docker/Dockerfile .

    docker images
}

function start_services() {
    cd $WORKPATH/docker/xeon

    export LLM_MODEL_ID="Intel/neural-chat-7b-v3-3"
    export TGI_LLM_ENDPOINT="http://${ip_address}:8008"
    export HUGGINGFACEHUB_API_TOKEN=${HUGGINGFACEHUB_API_TOKEN}
    export MEGA_SERVICE_HOST_IP=${ip_address}
    export LLM_SERVICE_HOST_IP=${ip_address}
    export BACKEND_SERVICE_ENDPOINT="http://${ip_address}:8888/v1/docsum"

    sed -i "s/backend_address/$ip_address/g" $WORKPATH/docker/ui/svelte/.env

    # Start Docker Containers
    # TODO: Replace the container name with a test-specific name
    docker compose -f docker_compose.yaml up -d

    sleep 2m # Waits 2 minutes
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

    # tgi for llm service
    validate_services \
        "${ip_address}:8008/generate" \
        "generated_text" \
        "tgi-llm" \
        "tgi_service" \
        '{"inputs":"What is Deep Learning?","parameters":{"max_new_tokens":17, "do_sample": true}}'

    # llm microservice
    validate_services \
        "${ip_address}:9000/v1/chat/docsum" \
        "data: " \
        "llm" \
        "llm-docsum-server" \
        '{"query":"Text Embeddings Inference (TEI) is a toolkit for deploying and serving open source text embeddings and sequence classification models. TEI enables high-performance extraction for the most popular models, including FlagEmbedding, Ember, GTE and E5."}'
}

function validate_megaservice() {
    # Curl the Mega Service
    validate_services \
    "${ip_address}:8888/v1/docsum" \
    "versatile toolkit" \
    "mega-docsum" \
    "docsum-xeon-backend-server" \
    '{"messages": "Text Embeddings Inference (TEI) is a toolkit for deploying and serving open source text embeddings and sequence classification models. TEI enables high-performance extraction for the most popular models, including FlagEmbedding, Ember, GTE and E5."}'
}

function validate_frontend() {
    cd $WORKPATH/docker/ui/svelte
    local conda_env_name="DocSum_e2e"
    export PATH=${HOME}/miniforge3/bin/:$PATH
    conda remove -n ${conda_env_name} --all -y
    conda create -n ${conda_env_name} python=3.12 -y
    source activate ${conda_env_name}

    sed -i "s/localhost/$ip_address/g" playwright.config.ts

    conda install -c conda-forge nodejs -y && npm install && npm ci && npx playwright install --with-deps
    node -v && npm -v && pip list

    exit_status=0
    npx playwright test || exit_status=$?

    if [ $exit_status -ne 0 ]; then
        echo "[TEST INFO]: ---------frontend test failed---------"
        exit $exit_status
    else
        echo "[TEST INFO]: ---------frontend test passed---------"
    fi

}

function stop_docker() {
    cd $WORKPATH/docker/xeon
    container_list=$(cat docker_compose.yaml | grep container_name | cut -d':' -f2)
    for container_name in $container_list; do
        cid=$(docker ps -aq --filter "name=$container_name")
        if [[ ! -z "$cid" ]]; then docker stop $cid && docker rm $cid && sleep 1s; fi
    done
}

function main() {

    stop_docker

    build_docker_images
    start_services

    validate_microservices
    validate_megaservice
    validate_frontend

    stop_docker
    echo y | docker system prune

}

main
