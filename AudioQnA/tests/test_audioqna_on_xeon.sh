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
    git clone https://github.com/opea-project/GenAIComps.git
    cd GenAIComps

    docker build -t opea/whisper:latest -f comps/asr/whisper/Dockerfile .
    docker build -t opea/asr:latest -f comps/asr/Dockerfile .
    docker build -t opea/llm-tgi:latest -f comps/llms/text-generation/tgi/Dockerfile .
    docker build -t opea/speecht5:latest -f comps/tts/speecht5/Dockerfile .
    docker build -t opea/tts:latest -f comps/tts/Dockerfile .

    docker pull ghcr.io/huggingface/tgi-gaudi:2.0.1

    cd $WORKPATH/docker
    docker build --no-cache -t opea/audioqna:latest -f Dockerfile .

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

    # sed -i "s/backend_address/$ip_address/g" $WORKPATH/docker/ui/svelte/.env

    if [[ "$IMAGE_REPO" != "" ]]; then
        # Replace the container name with a test-specific name
        echo "using image repository $IMAGE_REPO and image tag $IMAGE_TAG"
        sed -i "s#image: opea/audioqna:latest#image: opea/audioqna:${IMAGE_TAG}#g" compose.yaml
        sed -i "s#image: opea/audioqna-ui:latest#image: opea/audioqna-ui:${IMAGE_TAG}#g" compose.yaml
        sed -i "s#image: opea/*#image: ${IMAGE_REPO}opea/#g" compose.yaml
        echo "cat compose.yaml"
        cat compose.yaml
    fi

    # Start Docker Containers
    docker compose up -d
    n=0
    until [[ "$n" -ge 200 ]]; do
       docker logs tgi-service > $LOG_PATH/tgi_service_start.log
       if grep -q Connected $LOG_PATH/tgi_service_start.log; then
           break
       fi
       sleep 1s
       n=$((n+1))
    done
}


function validate_megaservice() {
    result=$(http_proxy="" curl http://${ip_address}:3008/v1/audioqna -XPOST -d '{"audio": "UklGRigAAABXQVZFZm10IBIAAAABAAEARKwAAIhYAQACABAAAABkYXRhAgAAAAEA", "max_tokens":64}' -H 'Content-Type: application/json')
    echo $result
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

function stop_docker() {
    cd $WORKPATH/docker/xeon
    docker compose stop && docker compose rm -f
}

function main() {

    stop_docker
    if [[ "$IMAGE_REPO" == "" ]]; then build_docker_images; fi
    start_services

    validate_megaservice
    # validate_frontend

    stop_docker
    echo y | docker system prune

}

main
