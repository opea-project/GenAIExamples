#!/bin/bash
# Copyright (C) 2024 Intel Corporation
# SPDX-License-Identifier: Apache-2.0

set -x

WORKPATH=$(dirname "$PWD")
LOG_PATH="$WORKPATH/tests"
ip_address=$(hostname -I | awk '{print $1}')
function build_docker_images() {
    cd $WORKPATH

    docker build --no-cache --build-arg https_proxy=$https_proxy --build-arg http_proxy=$http_proxy -t opea/vectorstore-pathway:comps -f comps/vectorstores/pathway/Dockerfile .

    cd $WORKPATH

    docker build --no-cache -t opea/retriever-pathway:comps --build-arg https_proxy=$https_proxy --build-arg http_proxy=$http_proxy -f comps/retrievers/pathway/langchain/Dockerfile .
    if [ $? -ne 0 ]; then
        echo "opea/retriever-pathway built fail"
        exit 1
    else
        echo "opea/retriever-pathway built successful"
    fi
}

function start_service() {
    cd $WORKPATH

    # tei endpoint
    tei_endpoint=5008
    model="BAAI/bge-base-en-v1.5"
    docker run -d --name="test-comps-retriever-pathway-tei-endpoint" -e http_proxy=$http_proxy -e https_proxy=$https_proxy -p $tei_endpoint:80 -v ./data:/data --pull always ghcr.io/huggingface/text-embeddings-inference:cpu-1.2 --model-id $model

    sleep 30s
    export TEI_EMBEDDING_ENDPOINT="http://${ip_address}:${tei_endpoint}"

    result=$(http_proxy=''
    curl $TEI_EMBEDDING_ENDPOINT     -X POST     -d '{"inputs":"Hey,"}'     -H 'Content-Type: application/json')

    echo "embed_result:"
    echo $result

    sleep 30s

    # pathway
    export PATHWAY_HOST="0.0.0.0"
    export PATHWAY_PORT=5433

    docker run -d --name="test-comps-retriever-pathway-vectorstore" -e PATHWAY_HOST=${PATHWAY_HOST} -e PATHWAY_PORT=${PATHWAY_PORT} -e TEI_EMBEDDING_ENDPOINT=${TEI_EMBEDDING_ENDPOINT} -e http_proxy=$http_proxy -e https_proxy=$https_proxy -v $WORKPATH/comps/vectorstores/pathway/README.md:/app/data/README.md -p ${PATHWAY_PORT}:${PATHWAY_PORT} --network="host" opea/vectorstore-pathway:comps

    sleep 45s

    export PATHWAY_HOST=$ip_address  # needed in order to reach to vector store

    docker run -d --name="test-comps-retriever-pathway-ms" -p 5009:7000 -e PATHWAY_HOST=${PATHWAY_HOST} -e PATHWAY_PORT=${PATHWAY_PORT} -e http_proxy=$http_proxy -e https_proxy=$https_proxy opea/retriever-pathway:comps

    sleep 10s
}

function validate_microservice() {
    retriever_port=5009
    export PATH="${HOME}/miniforge3/bin:$PATH"

    test_embedding=$(python -c "import random; embedding = [random.uniform(-1, 1) for _ in range(768)]; print(embedding)")

    result=$(http_proxy=''
    curl http://${ip_address}:$retriever_port/v1/retrieval \
        -X POST \
        -d "{\"text\":\"test\",\"embedding\":${test_embedding}}" \
        -H 'Content-Type: application/json')
    if [[ $result == *"retrieved_docs"* ]]; then
        echo "Result correct."
    else
        echo "Result wrong. Received was $result"
        docker logs test-comps-retriever-pathway-vectorstore >> ${LOG_PATH}/vectorstore-pathway.log
        docker logs test-comps-retriever-pathway-tei-endpoint >> ${LOG_PATH}/tei-endpoint.log
        docker logs test-comps-retriever-pathway-ms >> ${LOG_PATH}/retriever-pathway.log
        exit 1
    fi
}

function stop_docker() {
    cid=$(docker ps -aq --filter "name=test-comps-retriever-pathway*")
    if [[ ! -z "$cid" ]]; then docker stop $cid && docker rm $cid && sleep 1s; fi
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
