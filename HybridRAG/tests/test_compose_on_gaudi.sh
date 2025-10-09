#!/bin/bash
# Copyright (C) 2025 Intel Corporation
# SPDX-License-Identifier: Apache-2.0

set -e
IMAGE_REPO=${IMAGE_REPO:-"opea"}
IMAGE_TAG=${IMAGE_TAG:-"latest"}
echo "REGISTRY=IMAGE_REPO=${IMAGE_REPO}"
echo "TAG=IMAGE_TAG=${IMAGE_TAG}"
export REGISTRY=${IMAGE_REPO}
export TAG=${IMAGE_TAG}
export MODEL_CACHE=${model_cache:-"./data"}

WORKPATH=$(dirname "$PWD")
LOG_PATH="$WORKPATH/tests"
ip_address=$(hostname -I | awk '{print $1}')

cd $WORKPATH/docker_compose/intel/hpu/gaudi
source set_env.sh

function build_docker_images() {
    opea_branch=${opea_branch:-"main"}
    cd $WORKPATH/docker_image_build
    git clone --depth 1 --branch ${opea_branch} https://github.com/opea-project/GenAIComps.git
    pushd GenAIComps
    echo "GenAIComps test commit is $(git rev-parse HEAD)"
    docker build --no-cache -t ${REGISTRY}/comps-base:${TAG} --build-arg https_proxy=$https_proxy --build-arg http_proxy=$http_proxy -f Dockerfile .
    popd && sleep 1s

    echo "Build all the images with --no-cache, check docker_image_build.log for details..."
    service_list="hybridrag hybridrag-ui dataprep retriever text2query-cypher nginx"
    docker compose -f build.yaml build ${service_list} --no-cache > ${LOG_PATH}/docker_image_build.log 2>&1

    docker images && sleep 1s
}

function start_services() {
    cd $WORKPATH/docker_compose/intel/hpu/gaudi
    export no_proxy="localhost,127.0.0.1,$ip_address"
    # Start Docker Containers
    docker compose -f compose.yaml up -d > ${LOG_PATH}/start_services_with_compose.log
    n=0
    until [[ "$n" -ge 100 ]]; do
        docker logs vllm-service > ${LOG_PATH}/vllm_service_start.log 2>&1
        if grep -q complete ${LOG_PATH}/vllm_service_start.log; then
            break
        fi
        sleep 5s
        n=$((n+1))
    done
}

function dataprep() {
    cd $WORKPATH/tests/data
    sleep 25s
    URL="http://${ip_address}:6007/v1/dataprep/ingest"
    local CONTENT=$(curl -X POST -H "Content-Type: multipart/form-data" -F "files=@./Diabetes.txt" -F "files=@./Acne_Vulgaris.txt" -F "chunk_size=300" -F "chunk_overlap=20" "$URL")
    if echo "$CONTENT" | grep -q "Data preparation succeeded"; then
        echo "Data preparation succeeded."
    else
        echo "Data preparation failed."
        exit 1
    fi
}

function validate_service() {
    local URL="$1"
    local EXPECTED_RESULT="$2"
    local SERVICE_NAME="$3"
    local DOCKER_NAME="$4"
    local INPUT_DATA="$5"

    local HTTP_STATUS=$(curl -s -o /dev/null -w "%{http_code}" -X POST -d "$INPUT_DATA" -H 'Content-Type: application/json' "$URL")

    if [ "$DOCKER_NAME" = "text2query-cypher-gaudi-container" ]; then
        docker ps
        docker logs text2query-cypher-gaudi-container
    fi

    if [ "$HTTP_STATUS" -eq 200 ]; then
        echo "[ $SERVICE_NAME ] HTTP status is 200. Checking content..."

        local CONTENT=$(curl -s -X POST -d "$INPUT_DATA" -H 'Content-Type: application/json' "$URL" | tee ${LOG_PATH}/${SERVICE_NAME}.log)

        if echo "$CONTENT" | grep -q "$EXPECTED_RESULT"; then
            echo "[ $SERVICE_NAME ] Content is as expected."
        else
            echo "[ $SERVICE_NAME ] Content does not match the expected result: $CONTENT"
            docker logs ${DOCKER_NAME} >> ${LOG_PATH}/${SERVICE_NAME}.log
            if [ "$DOCKER_NAME" = "hybridrag-xeon-backend-server" ]; then
                docker ps
                docker logs text2query-cypher-gaudi-container
            fi
            exit 1
        fi
    else
        echo "[ $SERVICE_NAME ] HTTP status is not 200. Received status was $HTTP_STATUS"
        docker logs ${DOCKER_NAME} >> ${LOG_PATH}/${SERVICE_NAME}.log
        if [ "$DOCKER_NAME" = "hybridrag-xeon-backend-server" ]; then
            docker ps
            docker logs text2query-cypher-gaudi-container
        fi
        exit 1
    fi
    sleep 1s
}

function validate_microservices() {
    # Check if the microservices are running correctly.

    # tei for embedding service
    validate_service \
        "${ip_address}:6006/embed" \
        "\[\[" \
        "tei-embedding" \
        "tei-embedding-server" \
        '{"inputs":"What is Deep Learning?"}'

    sleep 1m # retrieval can't curl as expected, try to wait for more time

    # retrieval microservice
    test_embedding=$(python3 -c "import random; embedding = [random.uniform(-1, 1) for _ in range(768)]; print(embedding)")
    validate_service \
        "${ip_address}:7000/v1/retrieval" \
        " " \
        "retriever" \
        "retriever-redis-server" \
        "{\"text\":\"What is the revenue of Nike in 2023?\",\"embedding\":${test_embedding}}"

    # tei for rerank microservice
    validate_service \
        "${ip_address}:8808/rerank" \
        '{"index":1,"score":' \
        "tei-reranking-service" \
        "tei-reranking-server" \
        '{"query":"What is Deep Learning?", "texts": ["Deep Learning is not...", "Deep learning is..."]}'

    # vllm for llm service
    validate_service \
        "${ip_address}:9009/v1/chat/completions" \
        "content" \
        "vllm-service" \
        "vllm-service" \
        '{"model": "meta-llama/Meta-Llama-3-8B-Instruct", "messages": [{"role": "user", "content": "What is Deep Learning?"}], "max_tokens": 17}'
}

function validate_megaservice() {
    # Curl the Mega Service
    validate_service \
        "${ip_address}:8888/v1/hybridrag" \
        "data" \
        "hybridrag-xeon-backend-server" \
        "hybridrag-xeon-backend-server" \
        '{"messages": "what are the symptoms for Diabetes?"}'

}

function validate_text2cypher() {
    # text2query-cypher service
    validate_service \
        "${ip_address}:11801/v1/text2query" \
        "\[" \
        "text2cypher-gaudi" \
        "text2query-cypher-gaudi-container" \
        '{"query": "what are the symptoms for Diabetes?"}'
}

function stop_docker() {
    cd $WORKPATH/docker_compose/intel/hpu/gaudi
    docker compose -f compose.yaml down
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

    echo "::group::dataprep"
    dataprep
    echo "::endgroup::"

    echo "::group::validate_megaservice"
    validate_megaservice
    echo "::endgroup::"

    echo "::group::stop_docker"
    stop_docker
    echo "::endgroup::"

    docker system prune -f

}

main
