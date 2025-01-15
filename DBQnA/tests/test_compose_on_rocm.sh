#!/bin/bash
# Copyright (C) 2024 Intel Corporation
# SPDX-License-Identifier: Apache-2.0

set -xe

WORKPATH=$(dirname "$PWD")
LOG_PATH="$WORKPATH/tests"
ip_address=$(hostname -I | awk '{print $1}')
tgi_port=8008
tgi_volume=$WORKPATH/data

export host_ip=${ip_address}
export DBQNA_HUGGINGFACEHUB_API_TOKEN=${HUGGINGFACEHUB_API_TOKEN}
export DBQNA_TGI_SERVICE_PORT=8008
export DBQNA_TGI_LLM_ENDPOINT="http://${host_ip}:${DBQNA_TGI_SERVICE_PORT}"
export DBQNA_LLM_MODEL_ID="mistralai/Mistral-7B-Instruct-v0.3"
export MODEL_ID=${DBQNA_LLM_MODEL_ID}
export POSTGRES_USER="postgres"
export POSTGRES_PASSWORD="testpwd"
export POSTGRES_DB="chinook"
export DBQNA_TEXT_TO_SQL_PORT=9090
export DBQNA_UI_PORT=5174
export build_texttosql_url="${ip_address}:${DBQNA_TEXT_TO_SQL_PORT}/v1"

function build_docker_images() {
    cd "$WORKPATH"/docker_image_build
    git clone https://github.com/opea-project/GenAIComps.git && cd GenAIComps && git checkout "${opea_branch:-"main"}" && cd ../

    echo "Build all the images with --no-cache, check docker_image_build.log for details..."
    service_list="text2sql text2sql-react-ui"

    docker compose -f build.yaml build ${service_list} --no-cache > "${LOG_PATH}"/docker_image_build.log
    docker pull ghcr.io/huggingface/text-generation-inference:2.3.1-rocm
    docker images && sleep 1s
}

function start_service() {
    cd "$WORKPATH"/docker_compose/amd/gpu/rocm
    # Start Docker Containers
    docker compose up -d > "${LOG_PATH}"/start_services_with_compose.log
    n=0
    until [[ "$n" -ge 100 ]]; do
        docker logs dbqna-tgi-service > "${LOG_PATH}"/tgi_service_start.log
        if grep -q Connected "${LOG_PATH}"/tgi_service_start.log; then
            break
        fi
        sleep 5s
        n=$((n+1))
    done
}

function validate_microservice() {
    result=$(http_proxy="" curl --connect-timeout 5 --max-time 120000 http://${ip_address}:${DBQNA_TEXT_TO_SQL_PORT}/v1/text2sql \
        -X POST \
        -d '{"input_text": "Find the total number of Albums.","conn_str": {"user": "'${POSTGRES_USER}'","password": "'${POSTGRES_PASSWORD}'","host": "'${ip_address}'", "port": "5442", "database": "'${POSTGRES_DB}'" }}' \
        -H 'Content-Type: application/json')

    if [[ $result == *"output"* ]]; then
        echo $result
        echo "Result correct."
    else
        echo "Result wrong. Received was $result"
        docker logs text2sql > ${LOG_PATH}/text2sql.log
        docker logs dbqna-tgi-service > ${LOG_PATH}/tgi.log
        exit 1
    fi

}

function validate_frontend() {
    echo "[ TEST INFO ]: --------- frontend test started ---------"
    cd $WORKPATH/ui/react
    local conda_env_name="OPEA_e2e"
    export PATH=${HOME}/miniconda3/bin/:$PATH
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
    cd $WORKPATH/docker_compose/amd/gpu/rocm/
    docker compose stop && docker compose rm -f
}

function main() {

    stop_docker

    build_docker_images
    start_service
    sleep 10s
    validate_microservice
    validate_frontend

    stop_docker
    echo y | docker system prune

}

main
