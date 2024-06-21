#!/bin/bash
# Copyright (C) 2024 Intel Corporation
# SPDX-License-Identifier: Apache-2.0

set -xe

function test_env_setup() {
    WORKPATH=$(dirname "$PWD")
    LOG_PATH="$WORKPATH/tests/langchain.log"

    REDIS_CONTAINER_NAME="test-redis-vector-db"
    LANGCHAIN_CONTAINER_NAME="test-qna-rag-redis-server"
    AUDIOQNA_CONTAINER_NAME="test-AudioQnA_server"
    cd $WORKPATH
}

function rename() {
    # Rename the docker container/image names to avoid conflict with local test
    cd ${WORKPATH}
    sed -i "s/container_name: redis-vector-db/container_name: ${REDIS_CONTAINER_NAME}/g" langchain/docker/docker-compose.yml
    sed -i "s/container_name: qna-rag-redis-server/container_name: ${LANGCHAIN_CONTAINER_NAME}/g" langchain/docker/docker-compose.yml
    sed -i "s/image: intel\/gen-ai-examples:qna-rag-redis-server/image: intel\/gen-ai-examples:${LANGCHAIN_CONTAINER_NAME}/g" langchain/docker/docker-compose.yml
    sed -i "s/ChatQnA_server/${AUDIOQNA_CONTAINER_NAME}/g" serving/tgi_gaudi/launch_tgi_service.sh
}

function launch_tgi_gaudi_service() {
    local card_num=1
    local port=8888
    local model_name="Intel/neural-chat-7b-v3-3"

    cd ${WORKPATH}

    # Reset the tgi port
    sed -i "s/8080/$port/g" langchain/redis/rag_redis/config.py
    sed -i "s/8080/$port/g" langchain/docker/qna-app/app/server.py
    sed -i "s/8080/$port/g" langchain/docker/qna-app/Dockerfile

    docker pull ghcr.io/huggingface/tgi-gaudi:1.2.1
    bash serving/tgi_gaudi/launch_tgi_service.sh $card_num $port $model_name
    sleep 3m # Waits 3 minutes
}

function launch_redis_and_langchain_service() {
    cd $WORKPATH
    export HUGGINGFACEHUB_API_TOKEN=${HUGGINGFACEHUB_API_TOKEN}
    local port=8890
    sed -i "s/port=8000/port=$port/g" langchain/docker/qna-app/app/server.py
    docker compose -f langchain/docker/docker-compose.yml up -d --build

    # Ingest data into redis
    docker exec $LANGCHAIN_CONTAINER_NAME \
        bash -c "cd /ws && python ingest.py > /dev/null"
}

function start_backend_service() {
    cd $WORKPATH
    docker exec $LANGCHAIN_CONTAINER_NAME \
        bash -c "nohup python app/server.py &"
    sleep 1m
}

function run_tests() {
    cd $WORKPATH
    local port=8890
    curl 127.0.0.1:$port/v1/rag/chat \
        -X POST \
        -d "{\"query\":\"What is the total revenue of Nike in 2023?\"}" \
        -H 'Content-Type: application/json' > $LOG_PATH
}

function check_response() {
    cd $WORKPATH
    echo "Checking response"
    local status=false
    if [[ -f $LOG_PATH ]] && [[ $(grep -c "\$51.2 billion" $LOG_PATH) != 0 ]]; then
        status=true
    fi

    if [ $status == false ]; then
        echo "Response check failed"
        exit 1
    else
        echo "Response check succeed"
    fi
}

function docker_stop() {
    local container_name=$1
    cid=$(docker ps -aq --filter "name=$container_name")
    if [[ ! -z "$cid" ]]; then docker stop $cid && docker rm $cid; fi
}

function main() {
    test_env_setup
    rename
    docker_stop $CHATQNA_CONTAINER_NAME && docker_stop $LANGCHAIN_CONTAINER_NAME && docker_stop $REDIS_CONTAINER_NAME && sleep 5s

    launch_tgi_gaudi_service
    launch_redis_and_langchain_service
    start_backend_service

    run_tests

    docker_stop $AUDIOQNA_CONTAINER_NAME && docker_stop $LANGCHAIN_CONTAINER_NAME && docker_stop $REDIS_CONTAINER_NAME && sleep 5s
    echo y | docker system prune

    check_response
}

main
