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
    WORKPATH=$(dirname "$PWD")
    LOG_PATH="$WORKPATH/tests/langchain.log"

    TGI_CONTAINER_NAME="test-tgi-gaudi-server"
    LANGCHAIN_CONTAINER_NAME="test-searchqna-gaudi"
}

function rename() {
    # Rename the docker container/image names to avoid conflict with local test
    cd ${WORKPATH}
    sed -i "s/tgi-gaudi-server/${TGI_CONTAINER_NAME}/g" serving/tgi_gaudi/launch_tgi_service.sh
}

function launch_tgi_gaudi_service() {
    local card_num=1
    local port=8870
    local model_name="Intel/neural-chat-7b-v3-3"

    cd ${WORKPATH}

    docker pull ghcr.io/huggingface/tgi-gaudi:1.2.1
    bash serving/tgi_gaudi/launch_tgi_service.sh $card_num $port $model_name
    sleep 2m
}

function launch_langchain_service() {
    cd $WORKPATH
    local port=8875
    cd langchain/docker
    docker build . --build-arg http_proxy=${http_proxy} --build-arg https_proxy=${http_proxy} -t intel/gen-ai-examples:${LANGCHAIN_CONTAINER_NAME}

    tgi_ip_name=$(echo $(hostname) | tr '[a-z]-' '[A-Z]_')_$(echo 'IP')
    tgi_ip=$(eval echo '$'$tgi_ip_name)
    docker run -d --name=${LANGCHAIN_CONTAINER_NAME} -e TGI_ENDPOINT=http://${tgi_ip}:8870 -e GOOGLE_CSE_ID=${GOOGLE_CSE_ID} -e GOOGLE_API_KEY=${GOOGLE_API_KEY} -e HF_TOKEN=${HF_TOKEN} \
    -p ${port}:8000 --runtime=habana -e HABANA_VISIBE_DEVILCES=all -e OMPI_MCA_btl_vader_single_copy_mechanism=none --cap-add=sys_nice --ipc=host intel/gen-ai-examples:${LANGCHAIN_CONTAINER_NAME}

    sleep 2m
}


function run_tests() {
    cd $WORKPATH
    local port=8875

    curl http://localhost:${port}/v1/rag/web_search_chat \
        -X POST \
        -d '{"query":"What is the GitHub Repo link of Intel Neural Compressor?"}' \
        -H 'Content-Type: application/json' > $LOG_PATH

}

function check_response() {
    cd $WORKPATH
    echo "Checking response"
    local status=false
    if [[ -f $LOG_PATH ]] && [[ $(grep -c "Neural Compressor" $LOG_PATH) != 0 ]]; then
        status=true
    fi

    if [ $status == false ]; then
        echo "Response check failed, please check the logs in artifacts!"
        exit 1
    else
        echo "Response check succeed!"
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
    docker_stop $TGI_CONTAINER_NAME && docker_stop $LANGCHAIN_CONTAINER_NAME && sleep 5s

    launch_tgi_gaudi_service
    launch_langchain_service

    run_tests
    check_response

    docker_stop $TGI_CONTAINER_NAME && docker_stop $LANGCHAIN_CONTAINER_NAME && sleep 5s
    echo y | docker system prune
}

main
