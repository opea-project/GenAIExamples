#!/bin/bash
# Copyright (C) 2024 Intel Corporation
# SPDX-License-Identifier: Apache-2.0

#set -xe

WORKPATH=$(dirname "$PWD")
LOG_PATH="$WORKPATH/tests"
ip_address=$(hostname -I | awk '{print $1}')

function build_docker_images() {
    echo "Building the docker images"
    cd $WORKPATH
    echo $WORKPATH
    docker build --no-cache -t opea/comps-agent-langchain:comps -f comps/agent/langchain/docker/Dockerfile .
    if [ $? -ne 0 ]; then
        echo "opea/comps-agent-langchain built fail"
        exit 1
    else
        echo "opea/comps-agent-langchain built successful"
    fi
}

function start_service() {
    # redis endpoint
    export model=meta-llama/Meta-Llama-3-8B-Instruct
    export HUGGINGFACEHUB_API_TOKEN=${HF_TOKEN}
    echo "token is ${HF_TOKEN}"

    #single card
    echo "start tgi gaudi service"
    docker run -d --runtime=habana --name "test-comps-tgi-gaudi-service" -p 8080:80 -v ./data:/data -e HF_TOKEN=$HF_TOKEN -e HABANA_VISIBLE_DEVICES=all -e OMPI_MCA_btl_vader_single_copy_mechanism=none --cap-add=sys_nice --ipc=host ghcr.io/huggingface/tgi-gaudi:latest --model-id $model --max-input-tokens 4096 --max-total-tokens 8092
    sleep 5s
    docker logs test-comps-tgi-gaudi-service

    echo "Starting agent microservice"
    docker run -d --runtime=runc --name="test-comps-langchain-agent-endpoint" -v $WORKPATH/comps/agent/langchain/tools:/home/user/comps/agent/langchain/tools -p 5042:9090 --ipc=host -e HUGGINGFACEHUB_API_TOKEN=${HUGGINGFACEHUB_API_TOKEN} -e model=${model} -e strategy=react -e llm_endpoint_url=http://${ip_address}:8080 -e llm_engine=tgi -e recursion_limit=5 -e require_human_feedback=false -e tools=/home/user/comps/agent/langchain/tools/custom_tools.yaml opea/comps-agent-langchain:comps
    sleep 5s
    docker logs test-comps-langchain-agent-endpoint

    echo "Waiting tgi gaudi ready"
    n=0
    until [[ "$n" -ge 100 ]] || [[ $ready == true ]]; do
        docker logs test-comps-tgi-gaudi-service > ${WORKPATH}/tests/tgi-gaudi-service.log
        n=$((n+1))
        if grep -q Connected ${WORKPATH}/tests/tgi-gaudi-service.log; then
            break
        fi
        sleep 5s
    done
    sleep 5s
    docker logs test-comps-tgi-gaudi-service
    echo "Service started successfully"
}

function validate() {
    local CONTENT="$1"
    local EXPECTED_RESULT="$2"
    local SERVICE_NAME="$3"

    if echo "$CONTENT" | grep -q "$EXPECTED_RESULT"; then
        echo "[ $SERVICE_NAME ] Content is as expected: $CONTENT"
        echo 0
    else
        echo "[ $SERVICE_NAME ] Content does not match the expected result: $CONTENT"
        echo 1
    fi
}

function validate_microservice() {
    echo "Testing agent service"
    local CONTENT=$(curl http://${ip_address}:5042/v1/chat/completions -X POST -H "Content-Type: application/json" -d '{
     "query": "What is Intel OPEA project?"
    }' | tee ${LOG_PATH}/test-agent-langchain.log)
    local EXIT_CODE=$(validate "$CONTENT" "OPEA" "test-agent-langchain")
    echo "$EXIT_CODE"
    local EXIT_CODE="${EXIT_CODE:0-1}"
    echo "return value is $EXIT_CODE"
    if [ "$EXIT_CODE" == "1" ]; then
        docker logs test-comps-tgi-gaudi-service &> ${LOG_PATH}/test-comps-tgi-gaudi-service.log
        docker logs test-comps-langchain-agent-endpoint &> ${LOG_PATH}/test-comps-langchain-agent-endpoint.log
        exit 1
    fi
}

function stop_docker() {
    cid=$(docker ps -aq --filter "name=test-comps-tgi-gaudi-service")
    echo "Stopping the docker containers "${cid}
    if [[ ! -z "$cid" ]]; then docker rm $cid -f && sleep 1s; fi
    cid=$(docker ps -aq --filter "name=test-comps-langchain-agent-endpoint")
    echo "Stopping the docker containers "${cid}
    if [[ ! -z "$cid" ]]; then docker rm $cid -f && sleep 1s; fi
    echo "Docker containers stopped successfully"
}

function main() {

    stop_docker

    build_docker_images
    start_service

    validate_microservice

    stop_docker
    echo y | docker system prune 2>&1 > /dev/null

}

main
