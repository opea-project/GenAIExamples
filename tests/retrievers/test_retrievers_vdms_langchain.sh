#!/bin/bash
# Copyright (C) 2024 Intel Corporation
# SPDX-License-Identifier: Apache-2.0

set -xe

WORKPATH=$(dirname "$PWD")
LOG_PATH="$WORKPATH/tests"
ip_address=$(hostname -I | awk '{print $1}')
no_proxy=$no_proxy,$ip_address

function build_docker_images() {
    cd $WORKPATH
    hf_token="dummy"
    docker build --no-cache -t opea/retriever-vdms:comps \
        --build-arg https_proxy=$https_proxy \
        --build-arg http_proxy=$http_proxy \
        --build-arg huggingfacehub_api_token=$hf_token\
        -f comps/retrievers/vdms/langchain/Dockerfile .

}

function start_service() {
    #unset http_proxy
    # vdms
    vdms_port=55555
    docker run -d --name test-comps-retriever-vdms-vector-db \
        -p $vdms_port:$vdms_port   intellabs/vdms:latest
    sleep 10s

    # tei endpoint
    tei_endpoint=5058
    model="BAAI/bge-base-en-v1.5"
    docker run -d --name="test-comps-retriever-vdms-tei-endpoint" \
        -p $tei_endpoint:80 -v ./data:/data \
        -e HTTPS_PROXY=$https_proxy -e HTTP_PROXY=$https_proxy \
        --pull always ghcr.io/huggingface/text-embeddings-inference:cpu-1.5 \
        --model-id $model
    sleep 30s

    export TEI_EMBEDDING_ENDPOINT="http://${ip_address}:${tei_endpoint}"

    export INDEX_NAME="rag-vdms"

    # vdms retriever
    unset http_proxy
    use_clip=0 #set to 1 if openai clip embedding should be used

    retriever_port=5059
    docker run -d --name="test-comps-retriever-vdms-server" -p $retriever_port:7000 --ipc=host \
    -e INDEX_NAME=$INDEX_NAME -e VDMS_HOST=$ip_address \
    -e https_proxy=$https_proxy -e http_proxy=$http_proxy \
    -e VDMS_PORT=$vdms_port -e HUGGINGFACEHUB_API_TOKEN=$HUGGINGFACEHUB_API_TOKEN \
    -e TEI_EMBEDDING_ENDPOINT=$TEI_EMBEDDING_ENDPOINT -e USECLIP=$use_clip \
     opea/retriever-vdms:comps
    sleep 3m
}

function validate_microservice() {


    retriever_port=5059
    URL="http://${ip_address}:$retriever_port/v1/retrieval"
    #test_embedding=$(python -c "import random; embedding = [random.uniform(-1, 1) for _ in range(768)]; print(embedding)")

    test_embedding=$(python -c "import random; embedding = [random.uniform(-1, 1) for _ in range(768)]; print(embedding)")

    HTTP_STATUS=$(curl -s -o /dev/null -w "%{http_code}" -X POST -d "{\"text\":\"test\",\"embedding\":${test_embedding}}" -H 'Content-Type: application/json' "$URL")

    #echo "HTTP_STATUS = $HTTP_STATUS"

    if [ "$HTTP_STATUS" -eq 200 ]; then
        echo "[ retriever ] HTTP status is 200. Checking content..."
        local CONTENT=$(curl -s -X POST -d "{\"text\":\"test\",\"embedding\":${test_embedding}}" -H 'Content-Type: application/json' "$URL" | tee ${LOG_PATH}/retriever.log)

        if echo "$CONTENT" | grep -q "retrieved_docs"; then
            echo "[ retriever ] Content is as expected."
        else
            echo "[ retriever ] Content does not match the expected result: $CONTENT"
            docker logs test-comps-retriever-vdms-server >> ${LOG_PATH}/retriever.log
            exit 1
        fi
    else
        echo "[ retriever ] HTTP status is not 200. Received status was $HTTP_STATUS"
        docker logs test-comps-retriever-vdms-server >> ${LOG_PATH}/retriever.log
        exit 1
    fi

    docker logs test-comps-retriever-vdms-tei-endpoint >> ${LOG_PATH}/tei.log
}

function stop_docker() {
    cid_vdms=$(docker ps -aq --filter "name=test-comps-retriever-vdms*")
    if [[ ! -z "$cid_vdms" ]]; then
        docker stop $cid_vdms && docker rm $cid_vdms && sleep 1s
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
