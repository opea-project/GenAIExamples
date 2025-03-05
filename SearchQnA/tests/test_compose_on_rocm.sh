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
export MODEL_PATH=${model_cache:-"./data"}

WORKPATH=$(dirname "$PWD")
LOG_PATH="$WORKPATH/tests"
ip_address=$(hostname -I | awk '{print $1}')

function build_docker_images() {
    cd $WORKPATH/docker_image_build
    git clone https://github.com/opea-project/GenAIComps.git && cd GenAIComps && git checkout "${opea_branch:-"main"}" && cd ../

    echo "Build all the images with --no-cache, check docker_image_build.log for details..."
    service_list="searchqna searchqna-ui embedding web-retriever reranking llm-textgen"
    docker compose -f build.yaml build ${service_list} --no-cache > ${LOG_PATH}/docker_image_build.log

    docker pull ghcr.io/huggingface/text-embeddings-inference:cpu-1.5
    docker pull ghcr.io/huggingface/text-generation-inference:2.3.1-rocm
    docker images && sleep 1s
}

function start_services() {
    cd $WORKPATH/docker_compose/amd/gpu/rocm/
    export SEARCH_HOST_IP=${ip_address}
    export SEARCH_EXTERNAL_HOST_IP=${ip_address}
    export SEARCH_EMBEDDING_MODEL_ID='BAAI/bge-base-en-v1.5'
    export SEARCH_TEI_EMBEDDING_ENDPOINT=http://${SEARCH_HOST_IP}:3001
    export SEARCH_RERANK_MODEL_ID='BAAI/bge-reranker-base'
    export SEARCH_TEI_RERANKING_ENDPOINT=http://${SEARCH_HOST_IP}:3004
    export SEARCH_HUGGINGFACEHUB_API_TOKEN=${HUGGINGFACEHUB_API_TOKEN}
    export SEARCH_OPENAI_API_KEY=${OPENAI_API_KEY}
    export SEARCH_TGI_LLM_ENDPOINT=http://${SEARCH_HOST_IP}:3006
    export SEARCH_LLM_MODEL_ID='Intel/neural-chat-7b-v3-3'
    export SEARCH_MEGA_SERVICE_HOST_IP=${SEARCH_EXTERNAL_HOST_IP}
    export SEARCH_EMBEDDING_SERVICE_HOST_IP=${SEARCH_HOST_IP}
    export SEARCH_WEB_RETRIEVER_SERVICE_HOST_IP=${SEARCH_HOST_IP}
    export SEARCH_RERANK_SERVICE_HOST_IP=${SEARCH_HOST_IP}
    export SEARCH_LLM_SERVICE_HOST_IP=${SEARCH_HOST_IP}
    export SEARCH_EMBEDDING_SERVICE_PORT=3002
    export SEARCH_WEB_RETRIEVER_SERVICE_PORT=3003
    export SEARCH_RERANK_SERVICE_PORT=3005
    export SEARCH_LLM_SERVICE_PORT=3007
    export SEARCH_FRONTEND_SERVICE_PORT=5173
    export SEARCH_BACKEND_SERVICE_PORT=3008
    export SEARCH_BACKEND_SERVICE_ENDPOINT=http://${SEARCH_HOST_IP}:${SEARCH_BACKEND_SERVICE_PORT}/v1/searchqna
    export SEARCH_GOOGLE_API_KEY=${GOOGLE_API_KEY}
    export SEARCH_GOOGLE_CSE_ID=${GOOGLE_CSE_ID}

    sed -i "s/backend_address/$ip_address/g" $WORKPATH/ui/svelte/.env

    # Start Docker Containers
    docker compose up -d > ${LOG_PATH}/start_services_with_compose.log
    n=0
    until [[ "$n" -ge 100 ]]; do
        docker logs search-tgi-service > $LOG_PATH/search-tgi-service_start.log
        if grep -q Connected $LOG_PATH/search-tgi-service_start.log; then
            break
        fi
        sleep 5s
        n=$((n+1))
    done
}


function validate_megaservice() {
    result=$(http_proxy="" curl http://${ip_address}:3008/v1/searchqna -XPOST -d '{"messages": "What is black myth wukong?", "stream": "False"}' -H 'Content-Type: application/json')
    echo $result

    if [[ $result == *"the"* ]]; then
        docker logs search-web-retriever-server
        docker logs search-backend-server
        echo "Result correct."
    else
        docker logs search-web-retriever-server
        docker logs search-backend-server
        echo "Result wrong."
        exit 1
    fi

}

function validate_frontend() {
    cd $WORKPATH/ui/svelte
    local conda_env_name="OPEA_e2e"
    export PATH=${HOME}/miniconda3/bin/:$PATH
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
    cd $WORKPATH/docker_compose/amd/gpu/rocm/
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
