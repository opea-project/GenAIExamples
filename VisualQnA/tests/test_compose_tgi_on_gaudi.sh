#!/bin/bash
# Copyright (C) 2024 Intel Corporation
# SPDX-License-Identifier: Apache-2.0

set -x
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
    service_list="visualqna visualqna-ui lvm nginx"
    docker compose -f build.yaml build ${service_list} --no-cache > ${LOG_PATH}/docker_image_build.log

    docker images && sleep 1s
}

function start_services() {
    cd $WORKPATH/docker_compose/intel/hpu/gaudi

    export HF_TOKEN=${HF_TOKEN}
    export NGINX_PORT=80
    export host_ip=${ip_address}
    export no_proxy="localhost,127.0.0.1,$ip_address"
    source ./set_env.sh
    export LVM_MODEL_ID="llava-hf/llava-v1.6-mistral-7b-hf"

    sed -i "s/backend_address/$ip_address/g" $WORKPATH/ui/svelte/.env

    # Start Docker Containers
    docker compose -f compose_tgi.yaml -f compose.monitoring.yaml up -d > ${LOG_PATH}/start_services_with_compose.log

    n=0
    until [[ "$n" -ge 100 ]]; do
        docker logs tgi-llava-gaudi-server > ${LOG_PATH}/lvm_tgi_service_start.log
        if grep -q Connected ${LOG_PATH}/lvm_tgi_service_start.log; then
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
    sleep 1s
}

function validate_microservices() {
    sleep 15s
    # Check if the microservices are running correctly.

    # lvm microservice
    validate_services \
        "${ip_address}:9399/v1/lvm" \
        "The image" \
        "lvm" \
        "lvm-gaudi-server" \
        '{"image": "iVBORw0KGgoAAAANSUhEUgAAAAoAAAAKCAYAAACNMs+9AAAAFUlEQVR42mP8/5+hnoEIwDiqkL4KAcT9GO0U4BxoAAAAAElFTkSuQmCC", "prompt":"What is this?"}'
}

function validate_megaservice() {
    sleep 15s
    # Curl the Mega Service
    validate_services \
    "${ip_address}:8888/v1/visualqna" \
    "The image" \
    "visualqna-gaudi-backend-server" \
    "visualqna-gaudi-backend-server" \
    '{
        "messages": [
        {
            "role": "user",
            "content": [
            {
                "type": "text",
                "text": "What'\''s in this image?"
            },
            {
                "type": "image_url",
                "image_url": {
                "url": "https://www.ilankelman.org/stopsigns/australia.jpg"
                }
            }
            ]
        }
        ],
        "max_tokens": 300
    }'

    # test the megeservice via nginx
    validate_services \
    "${ip_address}:80/v1/visualqna" \
    "The image" \
    "visualqna-gaudi-nginx-server" \
    "visualqna-gaudi-nginx-server" \
    '{
        "messages": [
        {
            "role": "user",
            "content": [
            {
                "type": "text",
                "text": "What'\''s in this image?"
            },
            {
                "type": "image_url",
                "image_url": {
                "url": "https://www.ilankelman.org/stopsigns/australia.jpg"
                }
            }
            ]
        }
        ],
        "max_tokens": 300
    }'
}

function stop_docker() {
    cd $WORKPATH/docker_compose/intel/hpu/gaudi
    docker compose -f compose_tgi.yaml -f compose.monitoring.yaml down
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

    echo "::group::validate_megaservice"
    validate_megaservice
    echo "::endgroup::"

    echo "::group::stop_docker"
    stop_docker
    echo "::endgroup::"

    docker system prune -f

}

main
