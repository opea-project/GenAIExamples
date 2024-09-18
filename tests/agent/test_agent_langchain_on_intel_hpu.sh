#!/bin/bash
# Copyright (C) 2024 Intel Corporation
# SPDX-License-Identifier: Apache-2.0

#set -xe

WORKPATH=$(dirname "$PWD")
LOG_PATH="$WORKPATH/tests"
ip_address=$(hostname -I | awk '{print $1}')
tgi_port=8080
tgi_volume=$WORKPATH/data

export model=mistralai/Mistral-7B-Instruct-v0.3
export HUGGINGFACEHUB_API_TOKEN=${HF_TOKEN}

function build_docker_images() {
    echo "Building the docker images"
    cd $WORKPATH
    echo $WORKPATH
    docker build --no-cache -t opea/agent-langchain:comps -f comps/agent/langchain/Dockerfile .
    if [ $? -ne 0 ]; then
        echo "opea/agent-langchain built fail"
        exit 1
    else
        echo "opea/agent-langchain built successful"
    fi
}

function start_tgi_service() {
    # redis endpoint
    echo "token is ${HF_TOKEN}"

    #single card
    echo "start tgi gaudi service"
    docker run -d --runtime=habana --name "test-comps-tgi-gaudi-service" -p $tgi_port:80 -v $tgi_volume:/data -e HF_TOKEN=$HF_TOKEN -e HABANA_VISIBLE_DEVICES=all -e OMPI_MCA_btl_vader_single_copy_mechanism=none --cap-add=sys_nice --ipc=host ghcr.io/huggingface/tgi-gaudi:latest --model-id $model --max-input-tokens 4096 --max-total-tokens 8092
    sleep 5s
    echo "Waiting tgi gaudi ready"
    n=0
    until [[ "$n" -ge 100 ]] || [[ $ready == true ]]; do
        docker logs test-comps-tgi-gaudi-service &> ${LOG_PATH}/tgi-gaudi-service.log
        n=$((n+1))
        if grep -q Connected ${LOG_PATH}/tgi-gaudi-service.log; then
            break
        fi
        sleep 5s
    done
    sleep 5s
    echo "Service started successfully"
}

function start_react_langchain_agent_service() {
    echo "Starting react_langchain agent microservice"
    docker run -d --runtime=runc --name="test-comps-agent-endpoint" -v $WORKPATH/comps/agent/langchain/tools:/home/user/comps/agent/langchain/tools -p 5042:9090 --ipc=host -e HUGGINGFACEHUB_API_TOKEN=${HUGGINGFACEHUB_API_TOKEN} -e model=${model} -e strategy=react_langchain -e llm_endpoint_url=http://${ip_address}:${tgi_port} -e llm_engine=tgi -e recursion_limit=10 -e require_human_feedback=false -e tools=/home/user/comps/agent/langchain/tools/custom_tools.yaml opea/agent-langchain:comps
    sleep 5s

    docker logs test-comps-agent-endpoint
    echo "Service started successfully"
}


function start_react_langgraph_agent_service() {
    echo "Starting react_langgraph agent microservice"
    docker run -d --runtime=runc --name="test-comps-agent-endpoint" -v $WORKPATH/comps/agent/langchain/tools:/home/user/comps/agent/langchain/tools -p 5042:9090 --ipc=host -e HUGGINGFACEHUB_API_TOKEN=${HUGGINGFACEHUB_API_TOKEN} -e model=${model} -e strategy=react_langgraph -e llm_endpoint_url=http://${ip_address}:${tgi_port} -e llm_engine=tgi -e recursion_limit=10 -e require_human_feedback=false -e tools=/home/user/comps/agent/langchain/tools/custom_tools.yaml opea/agent-langchain:comps
    sleep 5s
    docker logs test-comps-agent-endpoint
    echo "Service started successfully"
}

function start_react_langgraph_agent_service_openai() {
    echo "Starting react_langgraph agent microservice"
    docker run -d --runtime=runc --name="test-comps-agent-endpoint" -v $WORKPATH/comps/agent/langchain/tools:/home/user/comps/agent/langchain/tools -p 5042:9090 --ipc=host -e model=gpt-4o-mini-2024-07-18 -e strategy=react_langgraph -e llm_engine=openai -e OPENAI_API_KEY=${OPENAI_API_KEY} -e recursion_limit=10 -e require_human_feedback=false -e tools=/home/user/comps/agent/langchain/tools/custom_tools.yaml opea/agent-langchain:comps
    sleep 5s
    docker logs test-comps-agent-endpoint
    echo "Service started successfully"
}


