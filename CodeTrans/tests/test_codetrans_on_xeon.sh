#!/bin/bash
# Copyright (C) 2024 Intel Corporation
# SPDX-License-Identifier: Apache-2.0

set -xe

WORKPATH=$(dirname "$PWD")
LOG_PATH="$WORKPATH/tests"
ip_address=$(hostname -I | awk '{print $1}')

function build_docker_images() {
    cd $WORKPATH
    git clone https://github.com/opea-project/GenAIComps.git
    cd GenAIComps

    docker build -t opea/llm-tgi:latest -f comps/llms/text-generation/tgi/Dockerfile .

    cd $WORKPATH/docker
    docker build --no-cache -t opea/codetrans:latest -f Dockerfile .

    cd $WORKPATH/docker/ui
    docker build --no-cache -t opea/codetrans-ui:latest -f docker/Dockerfile .

    docker images
}

function start_services() {
    cd $WORKPATH/docker/xeon
    export http_proxy=${http_proxy}
    export https_proxy=${http_proxy}
    export LLM_MODEL_ID="HuggingFaceH4/mistral-7b-grok"
    export TGI_LLM_ENDPOINT="http://${ip_address}:8008"
    export HUGGINGFACEHUB_API_TOKEN=${HUGGINGFACEHUB_API_TOKEN}
    export MEGA_SERVICE_HOST_IP=${ip_address}
    export LLM_SERVICE_HOST_IP=${ip_address}
    export BACKEND_SERVICE_ENDPOINT="http://${ip_address}:7777/v1/codetrans"

    sed -i "s/backend_address/$ip_address/g" $WORKPATH/docker/ui/svelte/.env

    if [[ "$IMAGE_REPO" != "" ]]; then
        # Replace the container name with a test-specific name
        echo "using image repository $IMAGE_REPO and image tag $IMAGE_TAG"
        sed -i "s#image: opea/codetrans:latest#image: opea/codetrans:${IMAGE_TAG}#g" compose.yaml
        sed -i "s#image: opea/codetrans-ui:latest#image: opea/codetrans-ui:${IMAGE_TAG}#g" compose.yaml
        sed -i "s#image: opea/*#image: ${IMAGE_REPO}opea/#g" compose.yaml
        echo "cat compose.yaml"
        cat compose.yaml
    fi

    # Start Docker Containers
    docker compose up -d

    n=0
    until [[ "$n" -ge 400 ]]; do
        docker logs codetrans-tgi-service > ${LOG_PATH}/tgi_service_start.log
        if grep -q Connected ${LOG_PATH}/tgi_service_start.log; then
            break
        fi
        sleep 1s
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
    sleep 5s
}

function validate_microservices() {
    # tgi for embedding service
    validate_services \
        "${ip_address}:8008/generate" \
        "generated_text" \
        "tgi" \
        "codetrans-tgi-service" \
        '{"inputs":"What is Deep Learning?","parameters":{"max_new_tokens":17, "do_sample": true}}'

    # llm microservice
    validate_services \
        "${ip_address}:9000/v1/chat/completions" \
        "data: " \
        "llm" \
        "llm-tgi-server" \
        '{"query":"    ### System: Please translate the following Golang codes into  Python codes.    ### Original codes:    '\'''\'''\''Golang    \npackage main\n\nimport \"fmt\"\nfunc main() {\n    fmt.Println(\"Hello, World!\");\n    '\'''\'''\''    ### Translated codes:"}'

}

function validate_megaservice() {
    # Curl the Mega Service
    validate_services \
        "${ip_address}:7777/v1/codetrans" \
        "print" \
        "mega-codetrans" \
        "codetrans-xeon-backend-server" \
        '{"language_from": "Golang","language_to": "Python","source_code": "package main\n\nimport \"fmt\"\nfunc main() {\n    fmt.Println(\"Hello, World!\");\n}"}'

}

function validate_frontend() {
    cd $WORKPATH/docker/ui/svelte
    local conda_env_name="OPEA_e2e"
    export PATH=${HOME}/miniforge3/bin/:$PATH
#    conda remove -n ${conda_env_name} --all -y
#    conda create -n ${conda_env_name} python=3.12 -y
    source activate ${conda_env_name}

    sed -i "s/localhost/$ip_address/g" playwright.config.ts

#    conda install -c conda-forge nodejs -y
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
    cd $WORKPATH/docker/xeon
    docker compose stop && docker compose rm -f
}

function main() {

    stop_docker

    if [[ "$IMAGE_REPO" == "" ]]; then build_docker_images; fi
    start_services

    validate_microservices
    validate_megaservice
    validate_frontend

    stop_docker
    echo y | docker system prune

}

main
