#!/bin/bash
# Copyright (c) 2024 Intel Corporation
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#    http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
set -xe

function test_env_setup() {
    WORKPATH=$(dirname $(dirname "$PWD"))
    DOCKER_NAME="qna-rag-redis-server"
    LOG_PATH="$WORKPATH/tests/langchain.log"
    cd $WORKPATH # go to ChatQnA
}

function docker_setup() {
    # todo
    local card_num=1
    local port=8888
    local model_name="Intel/neural-chat-7b-v3-3"
    docker pull ghcr.io/huggingface/tgi-gaudi:1.2.1
    bash serving/tgi_gaudi/launch_tgi_service.sh $card_num $port $model_name
}

function launch_redis() {
    # Launch LangChain Docker
    cd $WORKPATH/langchain/docker
    docker compose -f docker-compose-langchain.yml up -d

    # Ingest data into redis
    cd $WORKPATH
    docker exec -it $DOCKER_NAME \
        bash -c "cd /ws && python ingest.py"
}

function launch_server() {
    # Start the Backend Service
    cd $WORKPATH

    docker exec -it $DOCKER_NAME \
        bash -c "nohup python app/server.py &"
}

function run_tests() {
    # todo
    cd $WORKPATH
    echo "Requesting sth..." >>$LOG_PATH
}

function check_response() {
    # todo
    cd $WORKPATH
    echo "Checking response"
    local status=true
    if [ $status == false ]; then
        echo "Response check failed"
        exit 1
    else
        echo "Response check succeed"
    fi
}

function docker_stop() {
    docker stop $DOCKER_NAME
    docker rm $DOCKER_NAME
}

function main() {
    test_env_setup

    docker_setup
    launch_redis
    launch_server

    run_tests
    docker_stop

    check_response
}

main
