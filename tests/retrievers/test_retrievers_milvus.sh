#!/bin/bash
# Copyright (C) 2024 Intel Corporation
# SPDX-License-Identifier: Apache-2.0

set -x

WORKPATH=$(dirname "$PWD")
LOG_PATH="$WORKPATH/tests"
ip_address=$(hostname -I | awk '{print $1}')

function build_docker_images() {
    cd $WORKPATH
    docker build --no-cache -t opea/retriever-milvus:comps --build-arg https_proxy=$https_proxy --build-arg http_proxy=$http_proxy -f comps/retrievers/src/Dockerfile .
    if [ $? -ne 0 ]; then
        echo "opea/retriever-milvus built fail"
        exit 1
    else
        echo "opea/retriever-milvus built successful"
    fi
}

function start_service() {
    # start milvus vector db
    cd $WORKPATH/comps/dataprep/milvus/langchain/
    # wget https://raw.githubusercontent.com/milvus-io/milvus/v2.4.9/configs/milvus.yaml
    # wget https://github.com/milvus-io/milvus/releases/download/v2.4.9/milvus-standalone-docker-compose.yml -O docker-compose.yml
    # sed '/- \${DOCKER_VOLUME_DIRECTORY:-\.}\/volumes\/milvus:\/var\/lib\/milvus/a \ \ \ \ \ \ - \${DOCKER_VOLUME_DIRECTORY:-\.}\/milvus.yaml:\/milvus\/configs\/milvus.yaml' -i docker-compose.yml
    docker compose up -d

    # tei endpoint
    tei_endpoint=5014
    model="BAAI/bge-base-en-v1.5"
    docker run -d --name="test-comps-retriever-milvus-tei-endpoint" -p $tei_endpoint:80 -v ./data:/data --pull always ghcr.io/huggingface/text-embeddings-inference:cpu-1.5 --model-id $model
    export TEI_EMBEDDING_ENDPOINT="http://${ip_address}:${tei_endpoint}"

    # milvus retriever
    export MILVUS_HOST=${ip_address}
    export HUGGINGFACEHUB_API_TOKEN=$HF_TOKEN
    retriever_port=5015
    # unset http_proxy
    docker run -d --name="test-comps-retriever-milvus-server" -p ${retriever_port}:7000 --ipc=host -e HUGGINGFACEHUB_API_TOKEN=${HUGGINGFACEHUB_API_TOKEN} -e TEI_EMBEDDING_ENDPOINT=$TEI_EMBEDDING_ENDPOINT -e http_proxy=$http_proxy -e https_proxy=$https_proxy -e no_proxy=$no_proxy -e MILVUS_HOST=$ip_address -e LOGFLAG=true -e RETRIEVER_COMPONENT_NAME="OPEA_RETRIEVER_MILVUS" opea/retriever-milvus:comps

    sleep 1m
}

function validate_microservice() {
    local test_embedding="$1"

    retriever_port=5015
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
            docker logs test-comps-retriever-milvus-server >> ${LOG_PATH}/retriever.log
            exit 1
        fi
    else
        echo "[ retriever ] HTTP status is not 200. Received status was $HTTP_STATUS"
        docker logs test-comps-retriever-milvus-server >> ${LOG_PATH}/retriever.log
        exit 1
    fi
}

function stop_docker() {
    cid_retrievers=$(docker ps -aq --filter "name=test-comps-retriever-milvus*")
    if [[ ! -z "$cid_retrievers" ]]; then
        docker stop $cid_retrievers && docker rm $cid_retrievers && sleep 1s
    fi
    cid=$(docker ps -aq --filter "name=milvus-*")
    if [[ ! -z "$cid" ]]; then docker stop $cid && docker rm $cid && sleep 1s; fi
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
