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
export NGINX_PORT=81

WORKPATH=$(dirname "$PWD")
LOG_PATH="$WORKPATH/tests"
ip_address=$(hostname -I | awk '{print $1}')

function build_docker_images() {
    ## Revert this ------------------>
    cd $WORKPATH/docker_image_build
    git clone --depth 1 --branch vllm_vision https://github.com/Spycsh/GenAIComps.git
    docker compose -f build.yaml build --no-cache > ${LOG_PATH}/docker_image_build.log

    # opea_branch=${opea_branch:-"main"}
    # # If the opea_branch isn't main, replace the git clone branch in Dockerfile.
    # if [[ "${opea_branch}" != "main" ]]; then
    #     cd $WORKPATH
    #     OLD_STRING="RUN git clone --depth 1 https://github.com/opea-project/GenAIComps.git"
    #     NEW_STRING="RUN git clone --depth 1 --branch ${opea_branch} https://github.com/opea-project/GenAIComps.git"
    #     find . -type f -name "Dockerfile*" | while read -r file; do
    #         echo "Processing file: $file"
    #         sed -i "s|$OLD_STRING|$NEW_STRING|g" "$file"
    #     done
    # fi

    # cd $WORKPATH/docker_image_build
    # git clone --depth 1 --branch ${opea_branch} https://github.com/opea-project/GenAIComps.git

    # echo "Build all the images with --no-cache, check docker_image_build.log for details..."
    # docker compose -f build.yaml build --no-cache > ${LOG_PATH}/docker_image_build.log

    git clone https://github.com/HabanaAI/vllm-fork.git
    cd ./vllm-fork/
    git checkout habana_main
    docker build -f Dockerfile.hpu -t opea/vllm-gaudi:latest --shm-size=128g . --build-arg https_proxy=$https_proxy --build-arg http_proxy=$http_proxy
    cd ..
    rm -rf vllm-fork

    docker images && sleep 1s
}

function start_services() {
    cd $WORKPATH/docker_compose/intel/hpu/gaudi

    source ./set_env.sh


    sed -i "s/backend_address/$ip_address/g" $WORKPATH/ui/svelte/.env

    # Start Docker Containers
    docker compose up -d > ${LOG_PATH}/start_services_with_compose.log

    n=0
    until [[ "$n" -ge 100 ]]; do
        docker logs lvm-gaudi-server > ${LOG_PATH}/lvm_vllm_service_start.log
        if grep -q Starting ${LOG_PATH}/lvm_vllm_service_start.log; then
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
        "yellow" \
        "lvm" \
        "lvm-gaudi-server" \
        '{"image": "iVBORw0KGgoAAAANSUhEUgAAAAoAAAAKCAYAAACNMs+9AAAAFUlEQVR42mP8/5+hnoEIwDiqkL4KAcT9GO0U4BxoAAAAAElFTkSuQmCC", "prompt":"What is this?"}'
}

function validate_megaservice() {
    # Curl the Mega Service
    validate_services \
    "${ip_address}:8899/v1/visualqna" \
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
    "${ip_address}:${NGINX_PORT}/v1/visualqna" \
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

function stop_docker() {
    cd $WORKPATH/docker_compose/intel/hpu/gaudi
    docker compose stop && docker compose rm -f
}

function main() {

    stop_docker

    if [[ "$IMAGE_REPO" == "opea" ]]; then build_docker_images; fi
    start_services

    validate_microservices
    validate_megaservice
    # validate_frontend

    stop_docker
    echo y | docker system prune

}

main
