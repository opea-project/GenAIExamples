#!/bin/bash
# Copyright (C) 2024 Intel Corporation
# SPDX-License-Identifier: Apache-2.0

set -x

WORKPATH=$(dirname "$PWD")
LOG_PATH="$WORKPATH/tests"
ip_address=$(hostname -I | awk '{print $1}')

function build_docker_images() {
    cd $WORKPATH
    docker build --no-cache -t opea/retriever-pinecone:comps --build-arg https_proxy=$https_proxy --build-arg http_proxy=$http_proxy -f comps/retrievers/src/Dockerfile .
    if [ $? -ne 0 ]; then
        echo "opea/retriever-pinecone built fail"
        exit 1
    else
        echo "opea/retriever-pinecone built successful"
    fi
}

function start_service() {
    # pinecone retriever
    export PINECONE_API_KEY=$PINECONE_KEY
    export PINECONE_INDEX_NAME="langchain-test"
    export HUGGINGFACEHUB_API_TOKEN=$HF_TOKEN
    retriever_port=5054
    unset http_proxy
    docker run -d --name="test-comps-retriever-pinecone-server" -p ${retriever_port}:7000 --ipc=host -e HUGGINGFACEHUB_API_TOKEN=${HUGGINGFACEHUB_API_TOKEN} -e http_proxy=$http_proxy -e https_proxy=$https_proxy -e no_proxy=$no_proxy -e PINECONE_API_KEY=$PINECONE_API_KEY -e PINECONE_INDEX_NAME=$PINECONE_INDEX_NAME -e INDEX_NAME=$PINECONE_INDEX_NAME -e LOGFLAG=true -e RETRIEVER_COMPONENT_NAME="OPEA_RETRIEVER_PINECONE" opea/retriever-pinecone:comps

    sleep 1m
}

function validate_microservice() {
    local test_embedding="$1"

    retriever_port=5054
    export PATH="${HOME}/miniforge3/bin:$PATH"
    source activate
    URL="http://${ip_address}:$retriever_port/v1/retrieval"

    HTTP_STATUS=$(curl -s -o /dev/null -w "%{http_code}" -X POST -d "{\"text\":\"test\",\"embedding\":${test_embedding}}" -H 'Content-Type: application/json' "$URL")
    if [ "$HTTP_STATUS" -eq 200 ]; then
        echo "[ retriever ] HTTP status is 200. Checking content..."
        local CONTENT=$(curl -s -X POST -d "{\"text\":\"test\",\"embedding\":${test_embedding}}" -H 'Content-Type: application/json' "$URL" | tee ${LOG_PATH}/retriever.log)

        if echo "$CONTENT" | grep -q "retrieved_docs"; then
            echo "[ retriever ] Content is as expected."
        else
            echo "[ retriever ] Content does not match the expected result: $CONTENT"
            docker logs test-comps-retriever-pinecone-server >> ${LOG_PATH}/retriever.log
            exit 1
        fi
    else
        echo "[ retriever ] HTTP status is not 200. Received status was $HTTP_STATUS"
        docker logs test-comps-retriever-pinecone-server >> ${LOG_PATH}/retriever.log
        exit 1
    fi
}

function stop_docker() {
    cid_retrievers=$(docker ps -aq --filter "name=test-comps-retriever-pinecone*")
    if [[ ! -z "$cid_retrievers" ]]; then
        docker stop $cid_retrievers && docker rm $cid_retrievers && sleep 1s
    fi
}

function main() {

    stop_docker
    build_docker_images

    start_service
    test_embedding=$(python -c "import random; embedding = [random.uniform(-1, 1) for _ in range(768)]; print(embedding)")
    validate_microservice "$test_embedding"

    stop_docker
    echo y | docker system prune

}

main
