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
    until [[ "$n" -ge 100 ]]; do
        docker logs ${llm_container_name} > ${LOG_PATH}/llm_service_start.log 2>&1
        if grep -E "Connected|complete" ${LOG_PATH}/llm_service_start.log; then
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
