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
    workpath=$(dirname $(dirname "$PWD"))
    cd $workpath # go to ChatQnA
}

function docker_setup() {
    local card_num=1
    local port=8888
    local model_name="Intel/neural-chat-7b-v3-3"
    docker pull ghcr.io/huggingface/tgi-gaudi:1.2.1
    bash serving/tgi_gaudi/launch_tgi_service.sh $card_num $port $model_name
}

function launch_redis() {
    cd $workpath/langchain/docker
    docker compose -f docker-compose-langchain.yml up -d
}

function launch_server() {
    cd $workpath
    docker exec -it qna-rag-redis-server \
        bash -c "cd /ws && python ingest.py"

    docker exec -it qna-rag-redis-server \
        bash -c "python app/server.py"
}

function run_tests() {
    # todo
    cd $workpath
    echo "Requesting sth..."
}

function check_response() {
    # todo
    cd $workpath
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
    docker stop qna-rag-redis-server
    docker rm qna-rag-redis-server
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
