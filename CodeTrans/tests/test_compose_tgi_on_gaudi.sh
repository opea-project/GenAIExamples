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
    service_list="codetrans codetrans-ui llm-textgen nginx"
    docker compose -f build.yaml build ${service_list} --no-cache > ${LOG_PATH}/docker_image_build.log

    docker pull ghcr.io/huggingface/tgi-gaudi:2.0.6
    docker images && sleep 1s
}

function start_services() {
    cd $WORKPATH/docker_compose
    export HUGGINGFACEHUB_API_TOKEN=${HUGGINGFACEHUB_API_TOKEN}

    export NGINX_PORT=80
    export host_ip=${ip_address}
    source set_env.sh
    cd intel/hpu/gaudi/

    sed -i "s/backend_address/$ip_address/g" $WORKPATH/ui/svelte/.env

    # Start Docker Containers
    docker compose -f compose_tgi.yaml up -d > ${LOG_PATH}/start_services_with_compose.log

    n=0
    until [[ "$n" -ge 100 ]]; do
        docker logs codetrans-gaudi-tgi-service > ${LOG_PATH}/tgi_service_start.log
        if grep -q Connected ${LOG_PATH}/tgi_service_start.log; then
            break
        fi
        sleep 5s
        n=$((n+1))
    done

    sleep 1m
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
    sleep 5s
}

function validate_microservices() {
    # tgi for embedding service
    validate_services \
        "${ip_address}:8008/generate" \
        "generated_text" \
        "tgi" \
        "codetrans-gaudi-tgi-service" \
        '{"inputs":"What is Deep Learning?","parameters":{"max_new_tokens":17, "do_sample": true}}'

    # llm microservice
    validate_services \
        "${ip_address}:9000/v1/chat/completions" \
        "data: " \
        "llm" \
        "codetrans-gaudi-llm-server" \
        '{"query":"    ### System: Please translate the following Golang codes into  Python codes.    ### Original codes:    '\'''\'''\''Golang    \npackage main\n\nimport \"fmt\"\nfunc main() {\n    fmt.Println(\"Hello, World!\");\n    '\'''\'''\''    ### Translated codes:"}'

}

function validate_megaservice() {
    # Curl the Mega Service
    validate_services \
        "${ip_address}:${BACKEND_SERVICE_PORT}/v1/codetrans" \
        "print" \
        "mega-codetrans" \
        "codetrans-gaudi-backend-server" \
        '{"language_from": "Golang","language_to": "Python","source_code": "package main\n\nimport \"fmt\"\nfunc main() {\n    fmt.Println(\"Hello, World!\");\n}"}'

    # test the megeservice via nginx
    validate_services \
        "${ip_address}:${NGINX_PORT}/v1/codetrans" \
        "print" \
        "mega-codetrans-nginx" \
        "codetrans-gaudi-nginx-server" \
        '{"language_from": "Golang","language_to": "Python","source_code": "package main\n\nimport \"fmt\"\nfunc main() {\n    fmt.Println(\"Hello, World!\");\n}"}'

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
    cd $WORKPATH/docker_compose/intel/hpu/gaudi/
    docker compose -f compose_tgi.yaml stop && docker compose rm -f
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

    echo "::group::validate_frontend"
    validate_frontend
    echo "::endgroup::"

    echo "::group::stop_docker"
    stop_docker
    echo "::endgroup::"

    docker system prune -f

}

main
