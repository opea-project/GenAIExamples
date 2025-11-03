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

    echo "Build all the images with --no-cache, check docker_image_build.log for details..."
    service_list="codegen codegen-ui llm-textgen dataprep retriever embedding"

    docker compose -f build.yaml build ${service_list} --no-cache > ${LOG_PATH}/docker_image_build.log

    docker pull ghcr.io/huggingface/text-generation-inference:2.4.0-intel-cpu
    docker images && sleep 1s
}

function start_services() {
    local compose_file="$1"
    local llm_container_name="$2"
    export no_proxy="localhost,127.0.0.1,$ip_address"
    cd $WORKPATH/docker_compose/intel/cpu/xeon/

    # Start Docker Containers
    docker compose -f ${compose_file} up -d > ${LOG_PATH}/start_services_with_compose.log

    n=0
    until [[ "$n" -ge 200 ]]; do
        docker logs ${llm_container_name} > ${LOG_PATH}/llm_service_start.log 2>&1
        if grep -E "Connected|complete|healthy" ${LOG_PATH}/llm_service_start.log; then
            break
        fi
        sleep 5s
        n=$((n+1))
    done
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

    export no_proxy="localhost,127.0.0.1,$ip_address"

    # Wait for backend service to be ready
    echo "Waiting for backend service to be ready..."
    n=0
    until [[ "$n" -ge 60 ]]; do
        HTTP_STATUS=$(curl -s -o /dev/null -w "%{http_code}" "http://${ip_address}:7778/v1/chatcompletions")
        if [ "$HTTP_STATUS" = "200" ] || [ "$HTTP_STATUS" = "500" ]; then  # 500 might be expected if model is loading
            echo "Backend service is ready"
            break
        fi
        echo "Waiting for backend service... (attempt $n/60), HTTP status: $HTTP_STATUS"
        sleep 5s
        n=$((n+1))
    done

    # Wait for UI service to be ready
    echo "Waiting for UI service to be ready..."
    n=0
    until [[ "$n" -ge 60 ]]; do
        HTTP_STATUS=$(curl -s -o /dev/null -w "%{http_code}" "http://${ip_address}:5173/health")
        if [ "$HTTP_STATUS" = "200" ]; then
            echo "UI service is ready"
            break
        fi
        echo "Waiting for UI service... (attempt $n/60), HTTP status: $HTTP_STATUS"
        sleep 5s
        n=$((n+1))
    done

    # Run tests with better logging
    echo "Starting Playwright tests..."
    exit_status=0
    npx playwright test --reporter=list > ${LOG_PATH}/frontend_test.log 2>&1 || exit_status=$?

    if [ $exit_status -ne 0 ]; then
        echo "[TEST INFO]: ---------frontend test failed---------"
        echo "Test logs:"
        cat ${LOG_PATH}/frontend_test.log
        exit $exit_status
    else
        echo "[TEST INFO]: ---------frontend test passed---------"
    fi
}

function validate_gradio() {
    local URL="http://${ip_address}:5173/health"
    local HTTP_STATUS=$(curl -s "$URL")
    local SERVICE_NAME="CodeGen UI"

    if [ "$HTTP_STATUS" = '{"status":"ok"}' ] || [ "$HTTP_STATUS" = "200" ]; then
        echo "[ $SERVICE_NAME ] HTTP status is 200. UI server is running successfully..."
    else
        echo "[ $SERVICE_NAME ] UI server health check failed. Response: $HTTP_STATUS"
    fi
}

function stop_docker() {
    local compose_file="$1"

    cd $WORKPATH/docker_compose/intel/cpu/xeon/
    docker compose -f ${compose_file} down
}

function main() {
    # all docker docker compose files for Xeon Platform
    docker_compose_files=("compose_tgi.yaml" "compose.yaml")
    docker_llm_container_names=("tgi-server" "vllm-server")

    # get number of compose files and LLM docker container names
    len_compose_files=${#docker_compose_files[@]}
    len_containers=${#docker_llm_container_names[@]}

    # number of compose files and docker container names must be matched
    if [ ${len_compose_files} -ne ${len_containers} ]; then
        echo "Error: number of docker compose files ${len_compose_files} and container names ${len_containers} mismatched"
        exit 1
    fi

    # stop_docker, stop all compose files
    for ((i = 0; i < len_compose_files; i++)); do
        stop_docker "${docker_compose_files[${i}]}"
    done

    # build docker images
    if [[ "$IMAGE_REPO" == "opea" ]]; then build_docker_images; fi

    # loop all compose files
    for ((i = 0; i < len_compose_files; i++)); do
        echo "Process [${i}]: ${docker_compose_files[$i]}, ${docker_llm_container_names[${i}]}"
        docker ps -a

        echo "::group::start_services"
        start_services "${docker_compose_files[${i}]}" "${docker_llm_container_names[${i}]}"
        echo "::endgroup::"

        echo "::group::validate_ui"
        validate_frontend
        if [ $? -ne 0 ]; then
            echo "Frontend validation failed, checking logs..."
            if [ -f "${LOG_PATH}/frontend_test.log" ]; then
                echo "Frontend test logs:"
                cat "${LOG_PATH}/frontend_test.log"
            fi
        fi
        echo "::endgroup::"

        echo "::group::validate_gradio"
        validate_gradio
        echo "::endgroup::"

        stop_docker "${docker_compose_files[${i}]}"
        sleep 5s
    done

    docker system prune -f
}

main
