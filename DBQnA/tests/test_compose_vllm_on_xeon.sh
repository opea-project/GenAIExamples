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
    cd $WORKPATH
    git clone https://github.com/vllm-project/vllm.git
    cd ./vllm/
    VLLM_VER="$(git describe --tags "$(git rev-list --tags --max-count=1)" )"
    echo "Check out vLLM tag ${VLLM_VER}"
    git checkout ${VLLM_VER} &> /dev/null
    docker build --no-cache -f Dockerfile.cpu -t ${REGISTRY:-opea}/vllm:${TAG:-latest} --shm-size=128g .
    if [ $? -ne 0 ]; then
        echo "opea/vllm built fail"
        exit 1
    else
        echo "opea/vllm built successful"
    fi

    cd $WORKPATH/docker_image_build
    git clone --single-branch --branch "${opea_branch:-"main"}" https://github.com/opea-project/GenAIComps.git

    echo "Build all the images with --no-cache, check docker_image_build.log for details..."
    service_list="vllm-service text2sql text2sql-react-ui"
    docker compose -f build.yaml build ${service_list} --no-cache > ${LOG_PATH}/docker_image_build.log

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
	  export LLM_ENDPOINT_PORT=8008
    export LLM_ENDPOINT="http://${ip_address}:${LLM_ENDPOINT_PORT}"

    # Start Docker Containers
    docker compose -f compose_vllm.yaml up -d > ${LOG_PATH}/start_services_with_compose.log

    # check whether vLLM is fully ready.
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
