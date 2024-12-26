#!/bin/bash
# Copyright (C) 2024 Intel Corporation
# SPDX-License-Identifier: Apache-2.0

set -x

WORKPATH=$(dirname "$PWD")
LOG_PATH="$WORKPATH/tests"
ip_address=$(hostname -I | awk '{print $1}')
retriever_port="7000"
OPENSEARCH_INITIAL_ADMIN_PASSWORD="StRoNgOpEa0)"

function build_docker_images() {
    cd $WORKPATH
    docker build -t opea/retriever-opensearch:latest --build-arg https_proxy=$https_proxy --build-arg http_proxy=$http_proxy -f comps/retrievers/opensearch/langchain/Dockerfile .
    if [ $? -ne 0 ]; then
        echo "opea/retriever-opensearch built fail"
        exit 1
    else
        echo "opea/retriever-opensearch built successful"
    fi
}

function start_service() {
    # Start OpenSearch vector db container
    docker run -d \
        --name test-comps-retriever-opensearch \
        -e cluster.name=opensearch-cluster \
        -e node.name=opensearch-vector-db \
        -e discovery.seed_hosts=opensearch-vector-db \
        -e cluster.initial_master_nodes=opensearch-vector-db \
        -e bootstrap.memory_lock=true \
        -e "OPENSEARCH_JAVA_OPTS=-Xms512m -Xmx512m" \
        -e OPENSEARCH_INITIAL_ADMIN_PASSWORD=$OPENSEARCH_INITIAL_ADMIN_PASSWORD \
        --ulimit memlock=-1:-1 \
        --ulimit nofile=65536:65536 \
        -p 9200:9200 \
        -p 9600:9600 \
        opensearchproject/opensearch:latest

    # tei endpoint
    tei_endpoint=6060
    model="BAAI/bge-base-en-v1.5"
    docker run -d --name="test-comps-retriever-opensearch-tei-endpoint" -p $tei_endpoint:80 -v ./data:/data --pull always ghcr.io/huggingface/text-embeddings-inference:cpu-1.5 --model-id $model
    sleep 30s
    export TEI_EMBEDDING_ENDPOINT="http://${ip_address}:${tei_endpoint}"

    # Start OpenSearch retriever container
    OPENSEARCH_URL="http://${ip_address}:9200"
    INDEX_NAME="file-index"
    docker run -d \
        --name test-comps-retriever-opensearch-server \
        -p 7000:7000 \
        -e https_proxy=$https_proxy \
        -e http_proxy=$http_proxy \
        -e OPENSEARCH_INITIAL_ADMIN_PASSWORD=$OPENSEARCH_INITIAL_ADMIN_PASSWORD \
        -e OPENSEARCH_URL=$OPENSEARCH_URL \
        -e INDEX_NAME=$INDEX_NAME \
        -e TEI_EMBEDDING_ENDPOINT=${TEI_EMBEDDING_ENDPOINT} \
        opea/retriever-opensearch:latest

    sleep 2m
}

function validate_microservice() {
    export PATH="${HOME}/miniforge3/bin:$PATH"
    source activate
    URL="http://${ip_address}:$retriever_port/v1/retrieval"

    test_embedding=$(python3  -c "import random; embedding = [random.uniform(-1, 1) for _ in range(768)]; print(embedding)")

    HTTP_STATUS=$(curl -s -o /dev/null -w "%{http_code}" -X POST -d "{\"text\":\"test\",\"embedding\":${test_embedding}}" -H 'Content-Type: application/json' -k -u admin:$OPENSEARCH_INITIAL_ADMIN_PASSWORD "$URL")
    if [ "$HTTP_STATUS" -eq 200 ]; then
        echo "[ retriever ] HTTP status is 200. Checking content..."
        local CONTENT=$(curl -s -X POST -d "{\"text\":\"test\",\"embedding\":${test_embedding}}" -H 'Content-Type: application/json' "$URL" | tee ${LOG_PATH}/retriever.log)

        if echo "$CONTENT" | grep -q "retrieved_docs"; then
            echo "[ retriever ] Content is as expected."
        else
            echo "[ retriever ] Content does not match the expected result: $CONTENT"
            docker logs test-comps-retriever-opensearch-server >> ${LOG_PATH}/retriever.log
            docker logs test-comps-retriever-opensearch-tei-endpoint >> ${LOG_PATH}/tei.log
            exit 1
        fi
    else
        echo "[ retriever ] HTTP status is not 200. Received status was $HTTP_STATUS"
        docker logs test-comps-retriever-opensearch-server >> ${LOG_PATH}/retriever.log
        docker logs test-comps-retriever-opensearch-tei-endpoint >> ${LOG_PATH}/tei.log
        exit 1
    fi
}

function stop_service() {
    cid=$(docker ps -aq --filter "name=test-comps-retriever-opensearch*")
    if [[ ! -z "$cid" ]]; then docker stop $cid && docker rm $cid && sleep 1s; fi

}

function main() {
    stop_service

    build_docker_images
    start_service

    validate_microservice

    stop_service
    # echo y | docker system prune
}

main
