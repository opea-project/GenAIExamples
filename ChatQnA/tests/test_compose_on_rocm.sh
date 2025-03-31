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
export MODEL_CACHE=${model_cache:-"/var/opea/chatqna-service/data"}

WORKPATH=$(dirname "$PWD")
LOG_PATH="$WORKPATH/tests"
ip_address=$(hostname -I | awk '{print $1}')

export HOST_IP=${ip_address}
export CHATQNA_TGI_SERVICE_IMAGE="ghcr.io/huggingface/text-generation-inference:2.3.1-rocm"
export CHATQNA_EMBEDDING_MODEL_ID="BAAI/bge-base-en-v1.5"
export CHATQNA_RERANK_MODEL_ID="BAAI/bge-reranker-base"
export CHATQNA_LLM_MODEL_ID="meta-llama/Meta-Llama-3-8B-Instruct"
export CHATQNA_TGI_SERVICE_PORT=9009
export CHATQNA_TEI_EMBEDDING_PORT=8090
export CHATQNA_TEI_EMBEDDING_ENDPOINT="http://${HOST_IP}:${CHATQNA_TEI_EMBEDDING_PORT}"
export CHATQNA_TEI_RERANKING_PORT=8808
export CHATQNA_REDIS_VECTOR_PORT=6379
export CHATQNA_REDIS_VECTOR_INSIGHT_PORT=8001
export CHATQNA_REDIS_DATAPREP_PORT=6007
export CHATQNA_REDIS_RETRIEVER_PORT=7000
export CHATQNA_INDEX_NAME="rag-redis"
export CHATQNA_MEGA_SERVICE_HOST_IP=${HOST_IP}
export CHATQNA_RETRIEVER_SERVICE_HOST_IP=${HOST_IP}
export CHATQNA_BACKEND_SERVICE_ENDPOINT="http://127.0.0.1:${CHATQNA_BACKEND_SERVICE_PORT}/v1/chatqna"
export CHATQNA_DATAPREP_SERVICE_ENDPOINT="http://127.0.0.1:${CHATQNA_REDIS_DATAPREP_PORT}/v1/dataprep/ingest"
export CHATQNA_DATAPREP_GET_FILE_ENDPOINT="http://127.0.0.1:${CHATQNA_REDIS_DATAPREP_PORT}/v1/dataprep/get"
export CHATQNA_DATAPREP_DELETE_FILE_ENDPOINT="http://127.0.0.1:${CHATQNA_REDIS_DATAPREP_PORT}/v1/dataprep/delete"
export CHATQNA_FRONTEND_SERVICE_IP=${HOST_IP}
export CHATQNA_FRONTEND_SERVICE_PORT=15173
export CHATQNA_BACKEND_SERVICE_NAME=chatqna
export CHATQNA_BACKEND_SERVICE_IP=${HOST_IP}
export CHATQNA_BACKEND_SERVICE_PORT=8888
export CHATQNA_REDIS_URL="redis://${HOST_IP}:${CHATQNA_REDIS_VECTOR_PORT}"
export CHATQNA_EMBEDDING_SERVICE_HOST_IP=${HOST_IP}
export CHATQNA_RERANK_SERVICE_HOST_IP=${HOST_IP}
export CHATQNA_LLM_SERVICE_HOST_IP=${HOST_IP}
export CHATQNA_NGINX_PORT=80
export CHATQNA_HUGGINGFACEHUB_API_TOKEN=${HUGGINGFACEHUB_API_TOKEN}
export PATH="~/miniconda3/bin:$PATH"

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
    service_list="chatqna chatqna-ui dataprep retriever nginx"
    docker compose -f build.yaml build ${service_list} --no-cache > "${LOG_PATH}"/docker_image_build.log

    docker pull ghcr.io/huggingface/text-generation-inference:2.3.1-rocm
    docker pull ghcr.io/huggingface/text-embeddings-inference:cpu-1.5

    docker images && sleep 1s
}

function start_services() {
    cd "$WORKPATH"/docker_compose/amd/gpu/rocm

    # Start Docker Containers
    docker compose -f compose.yaml up -d > "${LOG_PATH}"/start_services_with_compose.log

    n=0
    until [[ "$n" -ge 160 ]]; do
        docker logs chatqna-tgi-server > "${LOG_PATH}"/tgi_service_start.log
        if grep -q Connected "${LOG_PATH}"/tgi_service_start.log; then
            break
        fi
        sleep 5s
        n=$((n+1))
    done

    echo "all containers start!"
}

