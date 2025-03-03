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

WORKPATH=$(dirname "$PWD")
LOG_PATH="$WORKPATH/tests"
ip_address=$(hostname -I | awk '{print $1}')
tgi_port=8008

function build_docker_images() {
    cd $WORKPATH/docker_image_build
    git clone --single-branch --branch "${opea_branch:-"main"}" https://github.com/opea-project/GenAIComps.git

    echo "Build all the images with --no-cache, check docker_image_build.log for details..."
    docker compose -f build.yaml build --no-cache > ${LOG_PATH}/docker_image_build.log

    docker pull ghcr.io/huggingface/text-generation-inference:2.4.0-intel-cpu
    docker images && sleep 1s
}

function start_service() {
    cd $WORKPATH/docker_compose/intel/cpu/xeon
    export model="mistralai/Mistral-7B-Instruct-v0.3"
    export LLM_MODEL_ID=${model}
    export HUGGINGFACEHUB_API_TOKEN=${HUGGINGFACEHUB_API_TOKEN}
    export POSTGRES_USER=postgres
    export POSTGRES_PASSWORD=testpwd
    export POSTGRES_DB=chinook
    export TEXT2SQL_PORT=9090
    export TGI_LLM_ENDPOINT="http://${ip_address}:${tgi_port}"

    # Start Docker Containers
    docker compose -f compose.yaml up -d > ${LOG_PATH}/start_services_with_compose.log

    # check whether tgi is fully ready.
    n=0
    until [[ "$n" -ge 100 ]] || [[ $ready == true ]]; do
        docker logs tgi-service > ${LOG_PATH}/tgi.log
        n=$((n+1))
        if grep -q Connected ${LOG_PATH}/tgi.log; then
            break
        fi
        sleep 5s
    done
}

function validate_microservice() {
    result=$(http_proxy="" curl --connect-timeout 5 --max-time 120000 http://${ip_address}:$TEXT2SQL_PORT/v1/text2sql\
        -X POST \
        -d '{"input_text": "Find the total number of Albums.","conn_str": {"user": "'${POSTGRES_USER}'","password": "'${POSTGRES_PASSWORD}'","host": "'${ip_address}'", "port": "5442", "database": "'${POSTGRES_DB}'" }}' \
        -H 'Content-Type: application/json')

    if [[ $result == *"output"* ]]; then
        echo $result
        echo "Result correct."
    else
        echo "Result wrong. Received was $result"
        docker logs text2sql-service > ${LOG_PATH}/text2sql.log
        docker logs tgi-service > ${LOG_PATH}/tgi.log
        exit 1
    fi

}

function validate_frontend() {
    echo "[ TEST INFO ]: --------- frontend test started ---------"
    cd $WORKPATH/ui/react
    local conda_env_name="OPEA_e2e"
    export PATH=${HOME}/miniforge3/bin/:$PATH
    if conda info --envs | grep -q "$conda_env_name"; then
        echo "$conda_env_name exist!"
    else
        conda create -n ${conda_env_name} python=3.12 -y
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
    cd $WORKPATH/docker_compose/intel/cpu/xeon
    docker compose stop && docker compose rm -f
}

function main() {

    stop_docker

    build_docker_images
    start_service

    validate_microservice
    validate_frontend

    stop_docker
    echo y | docker system prune

}

main
