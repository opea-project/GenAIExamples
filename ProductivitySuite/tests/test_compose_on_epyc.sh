#!/bin/bash
# Copyright (C) 2025 Advanced Micro Devices, Inc.
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
mkdir -p "$WORKPATH/tests/logs"
LOG_PATH="$WORKPATH/tests/logs"
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
    docker compose -f build.yaml build --no-cache > ${LOG_PATH}/docker_image_build.log

    docker images && sleep 1s
}

function start_services() {
    cd $WORKPATH/docker_compose/amd/cpu/epyc/
    export host_ip=${ip_address}
    export LOGFLAG=True
    export no_proxy="$no_proxy,tgi_service_codegen,llm_codegen,tei-embedding-service,tei-reranking-service,chatqna-epyc-backend-server,retriever,tgi-service,redis-vector-db,whisper,llm-docsum-tgi,docsum-epyc-backend-server,mongo,codegen"

    source set_env.sh

    # Start Docker Containers
    docker compose up -d > ${LOG_PATH}/start_services_with_compose.log
    sleep 30s

    n=0
    until [[ "$n" -ge 100 ]]; do
        docker logs tgi_service_codegen > ${LOG_PATH}/tgi_service_codegen_start.log 2>&1
        if grep -q Connected ${LOG_PATH}/tgi_service_codegen_start.log; then
            echo "CodeGen TGI Service Connected"
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
    elif [[ $SERVICE_NAME == *"dataprep_upload_link"* ]]; then
        HTTP_RESPONSE=$(curl --silent --write-out "HTTPSTATUS:%{http_code}" -X POST -F 'link_list=["https://www.ces.tech/"]' "$URL")
    elif [[ $SERVICE_NAME == *"dataprep_get"* ]]; then
        HTTP_RESPONSE=$(curl --silent --write-out "HTTPSTATUS:%{http_code}" -X POST -H 'Content-Type: application/json' "$URL")
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
        "${ip_address}:6006/embed" \
        "[[" \
        "tei-embedding" \
        "tei-embedding-server" \
        '{"inputs":"What is Deep Learning?"}'

    sleep 1m # retrieval can't curl as expected, try to wait for more time

    # test /v1/dataprep/delete
    validate_service \
        "http://${ip_address}:6007/v1/dataprep/delete" \
        '{"status":true}' \
        "dataprep_del" \
        "dataprep-redis-server"

    # test /v1/dataprep/ingest upload file
    echo "Deep learning is a subset of machine learning that utilizes neural networks with multiple layers to analyze various levels of abstract data representations. It enables computers to identify patterns and make decisions with minimal human intervention by learning from large amounts of data." > $LOG_PATH/dataprep_file.txt
    validate_service \
        "http://${ip_address}:6007/v1/dataprep/ingest" \
        "Data preparation succeeded" \
        "dataprep_upload_file" \
        "dataprep-redis-server"

    # test /v1/dataprep upload link
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

    # retrieval microservice
    test_embedding=$(python3 -c "import random; embedding = [random.uniform(-1, 1) for _ in range(768)]; print(embedding)")
    validate_service \
        "${ip_address}:7001/v1/retrieval" \
        "retrieved_docs" \
        "retrieval-microservice" \
        "retriever-redis-server" \
        "{\"text\":\"What is the revenue of Nike in 2023?\",\"embedding\":${test_embedding}}"

    # tei for rerank microservice
    validate_service \
        "${ip_address}:8808/rerank" \
        '{"index":1,"score":' \
        "tei-rerank" \
        "tei-reranking-server" \
        '{"query":"What is Deep Learning?", "texts": ["Deep Learning is not...", "Deep learning is..."]}'

    # tgi for llm service
    validate_service \
        "${ip_address}:9009/generate" \
        "generated_text" \
        "tgi-llm" \
        "tgi-service" \
        '{"inputs":"What is Deep Learning?","parameters":{"max_new_tokens":17, "do_sample": true}}'


    # CodeGen llm microservice
    validate_service \
        "${ip_address}:9001/v1/chat/completions" \
        "data: " \
        "llm_codegen" \
        "llm-textgen-server-codegen" \
        '{"query":"def print_hello_world():"}'

    result=$(curl -X 'POST' \
    http://${ip_address}:6012/v1/chathistory/create \
    -H 'accept: application/json' \
    -H 'Content-Type: application/json' \
    -d '{
    "data": {
        "messages": "test Messages", "user": "test"
    }
    }')
        echo $result
        if [[ ${#result} -eq 26 ]]; then
            echo "Correct result."
        else
            echo "Incorrect result."
            exit 1
        fi

        result=$(curl -X 'POST' \
    http://$ip_address:6018/v1/prompt/create \
    -H 'accept: application/json' \
    -H 'Content-Type: application/json' \
    -d '{
        "prompt_text": "test prompt", "user": "test"
    }')
        echo $result
        if [[ ${#result} -eq 26 ]]; then
            echo "Correct result."
        else
            echo "Incorrect result."
            exit 1
        fi

}

function validate_megaservice() {

    # Curl the ChatQnAMega Service
    validate_service \
        "${ip_address}:8888/v1/chatqna" \
        "data: " \
        "chatqna-megaservice" \
        "chatqna-epyc-backend-server" \
        '{"messages": "What is the revenue of Nike in 2023?"}'\

    # Curl the CodeGen Mega Service
    validate_service \
    "${ip_address}:7778/v1/codegen" \
        "print" \
        "codegen-epyc-backend-server" \
        "codegen-epyc-backend-server" \
        '{"messages": "def print_hello_world():"}'
}

function validate_frontend() {
    echo "[ TEST INFO ]: --------- frontend test started ---------"
    cd $WORKPATH/ui/react
    local conda_env_name="OPEA_e2e"
    export PATH=${HOME}/miniforge3/bin/:$PATH

    if conda info --envs | grep -q "^${conda_env_name}[[:space:]]"; then
        echo "[ TEST INFO ]: Conda environment '${conda_env_name}' exists. Activating..."
    else
        echo "[ TEST INFO ]: Conda environment '${conda_env_name}' not found. Creating..."
        conda create -n "${conda_env_name}" python=3.12 -y
    fi
    CONDA_ROOT=$(conda info --base)
    source "${CONDA_ROOT}/etc/profile.d/conda.sh"
    conda activate ${conda_env_name}
    echo "[ TEST INFO ]: --------- conda env activated ---------"

    conda install -c conda-forge nodejs=22.6.0 -y
    npm install && npm ci
    node -v && npm -v && pip list

    exit_status=0
    npm run test || exit_status=$?

    if [ $exit_status -ne 0 ]; then
        echo "[TEST INFO]: ---------frontend test failed---------"
        exit $exit_status
    else
        echo "[TEST INFO]: ---------frontend test passed---------"
    fi
}

function stop_docker() {
    cd $WORKPATH/docker_compose/amd/cpu/epyc/
    docker compose stop && docker compose rm -f
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

    echo "::group::validate_frontend"
    validate_frontend
    echo "::endgroup::"

    echo "::group::stop_docker"
    stop_docker
    echo "::endgroup::"

    docker system prune -f

}

main
