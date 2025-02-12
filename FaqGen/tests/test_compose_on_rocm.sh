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

export HOST_IP=${ip_address}
export FAQGEN_LLM_MODEL_ID="meta-llama/Meta-Llama-3-8B-Instruct"
export FAQGEN_TGI_SERVICE_PORT=8008
export FAQGEN_LLM_SERVER_PORT=9000
export FAQGEN_HUGGINGFACEHUB_API_TOKEN=${HUGGINGFACEHUB_API_TOKEN}
export FAQGEN_CARD_ID="card1"
export FAQGEN_RENDER_ID="renderD136"
export FAQGEN_BACKEND_SERVER_PORT=8888
export FAGGEN_UI_PORT=5173
export LLM_ENDPOINT="http://${ip_address}:8008"
export MEGA_SERVICE_HOST_IP=${ip_address}
export LLM_SERVICE_HOST_IP=${ip_address}
export BACKEND_SERVICE_ENDPOINT="http://${ip_address}:8888/v1/faqgen"
export PATH="~/miniconda3/bin:$PATH"
export FAQGen_COMPONENT_NAME="OpeaFaqGenTgi"
export LOGFLAG=True

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
    service_list="faqgen faqgen-ui llm-faqgen"
    docker compose -f build.yaml build ${service_list} --no-cache > "${LOG_PATH}"/docker_image_build.log
    docker pull ghcr.io/huggingface/text-generation-inference:2.3.1-rocm
    docker images && sleep 1s
}

function start_services() {
    cd "$WORKPATH"/docker_compose/amd/gpu/rocm

    sed -i "s/backend_address/$ip_address/g" "$WORKPATH"/ui/svelte/.env

    # Start Docker Containers
    docker compose up -d > "${LOG_PATH}"/start_services_with_compose.log

    sleep 30s
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

        local CONTENT=$(curl -s -X POST -d "$INPUT_DATA" -H 'Content-Type: application/json' "$URL" | tee "${LOG_PATH}"/"${SERVICE_NAME}".log)

        if echo "$CONTENT" | grep -q "$EXPECTED_RESULT"; then
            echo "[ $SERVICE_NAME ] Content is as expected."
        else
            echo "[ $SERVICE_NAME ] Content does not match the expected result: $CONTENT"
            docker logs "${DOCKER_NAME}" >> "${LOG_PATH}"/"${SERVICE_NAME}".log
            exit 1
        fi
    else
        echo "[ $SERVICE_NAME ] HTTP status is not 200. Received status was $HTTP_STATUS"
        docker logs "${DOCKER_NAME}" >> "${LOG_PATH}"/"${SERVICE_NAME}".log
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
        "tgi-service" \
        "faqgen-tgi-service" \
        '{"inputs":"What is Deep Learning?","parameters":{"max_new_tokens":17, "do_sample": true}}'

    # llm microservice
    validate_services \
        "${ip_address}:9000/v1/faqgen" \
        "text" \
        "llm" \
        "faqgen-llm-server" \
        '{"messages":"Text Embeddings Inference (TEI) is a toolkit for deploying and serving open source text embeddings and sequence classification models. TEI enables high-performance extraction for the most popular models, including FlagEmbedding, Ember, GTE and E5."}'
}

function validate_megaservice() {
    local SERVICE_NAME="mega-faqgen"
    local DOCKER_NAME="faqgen-backend-server"
    local EXPECTED_RESULT="embedding"
    local INPUT_DATA="messages=Text Embeddings Inference (TEI) is a toolkit for deploying and serving open source text embeddings and sequence classification models. TEI enables high-performance extraction for the most popular models, including FlagEmbedding, Ember, GTE and E5."
    local URL="${ip_address}:8888/v1/faqgen"
    local HTTP_STATUS=$(curl -s -o /dev/null -w "%{http_code}" -X POST -F "$INPUT_DATA" -H 'Content-Type: multipart/form-data' "$URL")
    if [ "$HTTP_STATUS" -eq 200 ]; then
        echo "[ $SERVICE_NAME ] HTTP status is 200. Checking content..."

        local CONTENT=$(curl -s -X POST -F "$INPUT_DATA" -F "max_tokens=32" -F "stream=false" -H 'Content-Type: multipart/form-data' "$URL" | tee ${LOG_PATH}/${SERVICE_NAME}.log)

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

function validate_frontend() {
    cd "$WORKPATH"/ui/svelte
    local conda_env_name="OPEA_e2e"
    export PATH=${HOME}/miniforge3/bin/:$PATH
    if conda info --envs | grep -q "$conda_env_name"; then
        echo "$conda_env_name exist!"
    else
        conda create -n ${conda_env_name} python=3.12 -y
    fi
    source activate ${conda_env_name}

    sed -i "s/localhost/$ip_address/g" playwright.config.ts

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
    cd "$WORKPATH"/docker_compose/amd/gpu/rocm
    docker compose stop && docker compose rm -f
}

function main() {

    stop_docker

    if [[ "$IMAGE_REPO" == "opea" ]]; then build_docker_images; fi
    start_services

    validate_microservices
    validate_megaservice
#    validate_frontend

    stop_docker
    echo y | docker system prune

}

main
