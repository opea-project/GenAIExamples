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

export host_ip=${ip_address}
source $WORKPATH/docker_compose/amd/gpu/rocm/set_env.sh

export MODEL_CACHE=${model_cache:-"/var/lib/GenAI/data"}

function build_docker_images() {
    cd "$WORKPATH"/docker_image_build
    git clone https://github.com/opea-project/GenAIComps.git && cd GenAIComps && git checkout "${opea_branch:-"main"}" && cd ../

    echo "Build all the images with --no-cache, check docker_image_build.log for details..."
    service_list="text2sql text2sql-react-ui"

    docker compose -f build.yaml build ${service_list} --no-cache > "${LOG_PATH}"/docker_image_build.log
    docker pull ghcr.io/huggingface/text-generation-inference:2.4.1-rocm
    docker images && sleep 1s
}

function start_services() {
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
        docker logs text2sql > ${LOG_PATH}/text2sql.log
        docker logs dbqna-tgi-service > ${LOG_PATH}/tgi.log
        exit 1
    fi

}

function stop_docker() {
    cd $WORKPATH/docker_compose/amd/gpu/rocm/
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
