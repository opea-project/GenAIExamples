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
    cd $WORKPATH/docker_image_build
    git clone https://github.com/opea-project/GenAIComps.git && cd GenAIComps && git checkout "${opea_branch:-"main"}" && cd ../

    echo "Build all the images with --no-cache, check docker_image_build.log for details..."
    service_list="chatqna-guardrails chatqna-ui dataprep-redis retriever-redis guardrails-tgi nginx"
    docker compose -f build.yaml build ${service_list} --no-cache > ${LOG_PATH}/docker_image_build.log

    docker pull ghcr.io/huggingface/tgi-gaudi:2.0.6
    docker pull ghcr.io/huggingface/text-embeddings-inference:cpu-1.5
    docker pull ghcr.io/huggingface/tei-gaudi:1.5.0

    docker images && sleep 1s
}

function start_services() {
    cd $WORKPATH/docker_compose/intel/hpu/gaudi
    export EMBEDDING_MODEL_ID="BAAI/bge-base-en-v1.5"
    export RERANK_MODEL_ID="BAAI/bge-reranker-base"
    export LLM_MODEL_ID="Intel/neural-chat-7b-v3-3"
    export INDEX_NAME="rag-redis"
    export HUGGINGFACEHUB_API_TOKEN=${HUGGINGFACEHUB_API_TOKEN}
    export GURADRAILS_MODEL_ID="meta-llama/Meta-Llama-Guard-2-8B"

    # Start Docker Containers
    docker compose -f compose_guardrails.yaml up -d > ${LOG_PATH}/start_services_with_compose.log
    n=0
    until [[ "$n" -ge 100 ]]; do
        docker logs tgi-gaudi-server > tgi_service_start.log
        if grep -q Connected tgi_service_start.log; then
            break
        fi
        sleep 5s
        n=$((n+1))
    done

    # Make sure tgi guardrails service is ready
    n=0
    until [[ "$n" -ge 100 ]]; do
        docker logs tgi-guardrails-server > tgi_guardrails_service_start.log
        if grep -q Connected tgi_guardrails_service_start.log; then
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

    HTTP_RESPONSE=$(curl --silent --write-out "HTTPSTATUS:%{http_code}" -X POST -d "$INPUT_DATA" -H 'Content-Type: application/json' "$URL")
    HTTP_STATUS=$(echo $HTTP_RESPONSE | tr -d '\n' | sed -e 's/.*HTTPSTATUS://')
    RESPONSE_BODY=$(echo $HTTP_RESPONSE | sed -e 's/HTTPSTATUS\:.*//g')

    docker logs ${DOCKER_NAME} >> ${LOG_PATH}/${SERVICE_NAME}.log

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
    validate_services \
        "${ip_address}:8090/embed" \
        "[[" \
        "tei-embedding" \
        "tei-embedding-gaudi-server" \
        '{"inputs":"What is Deep Learning?"}'

    sleep 1m # retrieval can't curl as expected, try to wait for more time

    # retrieval microservice
    test_embedding=$(python3 -c "import random; embedding = [random.uniform(-1, 1) for _ in range(768)]; print(embedding)")
    validate_services \
        "${ip_address}:7000/v1/retrieval" \
        "retrieved_docs" \
        "retrieval" \
        "retriever-redis-server" \
        "{\"text\":\"What is the revenue of Nike in 2023?\",\"embedding\":${test_embedding}}"

    # tei for rerank microservice
    validate_services \
        "${ip_address}:8808/rerank" \
        '{"index":1,"score":' \
        "tei-rerank" \
        "tei-reranking-gaudi-server" \
        '{"query":"What is Deep Learning?", "texts": ["Deep Learning is not...", "Deep learning is..."]}'

    # tgi for llm service
    validate_services \
        "${ip_address}:8008/generate" \
        "generated_text" \
        "tgi-llm" \
        "tgi-gaudi-server" \
        '{"inputs":"What is Deep Learning?","parameters":{"max_new_tokens":17, "do_sample": true}}'

    # guardrails microservice
    validate_services \
        "${ip_address}:9090/v1/guardrails" \
        "Violated policies" \
        "guardrails" \
        "guardrails-tgi-gaudi-server" \
        '{"text":"How do you buy a tiger in the US?"}'
}

function validate_megaservice() {
    # Curl the Mega Service
    validate_services \
        "${ip_address}:8888/v1/chatqna" \
        "data: " \
        "mega-chatqna" \
        "chatqna-gaudi-guardrails-server" \
        '{"messages": "What is the revenue of Nike in 2023?"}'

}

function validate_frontend() {
    cd $WORKPATH/ui/svelte
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
    cd $WORKPATH/docker_compose/intel/hpu/gaudi
    docker compose -f compose_guardrails.yaml down
}

function main() {

    stop_docker
    if [[ "$IMAGE_REPO" == "opea" ]]; then build_docker_images; fi
    start_time=$(date +%s)
    start_services
    end_time=$(date +%s)
    duration=$((end_time-start_time))
    echo "Mega service start duration is $duration s"

    validate_microservices
    validate_megaservice
    validate_frontend

    stop_docker
    echo y | docker system prune

}

main
