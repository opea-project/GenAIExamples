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

export HOST_IP=${ip_address}
export HOST_IP_EXTERNAL=${ip_address}

export CHATQNA_EMBEDDING_MODEL_ID="BAAI/bge-base-en-v1.5"
export CHATQNA_HUGGINGFACEHUB_API_TOKEN=${HUGGINGFACEHUB_API_TOKEN}
export CHATQNA_LLM_MODEL_ID="meta-llama/Meta-Llama-3-8B-Instruct"
export CHATQNA_RERANK_MODEL_ID="BAAI/bge-reranker-base"

export CHATQNA_BACKEND_SERVICE_PORT=8888
export CHATQNA_FRONTEND_SERVICE_PORT=5173
export CHATQNA_NGINX_PORT=80
export CHATQNA_REDIS_DATAPREP_PORT=18103
export CHATQNA_REDIS_RETRIEVER_PORT=7000
export CHATQNA_REDIS_VECTOR_INSIGHT_PORT=8001
export CHATQNA_REDIS_VECTOR_PORT=6379
export CHATQNA_TEI_EMBEDDING_PORT=18090
export CHATQNA_TEI_RERANKING_PORT=18808
export CHATQNA_VLLM_SERVICE_PORT=18008

export CHATQNA_BACKEND_SERVICE_ENDPOINT="http://${HOST_IP_EXTERNAL}:${CHATQNA_BACKEND_SERVICE_PORT}/v1/chatqna"
export CHATQNA_BACKEND_SERVICE_IP=${HOST_IP_EXTERNAL}
export CHATQNA_DATAPREP_DELETE_FILE_ENDPOINT="http://${HOST_IP_EXTERNAL}:${CHATQNA_REDIS_DATAPREP_PORT}/v1/dataprep/delete"
export CHATQNA_DATAPREP_GET_FILE_ENDPOINT="http://${HOST_IP_EXTERNAL}:${CHATQNA_REDIS_DATAPREP_PORT}/v1/dataprep/get"
export CHATQNA_DATAPREP_SERVICE_ENDPOINT="http://${HOST_IP_EXTERNAL}:${CHATQNA_REDIS_DATAPREP_PORT}/v1/dataprep/ingest"
export CHATQNA_EMBEDDING_SERVICE_HOST_IP=${HOST_IP}
export CHATQNA_FRONTEND_SERVICE_IP=${HOST_IP}
export CHATQNA_LLM_SERVICE_HOST_IP=${HOST_IP}
export CHATQNA_MEGA_SERVICE_HOST_IP=${HOST_IP}
export CHATQNA_REDIS_URL="redis://${HOST_IP}:${CHATQNA_REDIS_VECTOR_PORT}"
export CHATQNA_RERANK_SERVICE_HOST_IP=${HOST_IP}
export CHATQNA_RETRIEVER_SERVICE_HOST_IP=${HOST_IP}
export CHATQNA_TEI_EMBEDDING_ENDPOINT="http://${HOST_IP}:${CHATQNA_TEI_EMBEDDING_PORT}"

export CHATQNA_BACKEND_SERVICE_NAME=chatqna
export CHATQNA_INDEX_NAME="rag-redis"


function build_docker_images() {
    opea_branch=${opea_branch:-"main"}

    cd $WORKPATH/docker_image_build
    git clone --depth 1 --branch ${opea_branch} https://github.com/opea-project/GenAIComps.git
    pushd GenAIComps
    echo "GenAIComps test commit is $(git rev-parse HEAD)"
    docker build --no-cache -t ${REGISTRY}/comps-base:${TAG} --build-arg https_proxy=$https_proxy --build-arg http_proxy=$http_proxy -f Dockerfile .
    popd && sleep 1s
    git clone --depth 1 https://github.com/vllm-project/vllm.git

    echo "Build all the images with --no-cache, check docker_image_build.log for details..."
    service_list="chatqna chatqna-ui dataprep retriever vllm-rocm nginx"
    docker compose -f build.yaml build ${service_list} --no-cache > ${LOG_PATH}/docker_image_build.log

    docker images && sleep 1s
}

function start_services() {
    cd "$WORKPATH"/docker_compose/amd/gpu/rocm

    # Start Docker Containers
    docker compose -f compose_vllm.yaml up -d > "${LOG_PATH}"/start_services_with_compose.log

    n=0
    until [[ "$n" -ge 500 ]]; do
        docker logs chatqna-vllm-service >& "${LOG_PATH}"/chatqna-vllm-service_start.log
        if grep -q "Application startup complete" "${LOG_PATH}"/chatqna-vllm-service_start.log; then
            break
        fi
        sleep 20s
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
    # Check if the microservices are running correctly.

    # tei for embedding service
    validate_service \
        "${ip_address}:${CHATQNA_TEI_EMBEDDING_PORT}/embed" \
        "\[\[" \
        "tei-embedding" \
        "chatqna-tei-embedding-service" \
        '{"inputs":"What is Deep Learning?"}'

    sleep 1m # retrieval can't curl as expected, try to wait for more time

    # retrieval microservice
    test_embedding=$(python3 -c "import random; embedding = [random.uniform(-1, 1) for _ in range(768)]; print(embedding)")
    validate_service \
        "${ip_address}:${CHATQNA_REDIS_RETRIEVER_PORT}/v1/retrieval" \
        " " \
        "retrieval" \
        "chatqna-retriever" \
        "{\"text\":\"What is the revenue of Nike in 2023?\",\"embedding\":${test_embedding}}"

    # tei for rerank microservice
    validate_service \
        "${ip_address}:${CHATQNA_TEI_RERANKING_PORT}/rerank" \
        '{"index":1,"score":' \
        "tei-rerank" \
        "chatqna-tei-reranking-service" \
        '{"query":"What is Deep Learning?", "texts": ["Deep Learning is not...", "Deep learning is..."]}'

    # vllm for llm service
    validate_service \
        "${ip_address}:${CHATQNA_VLLM_SERVICE_PORT}/v1/chat/completions" \
        "content" \
        "vllm-llm" \
        "chatqna-vllm-service" \
        '{"model": "meta-llama/Meta-Llama-3-8B-Instruct", "messages": [{"role": "user", "content": "What is Deep Learning?"}], "max_tokens": 17}'
}

function validate_megaservice() {
    # Curl the Mega Service
    validate_service \
        "${ip_address}:${CHATQNA_BACKEND_SERVICE_PORT}/v1/chatqna" \
        "data" \
        "mega-chatqna" \
        "chatqna-backend-server" \
        '{"messages": "What is the revenue of Nike in 2023?"}'

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
    cd $WORKPATH/docker_compose/amd/gpu/rocm
    docker compose -f compose_vllm.yaml down
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

    echo "::group::validate_frontend"
    validate_frontend
    echo "::endgroup::"

    echo "::group::stop_docker"
    stop_docker
    echo "::endgroup::"

    docker system prune -f

}

main
