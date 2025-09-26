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
    cd $WORKPATH/docker_compose/intel/cpu/xeon/
    export host_ip=${ip_address}
    export LOGFLAG=True
    export no_proxy="$no_proxy,tgi_service_codegen,llm_codegen,tei-embedding-service,tei-reranking-service,chatqna-xeon-backend-server,retriever,tgi-service,redis-vector-db,whisper,llm-docsum-tgi,docsum-xeon-backend-server,mongo,codegen"

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

    source activate ${conda_env_name}
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
    cd $WORKPATH/docker_compose/intel/cpu/xeon/
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

    echo "::group::validate_frontend"
    validate_frontend
    echo "::endgroup::"

    echo "::group::stop_docker"
    stop_docker
    echo "::endgroup::"

    docker system prune -f

}

main
