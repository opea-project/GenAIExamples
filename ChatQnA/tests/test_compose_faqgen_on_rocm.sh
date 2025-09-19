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
export MODEL_CACHE=${model_cache:-"./data"}

WORKPATH=$(dirname "$PWD")
LOG_PATH="$WORKPATH/tests"
ip_address=$(hostname -I | awk '{print $1}')

source $WORKPATH/docker_compose/amd/gpu/rocm/set_env_faqgen.sh

export PATH="$HOME/miniconda3/bin:$PATH"

function build_docker_images() {
    opea_branch=${opea_branch:-"main"}
    cd $WORKPATH/docker_image_build
    git clone --depth 1 --branch ${opea_branch} https://github.com/opea-project/GenAIComps.git
    pushd GenAIComps
    echo "GenAIComps test commit is $(git rev-parse HEAD)"
    docker build --no-cache -t ${REGISTRY}/comps-base:${TAG} --build-arg https_proxy=$https_proxy --build-arg http_proxy=$http_proxy -f Dockerfile .
    popd && sleep 1s

    echo "Build all the images with --no-cache, check docker_image_build.log for details..."
    service_list="chatqna chatqna-ui dataprep retriever llm-faqgen nginx"
    docker compose -f build.yaml build ${service_list} --no-cache > "${LOG_PATH}"/docker_image_build.log

    docker images && sleep 1s
}

function start_services() {
    cd "$WORKPATH"/docker_compose/amd/gpu/rocm

    # Start Docker Containers
    docker compose -f compose_faqgen.yaml up -d --quiet-pull > "${LOG_PATH}"/start_services_with_compose.log

    n=0
    until [[ "$n" -ge 160 ]]; do
        docker logs chatqna-tgi-service > "${LOG_PATH}"/tgi_service_start.log 2>&1
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
        "${ip_address}:${CHATQNA_TEI_EMBEDDING_PORT}/embed" \
        "[[" \
        "tei-embedding" \
        "chatqna-tei-embedding-service" \
        '{"inputs":"What is Deep Learning?"}'

    sleep 1m # retrieval can't curl as expected, try to wait for more time

    # retrieval microservice
    test_embedding=$(python3 -c "import random; embedding = [random.uniform(-1, 1) for _ in range(768)]; print(embedding)")
    validate_service \
        "${ip_address}:${CHATQNA_REDIS_RETRIEVER_PORT}/v1/retrieval" \
        " " \
        "retrieval-microservice" \
        "chatqna-retriever" \
        "{\"text\":\"What is the revenue of Nike in 2023?\",\"embedding\":${test_embedding}}"

    # tei for rerank microservice
    validate_service \
        "${ip_address}:${CHATQNA_TEI_RERANKING_PORT}/rerank" \
        '{"index":1,"score":' \
        "tei-rerank" \
        "chatqna-tei-reranking-service" \
        '{"query":"What is Deep Learning?", "texts": ["Deep Learning is not...", "Deep learning is..."]}'

    # tgi for llm service
    validate_service \
        "${ip_address}:${CHATQNA_TGI_SERVICE_PORT}/generate" \
        "generated_text" \
        "tgi-llm" \
        "chatqna-tgi-service" \
        '{"inputs":"What is Deep Learning?","parameters":{"max_new_tokens":17, "do_sample": true}}'

    # faqgen llm microservice
    echo "validate llm-faqgen..."
    validate_service \
        "${ip_address}:${CHATQNA_LLM_FAQGEN_PORT}/v1/faqgen" \
        "text" \
        "llm" \
        "chatqna-llm-faqgen" \
        '{"messages":"Text Embeddings Inference (TEI) is a toolkit for deploying and serving open source text embeddings and sequence classification models. TEI enables high-performance extraction for the most popular models, including FlagEmbedding, Ember, GTE and E5."}'

}

function validate_megaservice() {
    # Curl the Mega Service
    validate_service \
        "${ip_address}:${CHATQNA_BACKEND_SERVICE_PORT}/v1/chatqna" \
        "Embed" \
        "chatqna-megaservice" \
        "chatqna-backend-server" \
        '{"messages": "Text Embeddings Inference (TEI) is a toolkit for deploying and serving open source text embeddings and sequence classification models. TEI enables high-performance extraction for the most popular models, including FlagEmbedding, Ember, GTE and E5.","max_tokens":32}'

    validate_service \
        "${ip_address}:${CHATQNA_BACKEND_SERVICE_PORT}/v1/chatqna" \
        "Embed" \
        "chatqna-megaservice" \
        "chatqna-backend-server" \
        '{"messages": "Text Embeddings Inference (TEI) is a toolkit for deploying and serving open source text embeddings and sequence classification models. TEI enables high-performance extraction for the most popular models, including FlagEmbedding, Ember, GTE and E5.","max_tokens":32,"stream":false}'

}

function stop_docker() {
    cd "$WORKPATH"/docker_compose/amd/gpu/rocm
    docker compose -f compose_faqgen.yaml stop && docker compose rm -f
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

    echo "::group::stop_docker"
    stop_docker
    echo "::endgroup::"

    docker system prune -f

}

main
