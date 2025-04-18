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
export MODEL_CACHE=${model_cache:-"/var/lib/GenAI/data"}

export REDIS_DB_PORT=6379
export REDIS_INSIGHTS_PORT=8001
export REDIS_RETRIEVER_PORT=7000
export EMBEDDER_PORT=6000
export TEI_EMBEDDER_PORT=8090
export DATAPREP_REDIS_PORT=6007

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

    echo "Build all the images with --no-cache, check docker_image_build.log for details..."
    service_list="codegen codegen-gradio-ui llm-textgen dataprep retriever embedding"
    docker compose -f build.yaml build ${service_list} --no-cache > ${LOG_PATH}/docker_image_build.log

    docker pull ghcr.io/huggingface/text-generation-inference:2.3.1-rocm
    docker images && sleep 1s
}

function start_services() {
    cd $WORKPATH/docker_compose/amd/gpu/rocm/

    export HOST_IP=${ip_address}
    export CODEGEN_LLM_MODEL_ID="Qwen/Qwen2.5-Coder-7B-Instruct"
    export CODEGEN_TGI_SERVICE_PORT=8028
    export CODEGEN_TGI_LLM_ENDPOINT="http://${ip_address}:${CODEGEN_TGI_SERVICE_PORT}"
    export CODEGEN_LLM_SERVICE_PORT=9000
    export CODEGEN_HUGGINGFACEHUB_API_TOKEN=${HUGGINGFACEHUB_API_TOKEN}
    export CODEGEN_MEGA_SERVICE_HOST_IP=${ip_address}
    export CODEGEN_LLM_SERVICE_HOST_IP=${ip_address}
    export CODEGEN_BACKEND_SERVICE_PORT=18150
    export CODEGEN_BACKEND_SERVICE_URL="http://${ip_address}:${CODEGEN_BACKEND_SERVICE_PORT}/v1/codegen"
    export CODEGEN_UI_SERVICE_PORT=5173

    export REDIS_URL="redis://${HOST_IP}:${REDIS_DB_PORT}"
    export RETRIEVAL_SERVICE_HOST_IP=${HOST_IP}
    export RETRIEVER_COMPONENT_NAME="OPEA_RETRIEVER_REDIS"
    export INDEX_NAME="CodeGen"

    export EMBEDDING_MODEL_ID="BAAI/bge-base-en-v1.5"
    export TEI_EMBEDDING_HOST_IP=${HOST_IP}
    export TEI_EMBEDDING_ENDPOINT="http://${HOST_IPp}:${TEI_EMBEDDER_PORT}"
    export DATAPREP_ENDPOINT="http://${HOST_IP}:${DATAPREP_REDIS_PORT}/v1/dataprep"


    sed -i "s/backend_address/$ip_address/g" $WORKPATH/ui/svelte/.env

    # Start Docker Containers
    docker compose up -d > ${LOG_PATH}/start_services_with_compose.log

    n=0
    until [[ "$n" -ge 100 ]]; do
        docker logs codegen-tgi-service > ${LOG_PATH}/codegen_tgi_service_start.log
        if grep -q Connected ${LOG_PATH}/codegen_tgi_service_start.log; then
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
    # tgi for llm service
    validate_services \
        "${ip_address}:${CODEGEN_TGI_SERVICE_PORT}/generate" \
        "generated_text" \
        "codegen-tgi-service" \
        "codegen-tgi-service" \
        '{"inputs":"def print_hello_world():","parameters":{"max_new_tokens":256, "do_sample": true}}'
    sleep 10
    # llm microservice
    validate_services \
        "${ip_address}:${CODEGEN_LLM_SERVICE_PORT}/v1/chat/completions" \
        "data: " \
        "codegen-llm-server" \
        "codegen-llm-server" \
        '{"query":"def print_hello_world():"}'

    # Data ingest microservice
    validate_services \
        "${ip_address}:6007/v1/dataprep/ingest" \
        "Data preparation succeeded" \
        "ingest" \
        "dataprep-redis-server" \
        'link_list=["https://modin.readthedocs.io/en/latest/index.html"]'
}

function validate_megaservice() {
    # Curl the Mega Service
    validate_services \
        "${ip_address}:${CODEGEN_BACKEND_SERVICE_PORT}/v1/codegen" \
        "print" \
        "codegen-backend-server" \
        "codegen-backend-server" \
        '{"messages": "def print_hello_world():", "max_tokens": 256}'
    # Curl the Mega Service with index_name and agents_flag
    validate_services \
        "${ip_address}:${CODEGEN_BACKEND_SERVICE_PORT}/v1/codegen" \
        "" \
        "codegen-backend-server" \
        "codegen-backend-server" \
        '{ "index_name": "test_redis", "agents_flag": "True", "messages": "def print_hello_world():", "max_tokens": 256}'

}

function validate_frontend() {
    cd $WORKPATH/ui/svelte
    local conda_env_name="OPEA_e2e"
    export PATH=${HOME}/miniconda3/bin/:$PATH
    if conda info --envs | grep -q "$conda_env_name"; then
        echo "$conda_env_name exist!"
    else
        conda create -n ${conda_env_name} python=3.12 -y
    fi
    source activate ${conda_env_name}

    sed -i "s/localhost/$ip_address/g" playwright.config.ts
    sed -i "s/timeout: 5000/timeout: 15000/g" playwright.config.ts

    conda install -c conda-forge nodejs=22.6.0 -y
    npm install && npm ci && npx playwright install --with-deps
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
    cd $WORKPATH/docker_compose/amd/gpu/rocm/
    docker compose stop && docker compose rm -f
}

function main() {

    stop_docker

    if [[ "$IMAGE_REPO" == "opea" ]]; then build_docker_images; fi
    start_services

    validate_microservices
    validate_megaservice
    validate_frontend

    stop_docker
    echo y | docker system prune
    cd $WORKPATH

}

main
