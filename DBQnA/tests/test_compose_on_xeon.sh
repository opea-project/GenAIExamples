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
    cd $WORKPATH/docker_image_build
    git clone --single-branch --branch "${opea_branch:-"main"}" https://github.com/opea-project/GenAIComps.git

    echo "Build all the images with --no-cache, check docker_image_build.log for details..."
    docker compose -f build.yaml build --no-cache > ${LOG_PATH}/docker_image_build.log

    docker pull ghcr.io/huggingface/text-generation-inference:2.4.0-intel-cpu
    docker images && sleep 1s
}

function start_services() {
    cd $WORKPATH/docker_compose/intel/cpu/xeon
    export no_proxy="localhost,127.0.0.1,$ip_address"
    source ./set_env.sh

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
    url="postgresql://${POSTGRES_USER}:${POSTGRES_PASSWORD}@${ip_address}:5442/${POSTGRES_DB}"
    result=$(http_proxy="" curl --connect-timeout 5 --max-time 120000 http://${ip_address}:$TEXT2SQL_PORT/v1/text2query\
        -X POST \
        -d '{"query": "Find the total number of Albums.","conn_type": "sql", "conn_url": "'${url}'", "conn_user": "'${POSTGRES_USER}'","conn_password": "'${POSTGRES_PASSWORD}'","conn_dialect": "postgresql" }' \
        -H 'Content-Type: application/json')

    if echo "$result" | jq -e '.result.output' > /dev/null 2>&1; then
    # if [[ $result == *"output"* ]]; then
        echo $result
        echo "Result correct."
    else
        echo "Result wrong. Received was $result"
        docker logs text2sql-service > ${LOG_PATH}/text2sql.log
        docker logs tgi-service > ${LOG_PATH}/tgi.log
        exit 1
    fi

}

function stop_docker() {
    cd $WORKPATH/docker_compose/intel/cpu/xeon
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

    echo "::group::validate_microservice"
    validate_microservice
    echo "::endgroup::"

    echo "::group::stop_docker"
    stop_docker
    echo "::endgroup::"

    docker system prune -f

}

main
