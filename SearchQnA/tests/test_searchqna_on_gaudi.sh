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

function build_docker_images() {
    cd $WORKPATH/docker
    git clone https://github.com/opea-project/GenAIComps.git
    git clone https://github.com/huggingface/tei-gaudi

    echo "Build all the images with --no-cache, check docker_image_build.log for details..."
    service_list="searchqna searchqna-ui embedding-tei web-retriever-chroma reranking-tei llm-tgi tei-gaudi"
    docker compose -f docker_build_compose.yaml build ${service_list} --no-cache > ${LOG_PATH}/docker_image_build.log

    docker pull ghcr.io/huggingface/text-embeddings-inference:cpu-1.5
    docker pull ghcr.io/huggingface/tgi-gaudi:2.0.1
    docker images
}

function start_services() {

    cd $WORKPATH/docker/gaudi
    export GOOGLE_CSE_ID=$GOOGLE_CSE_ID
    export GOOGLE_API_KEY=$GOOGLE_API_KEY
    export HUGGINGFACEHUB_API_TOKEN=$HUGGINGFACEHUB_API_TOKEN

    export EMBEDDING_MODEL_ID=BAAI/bge-base-en-v1.5
    export TEI_EMBEDDING_ENDPOINT=http://$ip_address:3001
    export RERANK_MODEL_ID=BAAI/bge-reranker-base
    export TEI_RERANKING_ENDPOINT=http://$ip_address:3004

    export TGI_LLM_ENDPOINT=http://$ip_address:3006
    export LLM_MODEL_ID=Intel/neural-chat-7b-v3-3

    export MEGA_SERVICE_HOST_IP=${ip_address}
    export EMBEDDING_SERVICE_HOST_IP=${ip_address}
    export WEB_RETRIEVER_SERVICE_HOST_IP=${ip_address}
    export RERANK_SERVICE_HOST_IP=${ip_address}
    export LLM_SERVICE_HOST_IP=${ip_address}

    export EMBEDDING_SERVICE_PORT=3002
    export WEB_RETRIEVER_SERVICE_PORT=3003
    export RERANK_SERVICE_PORT=3005
    export LLM_SERVICE_PORT=3007
    export BACKEND_SERVICE_ENDPOINT="http://${ip_address}:3008/v1/searchqna"


    sed -i "s/backend_address/$ip_address/g" $WORKPATH/docker/ui/svelte/.env

    # Start Docker Containers
    docker compose up -d
    n=0
    until [[ "$n" -ge 500 ]]; do
        docker logs tgi-gaudi-server > $LOG_PATH/tgi_service_start.log
        if grep -q Connected $LOG_PATH/tgi_service_start.log; then
            break
        fi
        sleep 1s
        n=$((n+1))
    done
}


function validate_megaservice() {
    result=$(http_proxy="" curl http://${ip_address}:3008/v1/searchqna -XPOST -d '{"messages": "What is the latest news? Give me also the source link", "stream": "False"}' -H 'Content-Type: application/json')
    echo $result

    if [[ $result == *"news"* ]]; then
        echo "Result correct."
    else
        docker logs web-retriever-chroma-server > ${LOG_PATH}/web-retriever-chroma-server.log
        docker logs searchqna-gaudi-backend-server > ${LOG_PATH}/searchqna-gaudi-backend-server.log
        docker logs tei-embedding-gaudi-server > ${LOG_PATH}/tei-embedding-gaudi-server.log
        docker logs embedding-tei-server > ${LOG_PATH}/embedding-tei-server.log
        echo "Result wrong."
        exit 1
    fi

}

function validate_frontend() {
    cd $WORKPATH/docker/ui/svelte
    local conda_env_name="OPEA_e2e"

    export PATH=${HOME}/miniforge3/bin/:$PATH
    if conda info --envs | grep -q "$conda_env_name"; then
        echo "$conda_env_name exist!"
    else
        conda create -n ${conda_env_name} python=3.12 -y
    fi
    source activate ${conda_env_name}

    sed -i "s/localhost/$ip_address/g" playwright.config.ts

    conda install -c conda-forge nodejs -y
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
    cd $WORKPATH/docker/gaudi
    docker compose stop && docker compose rm -f
}

function main() {

    stop_docker
    if [[ "$IMAGE_REPO" == "opea" ]]; then build_docker_images; fi
    start_services

    validate_megaservice
    validate_frontend

    stop_docker
    echo y | docker system prune

}

main
