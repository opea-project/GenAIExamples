#!/bin/bash
# Copyright (C) 2024 Intel Corporation
# SPDX-License-Identifier: Apache-2.0

set -e
echo "IMAGE_REPO=${IMAGE_REPO}"

WORKPATH=$(dirname "$PWD")
LOG_PATH="$WORKPATH/tests"
ip_address=$(hostname -I | awk '{print $1}')

function build_docker_images() {
    cd $WORKPATH
    docker compose build

    # cd $WORKPATH/docker/ui
    # docker build --no-cache -t opea/audioqna-ui:latest -f docker/Dockerfile .

    docker images
}

function start_services() {
    cd $WORKPATH/docker/xeon
    export HUGGINGFACEHUB_API_TOKEN=${HUGGINGFACEHUB_API_TOKEN}
    export TGI_LLM_ENDPOINT=http://$ip_address:3006
    export LLM_MODEL_ID=Intel/neural-chat-7b-v3-3

    export ASR_ENDPOINT=http://$ip_address:7066
    export TTS_ENDPOINT=http://$ip_address:7055

    export MEGA_SERVICE_HOST_IP=${ip_address}
    export ASR_SERVICE_HOST_IP=${ip_address}
    export TTS_SERVICE_HOST_IP=${ip_address}
    export LLM_SERVICE_HOST_IP=${ip_address}

    export ASR_SERVICE_PORT=3001
    export TTS_SERVICE_PORT=3002
    export LLM_SERVICE_PORT=3007

    docker compose down --remove-orphans
    docker compose up -d
    sleep 3m
}


function validate_megaservice() {
    result=$(http_proxy="" curl http://${ip_address}:3008/v1/audioqna -XPOST -d '{"audio": "UklGRigAAABXQVZFZm10IBIAAAABAAEARKwAAIhYAQACABAAAABkYXRhAgAAAAEA", "max_tokens":64}' -H 'Content-Type: application/json')
    if [[ $result == *"AAA"* ]]; then
        echo "Result correct."
    else
        echo "Result wrong."
        exit 1
    fi

}

#function validate_frontend() {
#    cd $WORKPATH/docker/ui/svelte
#    local conda_env_name="OPEA_e2e"
#    export PATH=${HOME}/miniforge3/bin/:$PATH
##    conda remove -n ${conda_env_name} --all -y
##    conda create -n ${conda_env_name} python=3.12 -y
#    source activate ${conda_env_name}
#
#    sed -i "s/localhost/$ip_address/g" playwright.config.ts
#
##    conda install -c conda-forge nodejs -y
#    npm install && npm ci && npx playwright install --with-deps
#    node -v && npm -v && pip list
#
#    exit_status=0
#    npx playwright test || exit_status=$?
#
#    if [ $exit_status -ne 0 ]; then
#        echo "[TEST INFO]: ---------frontend test failed---------"
#        exit $exit_status
#    else
#        echo "[TEST INFO]: ---------frontend test passed---------"
#    fi
#}

function main() {

    build_docker_images
    # begin_time=$(date +%s)
    start_services

    validate_megaservice
    # validate_frontend

    docker compose down
    echo y | docker system prune

}

main
