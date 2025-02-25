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

    echo "Build all the images with --no-cache, check docker_image_build.log for details..."
    service_list="searchqna searchqna-ui embedding web-retriever reranking llm-textgen"
    docker compose -f build.yaml build ${service_list} --no-cache > ${LOG_PATH}/docker_image_build.log

    docker pull ghcr.io/huggingface/text-embeddings-inference:cpu-1.5
    docker pull ghcr.io/huggingface/tei-gaudi:1.5.0
    docker pull ghcr.io/huggingface/tgi-gaudi:2.0.6
    docker images && sleep 1s
}

function start_services() {

    cd $WORKPATH/docker_compose/intel/hpu/gaudi
    export GOOGLE_CSE_ID=$GOOGLE_CSE_ID
    export GOOGLE_API_KEY=$GOOGLE_API_KEY
    export HUGGINGFACEHUB_API_TOKEN=$HUGGINGFACEHUB_API_TOKEN

    export EMBEDDING_MODEL_ID=BAAI/bge-base-en-v1.5
    export TEI_EMBEDDING_ENDPOINT=http://$ip_address:3001
    export RERANK_MODEL_ID=BAAI/bge-reranker-base
    export RERANK_TYPE="tei"
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
    export host_ip=${ip_address}
    export LOGFLAG=true


    sed -i "s/backend_address/$ip_address/g" $WORKPATH/ui/svelte/.env

    # Start Docker Containers
    docker compose up -d > ${LOG_PATH}/start_services_with_compose.log

    sleep 10s
}


function validate_megaservice() {
    result=$(curl http://${ip_address}:3008/v1/searchqna -X POST -d '{"messages": "What is the capital of China?", "stream": "False"}' -H 'Content-Type: application/json')
    echo $result

    docker logs web-retriever-server > ${LOG_PATH}/web-retriever-server.log
    docker logs searchqna-gaudi-backend-server > ${LOG_PATH}/searchqna-gaudi-backend-server.log
    docker logs tei-embedding-gaudi-server > ${LOG_PATH}/tei-embedding-gaudi-server.log
    docker logs embedding-gaudi-server > ${LOG_PATH}/embedding-gaudi-server.log

    if [[ $result == *"capital"* ]]; then
        echo "Result correct."
    else
        echo "Result wrong."
        exit 1
    fi

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

    validate_megaservice
    validate_frontend

    stop_docker
    echo y | docker system prune

}

main
