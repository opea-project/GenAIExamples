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
export MODEL_CACHE=${model_cache:-"./data"}

WORKPATH=$(dirname "$PWD")
LOG_PATH="$WORKPATH/tests"
ip_address=$(hostname -I | awk '{print $1}')
source $WORKPATH/docker_compose/intel/set_env.sh

function build_docker_images() {
    opea_branch=${opea_branch:-"main"}

    cd $WORKPATH/docker_image_build
    git clone --depth 1 --branch ${opea_branch} https://github.com/opea-project/GenAIComps.git
    pushd GenAIComps
    echo "GenAIComps test commit is $(git rev-parse HEAD)"
    docker build --no-cache -t ${REGISTRY}/comps-base:${TAG} --build-arg https_proxy=$https_proxy --build-arg http_proxy=$http_proxy -f Dockerfile .
    popd && sleep 1s

    git clone https://github.com/vllm-project/vllm.git && cd vllm
    VLLM_VER=v0.9.0
    echo "Check out vLLM tag ${VLLM_VER}"
    git checkout ${VLLM_VER} &> /dev/null
    cd ../

    echo "Build all the images with --no-cache, check docker_image_build.log for details..."
    service_list="codegen codegen-gradio-ui llm-textgen vllm dataprep retriever embedding"

    docker compose -f build.yaml build ${service_list} --no-cache > ${LOG_PATH}/docker_image_build.log

    docker pull ghcr.io/huggingface/text-generation-inference:2.4.0-intel-cpu
    docker images && sleep 1s
}

function start_services() {
    local compose_profile="$1"
    local llm_container_name="$2"

    cd $WORKPATH/docker_compose/intel/cpu/xeon/

    # Start Docker Containers
    docker compose --profile ${compose_profile} up -d > ${LOG_PATH}/start_services_with_compose.log

    n=0
    until [[ "$n" -ge 100 ]]; do
        docker logs ${llm_container_name} > ${LOG_PATH}/llm_service_start.log 2>&1
        if grep -E "Connected|complete" ${LOG_PATH}/llm_service_start.log; then
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

    if [[ "$SERVICE_NAME" == "ingest" ]]; then
        local HTTP_STATUS=$(curl -s -o /dev/null -w "%{http_code}" -X POST -F "$INPUT_DATA" -F index_name=test_redis -H 'Content-Type: multipart/form-data' "$URL")

        if [ "$HTTP_STATUS" -eq 200 ]; then
            echo "[ $SERVICE_NAME ] HTTP status is 200. Data preparation succeeded..."
        else
            echo "[ $SERVICE_NAME ] Data preparation failed..."
        fi

    else
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
    fi
    sleep 5s
}

function validate_microservices() {
    local llm_container_name="$1"

    # tgi for llm service
    validate_services \
        "${ip_address}:8028/v1/chat/completions" \
        "completion_tokens" \
        "llm-service" \
        "${llm_container_name}" \
        '{"model": "Qwen/Qwen2.5-Coder-7B-Instruct", "messages": [{"role": "user", "content": "What is Deep Learning?"}], "max_tokens": 256}'

    # llm microservice
    validate_services \
        "${ip_address}:9000/v1/chat/completions" \
        "data: " \
        "llm" \
        "llm-textgen-server" \
        '{"query":"def print_hello_world():", "max_tokens": 256}'

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
        "${ip_address}:7778/v1/codegen" \
        "print" \
        "mega-codegen" \
        "codegen-xeon-backend-server" \
        '{"messages": "def print_hello_world():", "max_tokens": 256}'

    # Curl the Mega Service with index_name and agents_flag
    validate_services \
        "${ip_address}:7778/v1/codegen" \
        "" \
        "mega-codegen" \
        "codegen-xeon-backend-server" \
        '{ "index_name": "test_redis", "agents_flag": "True", "messages": "def print_hello_world():", "max_tokens": 256}'

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

function validate_gradio() {
    local URL="http://${ip_address}:5173/health"
    local HTTP_STATUS=$(curl "$URL")
    local SERVICE_NAME="Gradio"

    if [ "$HTTP_STATUS" = '{"status":"ok"}' ]; then
        echo "[ $SERVICE_NAME ] HTTP status is 200. UI server is running successfully..."
    else
        echo "[ $SERVICE_NAME ] UI server has failed..."
    fi
}

function stop_docker() {
    local docker_profile="$1"

    cd $WORKPATH/docker_compose/intel/cpu/xeon/
    docker compose --profile ${docker_profile} down
}

function main() {
    # all docker docker compose profiles for Xeon Platform
    docker_compose_profiles=("codegen-xeon-tgi" "codegen-xeon-vllm")
    docker_llm_container_names=("tgi-server" "vllm-server")

    # get number of profiels and LLM docker container names
    len_profiles=${#docker_compose_profiles[@]}
    len_containers=${#docker_llm_container_names[@]}

    # number of profiels and docker container names must be matched
    if [ ${len_profiles} -ne ${len_containers} ]; then
        echo "Error: number of profiles ${len_profiles} and container names ${len_containers} mismatched"
        exit 1
    fi

    # stop_docker, stop all profiles
    for ((i = 0; i < len_profiles; i++)); do
        stop_docker "${docker_compose_profiles[${i}]}"
    done

    # build docker images
    if [[ "$IMAGE_REPO" == "opea" ]]; then build_docker_images; fi

    # loop all profiles
    for ((i = 0; i < len_profiles; i++)); do
        echo "Process [${i}]: ${docker_compose_profiles[$i]}, ${docker_llm_container_names[${i}]}"
        docker ps -a

        echo "::group::start_services"
        start_services "${docker_compose_profiles[${i}]}" "${docker_llm_container_names[${i}]}"
        echo "::endgroup::"

        echo "::group::validate_microservices"
        validate_microservices "${docker_llm_container_names[${i}]}"
        echo "::endgroup::"

        echo "::group::validate_megaservice"
        validate_megaservice
        echo "::endgroup::"

        echo "::group::validate_gradio"
        validate_gradio
        echo "::endgroup::"

        stop_docker "${docker_compose_profiles[${i}]}"
        sleep 5s
    done

    docker system prune -f
}

main
