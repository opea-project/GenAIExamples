#!/bin/bash
# Copyright (C) 2024 Intel Corporation
# SPDX-License-Identifier: Apache-2.0

set -x

WORKPATH=$(dirname "$PWD")
LOG_PATH="$WORKPATH/tests"
ip_address=$(hostname -I | awk '{print $1}')

function build_docker_images() {
    cd $WORKPATH
    docker build --no-cache -t opea/retriever-pinecone:comps --build-arg https_proxy=$https_proxy --build-arg http_proxy=$http_proxy -f comps/retrievers/pinecone/langchain/Dockerfile .
    if [ $? -ne 0 ]; then
        echo "opea/retriever-pinecone built fail"
        exit 1
    else
        echo "opea/retriever-pinecone built successful"
    fi
}

function start_service() {
    # tei endpoint
    tei_endpoint=5053
    model="BAAI/bge-base-en-v1.5"
    docker run -d --name="test-comps-retriever-pinecone-tei-endpoint" -e HTTPS_PROXY=$https_proxy -e HTTP_PROXY=$https_proxy -p $tei_endpoint:80 -v ./data:/data --pull always ghcr.io/huggingface/text-embeddings-inference:cpu-1.2 --model-id $model
    bash ./tests/utils/wait-for-it.sh ${ip_address}:${tei_endpoint} -s -t 30 -- echo "tei endpoint up"
    TEI_ENDPOINT_UP=$?
    if [ ${TEI_ENDPOINT_UP} -ne 0 ]; then
        echo "Could not start TEI endpoint."
        return 1
    fi
    export TEI_EMBEDDING_ENDPOINT="http://${ip_address}:${tei_endpoint}"
    echo ${TEI_EMBEDDING_ENDPOINT}

    # pinecone retriever
    export PINECONE_API_KEY=$PINECONE_KEY
    export PINECONE_INDEX_NAME="langchain-test"
    export HUGGINGFACEHUB_API_TOKEN=$HF_TOKEN
    retriever_port=5054
    unset http_proxy
    docker run -d --name="test-comps-retriever-pinecone-server" -p ${retriever_port}:7000 --ipc=host -e HUGGINGFACEHUB_API_TOKEN=${HUGGINGFACEHUB_API_TOKEN} -e TEI_EMBEDDING_ENDPOINT=$TEI_EMBEDDING_ENDPOINT -e http_proxy=$http_proxy -e https_proxy=$https_proxy -e PINECONE_API_KEY=$PINECONE_API_KEY -e PINECONE_INDEX_NAME=$PINECONE_INDEX_NAME -e INDEX_NAME=$PINECONE_INDEX_NAME -e LOGFLAG="DEBUG" opea/retriever-pinecone:comps

    bash ./tests/utils/wait-for-it.sh ${ip_address}:$retriever_port -s -t 100 -- echo "Retriever up"
    RETRIEVER_UP=$?
    if [ ${RETRIEVER_UP} -ne 0 ]; then
        echo "Could not start Retriever."
        return 1
    fi

    sleep 5s
    bash ./tests/utils/wait-for-it.sh ${ip_address}:$retriever_port -s -t 1 -- echo "Retriever still up"
    RETRIEVER_UP=$?
    if [ ${RETRIEVER_UP} -ne 0 ]; then
        echo "Retriever crashed."
        return 1
    fi

}

function validate_microservice() {
    retriever_port=5054
    test_embedding=$(python -c "import random; embedding = [random.uniform(-1, 1) for _ in range(768)]; print(embedding)")

    result=$(http_proxy='' curl  --noproxy $ip_address http://${ip_address}:$retriever_port/v1/retrieval \
        -X POST \
        -d "{\"text\":\"test\",\"embedding\":${test_embedding}}" \
        -H 'Content-Type: application/json')
    if [[ $result == *"retrieved_docs"* ]]; then
        echo "Result correct."
    else
        echo "Result wrong. Received was $result"
        docker logs test-comps-retriever-pinecone-tei-endpoint >> ${LOG_PATH}/tei-endpoint.log
        docker logs test-comps-retriever-pinecone-server >> ${LOG_PATH}/retriever-pinecone.log
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

    validate_microservice

    stop_docker
    echo y | docker system prune

}

main
