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
    # If the opea_branch isn't main, replace the git clone branch in Dockerfile.
    if [[ "${opea_branch}" != "main" ]]; then
        cd $WORKPATH
        OLD_STRING="RUN git clone --depth 1 https://github.com/opea-project/GenAIComps.git"
        NEW_STRING="RUN git clone --depth 1 --branch ${opea_branch} https://github.com/opea-project/GenAIComps.git"
        find . -type f -name "Dockerfile*" | while read -r file; do
            echo "Processing file: $file"
            sed -i "s|$OLD_STRING|$NEW_STRING|g" "$file"
        done
    fi

    cd $WORKPATH/docker_image_build
    git clone --depth 1 --branch ${opea_branch} https://github.com/opea-project/GenAIComps.git
    git clone https://github.com/vllm-project/vllm.git && cd vllm
    VLLM_VER="$(git describe --tags "$(git rev-list --tags --max-count=1)" )"
    echo "Check out vLLM tag ${VLLM_VER}"
    git checkout ${VLLM_VER} &> /dev/null
    cd ../

    echo "Build all the images with --no-cache, check docker_image_build.log for details..."
    service_list="translation translation-ui llm-textgen vllm nginx"
    docker compose -f build.yaml build ${service_list} --no-cache > ${LOG_PATH}/docker_image_build.log

    docker pull ghcr.io/huggingface/text-generation-inference:2.4.0-intel-cpu
    docker images && sleep 1s
}

function start_services() {
    cd $WORKPATH/docker_compose/intel/cpu/xeon/

    export http_proxy=${http_proxy}
    export https_proxy=${https_proxy}
    export LLM_MODEL_ID="mistralai/Mistral-7B-Instruct-v0.3"
    export LLM_ENDPOINT="http://${ip_address}:8008"
    export LLM_COMPONENT_NAME="OpeaTextGenService"
    export HUGGINGFACEHUB_API_TOKEN=${HUGGINGFACEHUB_API_TOKEN}
    export MEGA_SERVICE_HOST_IP=${ip_address}
    export LLM_SERVICE_HOST_IP=${ip_address}
    export FRONTEND_SERVICE_IP=${ip_address}
    export FRONTEND_SERVICE_PORT=5173
    export BACKEND_SERVICE_NAME=translation
    export BACKEND_SERVICE_IP=${ip_address}
    export BACKEND_SERVICE_PORT=8888
    export BACKEND_SERVICE_ENDPOINT="http://${ip_address}:${BACKEND_SERVICE_PORT}/v1/translation"
    export NGINX_PORT=80
    export host_ip=${ip_address}

    sed -i "s/backend_address/$ip_address/g" $WORKPATH/ui/svelte/.env

    # Start Docker Containers
    docker compose -f compose.yaml up -d > ${LOG_PATH}/start_services_with_compose.log

    sleep 5s
}

function validate_services() {
    local URL="$1"
    local EXPECTED_RESULT="$2"
    local SERVICE_NAME="$3"
    local DOCKER_NAME="$4"
    local INPUT_DATA="$5"

    HTTP_RESPONSE=$(curl --silent --write-out "HTTPSTATUS:%{http_code}" -X POST -d "$INPUT_DATA" -H 'Content-Type: application/json' "$URL")
    HTTP_STATUS=$(echo $HTTP_RESPONSE | tr -d '\n' | sed -e 's/.*HTTPSTATUS://')
    RESPONSE_BODY=$(echo $HTTP_RESPONSE | sed -e 's/HTTPSTATUS\:.*//g')

    docker logs ${DOCKER_NAME} >> ${LOG_PATH}/${SERVICE_NAME}.log

    # check response status
    if [ "$HTTP_STATUS" -ne "200" ]; then
        echo "[ $SERVICE_NAME ] HTTP status is not 200. Received status was $HTTP_STATUS"
        exit 1
    else
        echo "[ $SERVICE_NAME ] HTTP status is 200. Checking content..."
    fi
    # check response body
    if [[ "$RESPONSE_BODY" != *"$EXPECTED_RESULT"* ]]; then
        echo "[ $SERVICE_NAME ] Content does not match the expected result: $RESPONSE_BODY"
        exit 1
    else
        echo "[ $SERVICE_NAME ] Content is as expected."
    fi

    sleep 5s
}

function validate_microservices() {
    # llm microservice
    validate_services \
        "${ip_address}:9000/v1/chat/completions" \
        "data: " \
        "llm" \
        "translation-xeon-llm-server" \
        '{"query":"    ### System: Please translate the following Golang codes into  Python codes.    ### Original codes:    '\'''\'''\''Golang    \npackage main\n\nimport \"fmt\"\nfunc main() {\n    fmt.Println(\"Hello, World!\");\n    '\'''\'''\''    ### Translated codes:"}'
}

function validate_megaservice() {
    # test the megaservice for code translation
    validate_services \
        "${ip_address}:${BACKEND_SERVICE_PORT}/v1/translation" \
        "print" \
        "mega-translation" \
        "translation-xeon-backend-server" \
        '{"language_from": "Golang","language_to": "Python","source_data": "package main\n\nimport \"fmt\"\nfunc main() {\n    fmt.Println(\"Hello, World!\");\n}","translate_type":"code"}'

    # test the megaservice for text translation
    validate_services \
        "${ip_address}:${BACKEND_SERVICE_PORT}/v1/translation" \
        "translation" \
        "mega-translation" \
        "translation-xeon-backend-server" \
        '{"language_from": "Chinese","language_to": "English","source_data": "我爱机器翻译。","translate_type":"text"}'

    # test the megeservice via nginx
    validate_services \
        "${ip_address}:${NGINX_PORT}/v1/translation" \
        "print" \
        "mega-translation-nginx" \
        "translation-xeon-nginx-server" \
        '{"language_from": "Golang","language_to": "Python","source_data": "package main\n\nimport \"fmt\"\nfunc main() {\n    fmt.Println(\"Hello, World!\");\n}","translate_type":"code"}'
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
    cd $WORKPATH/docker_compose/intel/cpu/xeon/
    docker compose -f compose.yaml stop && docker compose rm -f
}

function main() {

    stop_docker

    if [[ "$IMAGE_REPO" == "opea" ]]; then build_docker_images; fi
    start_services

    validate_microservices
    validate_megaservice
    validate_frontend

    stop_docker
    echo y | docker system prune

}

main