function validate_service() {
    local URL="$1"
    local EXPECTED_RESULT="$2"
    local SERVICE_NAME="$3"
    local DOCKER_NAME="$4"
    local INPUT_DATA="$5"

    if [[ $SERVICE_NAME == *"dataprep_upload_file"* ]]; then
        cd "$LOG_PATH"
        HTTP_RESPONSE=$(curl --silent --write-out "HTTPSTATUS:%{http_code}" -X POST -F 'files=@./dataprep_file.txt' -H 'Content-Type: multipart/form-data' "$URL")
    elif [[ $SERVICE_NAME == *"dataprep_upload_link"* ]]; then
        HTTP_RESPONSE=$(curl --silent --write-out "HTTPSTATUS:%{http_code}" -X POST -F 'link_list=["https://www.ces.tech/"]' "$URL")
    elif [[ $SERVICE_NAME == *"dataprep_get"* ]]; then
        HTTP_RESPONSE=$(curl --silent --write-out "HTTPSTATUS:%{http_code}" -X POST -H 'Content-Type: application/json' "$URL")
    elif [[ $SERVICE_NAME == *"dataprep_del"* ]]; then
        HTTP_RESPONSE=$(curl --silent --write-out "HTTPSTATUS:%{http_code}" -X POST -d '{"file_path": "all"}' -H 'Content-Type: application/json' "$URL")
    else
        HTTP_RESPONSE=$(curl --silent --write-out "HTTPSTATUS:%{http_code}" -X POST -d "$INPUT_DATA" -H 'Content-Type: application/json' "$URL")
    fi
    HTTP_STATUS=$(echo "$HTTP_RESPONSE" | tr -d '\n' | sed -e 's/.*HTTPSTATUS://')
    RESPONSE_BODY=$(echo "$HTTP_RESPONSE" | sed -e 's/HTTPSTATUS\:.*//g')

    docker logs "${DOCKER_NAME}" >> "${LOG_PATH}"/"${SERVICE_NAME}".log

    # check response status
    if [ "$HTTP_STATUS" -ne "200" ]; then
        echo "[ $SERVICE_NAME ] HTTP status is not 200. Received status was $HTTP_STATUS"
        exit 1
    else
        echo "[ $SERVICE_NAME ] HTTP status is 200. Checking content..."
    fi
    # check response body
    if [[ "$RESPONSE_BODY" != *"$EXPECTED_RESULT"* ]]; then
        echo "[ $SERVICE_NAME ] Content does not match the expected result: $RESPONSE_BODY"
        exit 1
    else
        echo "[ $SERVICE_NAME ] Content is as expected."
    fi

    sleep 1s
}

function validate_microservices() {
    # Check if the microservices are running correctly.

    # tei for embedding service
    validate_service \
        "${ip_address}:8090/embed" \
        "[[" \
        "tei-embedding" \
        "chatqna-tei-embedding-server" \
        '{"inputs":"What is Deep Learning?"}'

    sleep 1m # retrieval can't curl as expected, try to wait for more time

    # test /v1/dataprep/ingest upload file
    echo "Deep learning is a subset of machine learning that utilizes neural networks with multiple layers to analyze various levels of abstract data representations. It enables computers to identify patterns and make decisions with minimal human intervention by learning from large amounts of data." > "$LOG_PATH"/dataprep_file.txt
    validate_service \
        "http://${ip_address}:6007/v1/dataprep/ingest" \
        "Data preparation succeeded" \
        "dataprep_upload_file" \
        "dataprep-redis-server"

    # test /v1/dataprep/ingest upload link
    validate_service \
        "http://${ip_address}:6007/v1/dataprep/ingest" \
        "Data preparation succeeded" \
        "dataprep_upload_link" \
        "dataprep-redis-server"

    # test /v1/dataprep/get
    validate_service \
        "http://${ip_address}:6007/v1/dataprep/get" \
        '{"name":' \
        "dataprep_get" \
        "dataprep-redis-server"

    # test /v1/dataprep/delete
    validate_service \
        "http://${ip_address}:6007/v1/dataprep/delete" \
        '{"status":true}' \
        "dataprep_del" \
        "dataprep-redis-server"

    # retrieval microservice
    test_embedding=$(python3 -c "import random; embedding = [random.uniform(-1, 1) for _ in range(768)]; print(embedding)")
    validate_service \
        "${ip_address}:7000/v1/retrieval" \
        "retrieved_docs" \
        "retrieval-microservice" \
        "chatqna-retriever-redis-server" \
        "{\"text\":\"What is the revenue of Nike in 2023?\",\"embedding\":${test_embedding}}"

    # tei for rerank microservice
    validate_service \
        "${ip_address}:8808/rerank" \
        '{"index":1,"score":' \
        "tei-rerank" \
        "chatqna-tei-reranking-server" \
        '{"query":"What is Deep Learning?", "texts": ["Deep Learning is not...", "Deep learning is..."]}'

    # tgi for llm service
    validate_service \
        "${ip_address}:9009/generate" \
        "generated_text" \
        "tgi-llm" \
        "chatqna-tgi-server" \
        '{"inputs":"What is Deep Learning?","parameters":{"max_new_tokens":17, "do_sample": true}}'

}

function validate_megaservice() {
    # Curl the Mega Service
    validate_service \
        "${ip_address}:8888/v1/chatqna" \
        "Nike" \
        "chatqna-megaservice" \
        "chatqna-backend-server" \
        '{"messages": "What is the revenue of Nike in 2023?"}'

}

function validate_frontend() {
    echo "[ TEST INFO ]: --------- frontend test started ---------"
    cd "$WORKPATH"/ui/svelte
    local conda_env_name="OPEA_e2e"
    export PATH=${HOME}/miniforge3/bin/:$PATH
    if conda info --envs | grep -q "$conda_env_name"; then
        echo "$conda_env_name exist!"
    else
        conda create -n ${conda_env_name} python=3.12 -y
    fi
    source activate ${conda_env_name}
    echo "[ TEST INFO ]: --------- conda env activated ---------"

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
    start_time=$(date +%s)
    start_services
    end_time=$(date +%s)
    duration=$((end_time-start_time))
    echo "Mega service start duration is $duration s" && sleep 1s

    validate_microservices
    echo "==== microservices validated ===="
    validate_megaservice
    echo "==== megaservice validated ===="
    validate_frontend
    echo "==== frontend validated ===="

    stop_docker
    echo y | docker system prune

}

main
