#!/bin/bash
# Copyright (C) 2024 Intel Corporation
# SPDX-License-Identifier: Apache-2.0

set -e
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

    echo "Build all the images with --no-cache, check docker_image_build.log for details..."
    service_list="audioqna audioqna-ui whisper speecht5"
    docker compose -f build.yaml build ${service_list} --no-cache > ${LOG_PATH}/docker_image_build.log

    docker pull ghcr.io/huggingface/tgi-gaudi:2.0.6
    docker images && sleep 1s
}

function start_services() {
    cd $WORKPATH/docker_compose/intel/cpu/xeon/
    export HUGGINGFACEHUB_API_TOKEN=${HUGGINGFACEHUB_API_TOKEN}
    export LLM_MODEL_ID=Intel/neural-chat-7b-v3-3

    export MEGA_SERVICE_HOST_IP=${ip_address}
    export WHISPER_SERVER_HOST_IP=${ip_address}
    export SPEECHT5_SERVER_HOST_IP=${ip_address}
    export LLM_SERVER_HOST_IP=${ip_address}

    export WHISPER_SERVER_PORT=7066
    export SPEECHT5_SERVER_PORT=7055
    export LLM_SERVER_PORT=3006

    export BACKEND_SERVICE_ENDPOINT=http://${ip_address}:3008/v1/audioqna
    export host_ip=${ip_address}

    # sed -i "s/backend_address/$ip_address/g" $WORKPATH/ui/svelte/.env

    # Start Docker Containers
    docker compose up -d > ${LOG_PATH}/start_services_with_compose.log
    n=0
    until [[ "$n" -ge 200 ]]; do
       docker logs tgi-service > $LOG_PATH/tgi_service_start.log
       if grep -q Connected $LOG_PATH/tgi_service_start.log; then
           break
       fi
       sleep 5s
       n=$((n+1))
    done
}


function validate_megaservice() {
    response=$(http_proxy="" curl http://${ip_address}:3008/v1/audioqna -XPOST -d '{"audio": "UklGRigAAABXQVZFZm10IBIAAAABAAEARKwAAIhYAQACABAAAABkYXRhAgAAAAEA", "max_tokens":64}' -H 'Content-Type: application/json')
    # always print the log
    docker logs whisper-service > $LOG_PATH/whisper-service.log
    docker logs speecht5-service > $LOG_PATH/tts-service.log
    docker logs tgi-service > $LOG_PATH/tgi-service.log
    docker logs audioqna-xeon-backend-server > $LOG_PATH/audioqna-xeon-backend-server.log
    echo "$response" | sed 's/^"//;s/"$//' | base64 -d > speech.mp3

    if [[ $(file speech.mp3) == *"RIFF"* ]]; then
        echo "Result correct."
    else
        echo "Result wrong."
        exit 1
    fi

}

#function validate_frontend() {
#    cd $WORKPATH/ui/svelte
#    local conda_env_name="OPEA_e2e"
#    export PATH=${HOME}/miniforge3/bin/:$PATH
##    conda remove -n ${conda_env_name} --all -y
##    conda create -n ${conda_env_name} python=3.12 -y
#    source activate ${conda_env_name}
#
#    sed -i "s/localhost/$ip_address/g" playwright.config.ts
#
##    conda install -c conda-forge nodejs=22.6.0 -y
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

function stop_docker() {
    cd $WORKPATH/docker_compose/intel/cpu/xeon/
    docker compose stop && docker compose rm -f
}

function main() {

    stop_docker
    if [[ "$IMAGE_REPO" == "opea" ]]; then build_docker_images; fi
    start_services

    validate_megaservice
    # validate_frontend

    stop_docker
    echo y | docker system prune

}

main
