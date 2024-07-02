#!/bin/bash
# Copyright (C) 2024 Intel Corporation
# SPDX-License-Identifier: Apache-2.0

set -e

WORKPATH=$(dirname "$PWD")
LOG_PATH="$WORKPATH/tests"
ip_address=$(hostname -I | awk '{print $1}')

function build_docker_images() {
    cd $WORKPATH
    git clone https://github.com/opea-project/GenAIComps.git
    cd GenAIComps

    docker build -t opea/embedding-tei:latest  -f comps/embeddings/langchain/docker/Dockerfile .
    docker build -t opea/web-retriever-chroma:latest  -f comps/web_retrievers/langchain/chroma/docker/Dockerfile .
    docker build -t opea/reranking-tei:latest  -f comps/reranks/langchain/docker/Dockerfile .
    docker build -t opea/llm-tgi:latest  -f comps/llms/text-generation/tgi/Dockerfile .
    docker pull ghcr.io/huggingface/text-embeddings-inference:cpu-1.2
    docker pull ghcr.io/huggingface/text-generation-inference:1.4
    cd $WORKPATH/docker
    docker build -t opea/searchqna:latest -f Dockerfile .

    # cd $WORKPATH/docker/ui
    # docker build --no-cache -t opea/searchqna-ui:latest -f docker/Dockerfile .

    docker images
}

function start_services() {
    cd $WORKPATH/docker/xeon
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

    # sed -i "s/backend_address/$ip_address/g" $WORKPATH/docker/ui/svelte/.env

    # Replace the container name with a test-specific name
    # echo "using image repository $IMAGE_REPO and image tag $IMAGE_TAG"
    # sed -i "s#image: opea/chatqna:latest#image: opea/chatqna:${IMAGE_TAG}#g" docker_compose.yaml
    # sed -i "s#image: opea/chatqna-ui:latest#image: opea/chatqna-ui:${IMAGE_TAG}#g" docker_compose.yaml
    # sed -i "s#image: opea/*#image: ${IMAGE_REPO}opea/#g" docker_compose.yaml
    # Start Docker Containers
    docker compose -f docker_compose.yaml up -d
    n=0
    until [[ "$n" -ge 200 ]]; do
        docker logs tgi-service > tgi_service_start.log
        if grep -q Connected tgi_service_start.log; then
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
        docker logs web-retriever-chroma-server
        docker logs searchqna-xeon-backend-server
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
    container_list=$(cat docker_compose.yaml | grep container_name | cut -d':' -f2)
    for container_name in $container_list; do
        cid=$(docker ps -aq --filter "name=$container_name")
        if [[ ! -z "$cid" ]]; then docker stop $cid && docker rm $cid && sleep 1s; fi
    done
}

function main() {

    stop_docker
    build_docker_images
    # begin_time=$(date +%s)
    start_services
    # end_time=$(date +%s)
    # maximal_duration=$((end_time-begin_time))
    # echo "Mega service start duration is "$maximal_duration"s" && sleep 1s

    validate_megaservice
    # validate_frontend

    stop_docker
    echo y | docker system prune

}

main