function start_ragagent_agent_service() {
    echo "Starting rag agent microservice"
    docker run -d --runtime=runc --name="test-comps-agent-endpoint" -v $WORKPATH/comps/agent/langchain/tools:/home/user/comps/agent/langchain/tools -p 5042:9090 --ipc=host -e HUGGINGFACEHUB_API_TOKEN=${HUGGINGFACEHUB_API_TOKEN} -e model=${model} -e strategy=rag_agent -e llm_endpoint_url=http://${ip_address}:${tgi_port} -e llm_engine=tgi -e recursion_limit=10 -e require_human_feedback=false -e tools=/home/user/comps/agent/langchain/tools/custom_tools.yaml opea/agent-langchain:comps
    sleep 5s
    docker logs test-comps-agent-endpoint
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
    echo "Testing agent service - chat completion API"
    local CONTENT=$(http_proxy="" curl http://${ip_address}:5042/v1/chat/completions -X POST -H "Content-Type: application/json" -d '{
     "query": "What is Intel OPEA project?"
    }')
    local EXIT_CODE=$(validate "$CONTENT" "OPEA" "test-agent-langchain")
    echo "$EXIT_CODE"
    local EXIT_CODE="${EXIT_CODE:0-1}"
    echo "return value is $EXIT_CODE"
    if [ "$EXIT_CODE" == "1" ]; then
        docker logs test-comps-tgi-gaudi-service &> ${LOG_PATH}/test-comps-tgi-gaudi-service.log
        docker logs test-comps-agent-endpoint &> ${LOG_PATH}/test-comps-langchain-agent-endpoint.log
        exit 1
    fi
}

function validate_assistant_api() {
    cd $WORKPATH
    echo "Testing agent service - assistant api"
    local CONTENT=$(python3 comps/agent/langchain/test_assistant_api.py --ip_addr ${ip_address} --ext_port 5042 --assistants_api_test --query 'What is Intel OPEA project?' 2>&1 | tee ${LOG_PATH}/test-agent-langchain-assistantsapi.log)
    local EXIT_CODE=$(validate "$CONTENT" "OPEA" "test-agent-langchain-assistantsapi")
    echo "$EXIT_CODE"
    local EXIT_CODE="${EXIT_CODE:0-1}"
    echo "return value is $EXIT_CODE"
    if [ "$EXIT_CODE" == "1" ]; then
        docker logs comps-tgi-gaudi-service &> ${LOG_PATH}/test-comps-tgi-gaudi-service.log
        docker logs comps-langchain-agent-endpoint &> ${LOG_PATH}/test-comps-langchain-agent-endpoint.log
        exit 1
    fi
}

function stop_tgi_docker() {
    cid=$(docker ps -aq --filter "name=test-comps-tgi-gaudi-service")
    echo "Stopping the docker containers "${cid}
    if [[ ! -z "$cid" ]]; then docker rm $cid -f && sleep 1s; fi
    echo "Docker containers stopped successfully"
}

function stop_agent_docker() {
    cid=$(docker ps -aq --filter "name=test-comps-agent-endpoint")
    echo "Stopping the docker containers "${cid}
    if [[ ! -z "$cid" ]]; then docker rm $cid -f && sleep 1s; fi
    echo "Docker containers stopped successfully"
}

function stop_docker() {
    stop_tgi_docker
    stop_agent_docker
}

function main() {

    stop_docker
    build_docker_images

    start_tgi_service

    # test rag agent
    start_ragagent_agent_service
    echo "=============Testing RAG Agent============="
    validate_microservice
    stop_agent_docker
    echo "============================================="

    # test react_langchain
    start_react_langchain_agent_service
    echo "=============Testing ReAct Langchain============="
    validate_microservice
    validate_assistant_api
    stop_agent_docker
    echo "============================================="

    # # test react_langgraph
    ## For now need OpenAI llms for react_langgraph
    # start_react_langgraph_agent_service_openai
    # echo "===========Testing ReAct Langgraph (OpenAI LLM)============="
    # validate_microservice
    # stop_agent_docker
    # echo "============================================="

    stop_docker
    echo y | docker system prune 2>&1 > /dev/null
}

main
