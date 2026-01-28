#!/bin/bash
# Copyright (C) 2025 Intel Corporation
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

function build_docker_images() {
    opea_branch=${opea_branch:-"main"}

    cd $WORKPATH/docker_image_build
    git clone --depth 1 --branch ${opea_branch} https://github.com/opea-project/GenAIComps.git
    pushd GenAIComps
    echo "GenAIComps test commit is $(git rev-parse HEAD)"
    docker build --no-cache -t ${REGISTRY}/comps-base:${TAG} --build-arg https_proxy=$https_proxy --build-arg http_proxy=$http_proxy -f Dockerfile .
    popd && sleep 1s

    echo "Build all the images with --no-cache, check docker_image_build.log for details..."
    service_list="codegen codegen-ui llm-textgen dataprep retriever embedding"

    docker compose -f build.yaml build ${service_list} --no-cache > ${LOG_PATH}/docker_image_build.log

    docker images && sleep 1s
}

function start_services() {
    cd $WORKPATH/docker_compose/intel/cpu/xeon/
    export LOGFLAG=true
    export no_proxy="localhost,127.0.0.1,$ip_address"

    # openGauss configuration
    export GS_USER="gaussdb"
    export GS_PASSWORD="openGauss@123"
    export GS_DB="postgres"
    export GS_CONNECTION_STRING="opengauss+psycopg2://${GS_USER}:${GS_PASSWORD}@$ip_address:5432/${GS_DB}"

    source $WORKPATH/docker_compose/intel/set_env_opengauss.sh

    # Start Docker Containers
    docker compose -f compose_opengauss.yaml up -d --quiet-pull > ${LOG_PATH}/start_services_with_compose.log

    n=0
    until [[ "$n" -ge 100 ]]; do
        docker logs vllm-server > ${LOG_PATH}/vllm_service_start.log 2>&1
        if grep -q complete ${LOG_PATH}/vllm_service_start.log; then
            break
        fi
        sleep 5s
        n=$((n+1))
    done
}

function validate_service() {
    local URL="$1"
    local EXPECTED_RESULT="$2"
    local SERVICE_NAME="$3"
    local DOCKER_NAME="$4"
    local INPUT_DATA="$5"

    if [[ $SERVICE_NAME == *"dataprep_upload_file"* ]]; then
        cd $LOG_PATH
        HTTP_RESPONSE=$(curl --silent --write-out "HTTPSTATUS:%{http_code}" -X POST -F 'files=@./dataprep_file.txt' -H 'Content-Type: multipart/form-data' "$URL")
    elif [[ $SERVICE_NAME == *"dataprep_del"* ]]; then
        HTTP_RESPONSE=$(curl --silent --write-out "HTTPSTATUS:%{http_code}" -X POST -d '{"file_path": "all"}' -H 'Content-Type: application/json' "$URL")
    else
        HTTP_RESPONSE=$(curl --silent --write-out "HTTPSTATUS:%{http_code}" -X POST -d "$INPUT_DATA" -H 'Content-Type: application/json' "$URL")
    fi
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
    echo "Response"
    echo $RESPONSE_BODY
    echo "Expected Result"
    echo $EXPECTED_RESULT
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
        "tei-embedding-serving" \
        '{"inputs":"What is Deep Learning?"}'

    sleep 1m # retrieval can't curl as expected, try to wait for more time

    # test /v1/dataprep/ingest upload file
    echo "Deep learning is a subset of machine learning that utilizes neural networks with multiple layers to analyze various levels of abstract data representations. It enables computers to identify patterns and make decisions with minimal human intervention by learning from large amounts of data." > $LOG_PATH/dataprep_file.txt
    validate_service \
       "http://${ip_address}:6007/v1/dataprep/ingest" \
        "Data preparation succeeded" \
        "dataprep_upload_file" \
        "dataprep-opengauss-server"

    # test /v1/dataprep/delete
    validate_service \
       "http://${ip_address}:6007/v1/dataprep/delete" \
       '{"status":true}' \
        "dataprep_del" \
        "dataprep-opengauss-server"

    # retrieval microservice
    test_embedding=$(python3 -c "import random; embedding = [random.uniform(-1, 1) for _ in range(768)]; print(embedding)")
    validate_service \
        "${ip_address}:7000/v1/retrieval" \
        " " \
        "retrieval" \
        "retriever-opengauss-server" \
        "{\"text\":\"What is Deep Learning?\",\"embedding\":${test_embedding}}"

    # vllm for llm service
    echo "Validating llm service"
    validate_service \
        "${ip_address}:8028/v1/chat/completions" \
        "content" \
        "vllm-llm" \
        "vllm-server" \
        '{"model": "Qwen/Qwen2.5-Coder-7B-Instruct", "messages": [{"role": "user", "content": "What is Deep Learning?"}], "max_tokens": 17}'
}

function validate_megaservice() {
    # Curl the Mega Service
    validate_service \
        "${ip_address}:7778/v1/codegen" \
        "print" \
        "codegen-megaservice" \
        "codegen-xeon-backend-server" \
        '{"messages": "def print_hello_world():", "max_tokens": 256}'

    # Curl the Mega Service with stream as false
    validate_service \
        "${ip_address}:7778/v1/codegen" \
        "" \
        "codegen-megaservice-nostream" \
        "codegen-xeon-backend-server" \
        '{"messages": "def print_hello_world():", "max_tokens": 256, "stream": false}'

    # Curl the Mega Service with OpenAI format
    validate_service \
        "${ip_address}:7778/v1/codegen" \
        "class" \
        "codegen-megaservice-openai" \
        "codegen-xeon-backend-server" \
        '{"model": "Qwen/Qwen2.5-Coder-7B-Instruct", "messages": [{"role": "user", "content": "Implement a basic Python class"}], "max_tokens":32}'
}

function stop_docker() {
    echo "In stop docker"
    echo $WORKPATH
    cd $WORKPATH/docker_compose/intel/cpu/xeon/
    docker compose -f compose_opengauss.yaml down
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
