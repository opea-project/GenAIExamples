#!/bin/bash
# Copyright (C) 2024 Intel Corporation
# SPDX-License-Identifier: Apache-2.0

#set -xe

WORKPATH=$(dirname "$PWD")
echo $WORKPATH
LOG_PATH="$WORKPATH/tests"
ip_address=$(hostname -I | awk '{print $1}')
tgi_port=8085
tgi_volume=$WORKPATH/data
vllm_port=8086
vllm_volume=$WORKPATH/data

export WORKPATH=$WORKPATH

export agent_image="opea/agent-langchain:comps"
export agent_container_name="test-comps-agent-endpoint"

export model=meta-llama/Meta-Llama-3.1-70B-Instruct
export HUGGINGFACEHUB_API_TOKEN=${HF_TOKEN}
export ip_address=$(hostname -I | awk '{print $1}')
export HUGGINGFACEHUB_API_TOKEN=${HUGGINGFACEHUB_API_TOKEN}
export LLM_MODEL_ID="meta-llama/Meta-Llama-3.1-70B-Instruct"
export LLM_ENDPOINT_URL="http://${ip_address}:${tgi_port}"
export temperature=0.01
export max_new_tokens=4096
export TOOLSET_PATH=$WORKPATH/comps/agent/langchain/tools/
echo "TOOLSET_PATH=${TOOLSET_PATH}"
export recursion_limit=15

function build_docker_images() {
    echo "Building the docker images"
    cd $WORKPATH
    echo $WORKPATH
    docker build --no-cache -t $agent_image --build-arg http_proxy=$http_proxy --build-arg https_proxy=$https_proxy -f comps/agent/langchain/Dockerfile .
    if [ $? -ne 0 ]; then
        echo "opea/agent-langchain built fail"
        exit 1
    else
        echo "opea/agent-langchain built successful"
    fi
}

function build_vllm_docker_images() {
    echo "Building the vllm docker images"
    cd $WORKPATH
    echo $WORKPATH
    if [ ! -d "./vllm" ]; then
        git clone https://github.com/HabanaAI/vllm-fork.git
    fi
    cd ./vllm-fork
    docker build -f Dockerfile.hpu -t opea/vllm-gaudi:comps --shm-size=128g . --build-arg https_proxy=$https_proxy --build-arg http_proxy=$http_proxy
    if [ $? -ne 0 ]; then
        echo "opea/vllm-gaudi:comps failed"
        exit 1
    else
        echo "opea/vllm-gaudi:comps successful"
    fi
}

function start_tgi_service() {
    echo "token is ${HF_TOKEN}"

    #multi cards
    echo "start tgi gaudi service"
    docker run -d --runtime=habana --name "test-comps-tgi-gaudi-service" -p $tgi_port:80 -v $tgi_volume:/data -e HF_TOKEN=$HF_TOKEN -e HABANA_VISIBLE_DEVICES=0,1,2,3 -e OMPI_MCA_btl_vader_single_copy_mechanism=none -e PT_HPU_ENABLE_LAZY_COLLECTIVES=true -e http_proxy=$http_proxy -e https_proxy=$https_proxy --cap-add=sys_nice --ipc=host ghcr.io/huggingface/tgi-gaudi:2.0.5 --model-id $model --max-input-tokens 4096 --max-total-tokens 8192 --sharded true --num-shard 4
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

function start_vllm_service() {
    # redis endpoint
    echo "token is ${HF_TOKEN}"

    #single card
    echo "start vllm gaudi service"
    echo "**************model is $model**************"
    docker run -d --runtime=habana --rm --name "test-comps-vllm-gaudi-service" -e HABANA_VISIBLE_DEVICES=all -p $vllm_port:80 -v $vllm_volume:/data -e HF_TOKEN=$HF_TOKEN -e HF_HOME=/data -e OMPI_MCA_btl_vader_single_copy_mechanism=none -e PT_HPU_ENABLE_LAZY_COLLECTIVES=true -e http_proxy=$http_proxy -e https_proxy=$https_proxy -e VLLM_SKIP_WARMUP=true --cap-add=sys_nice --ipc=host opea/vllm-gaudi:comps --model ${model} --host 0.0.0.0 --port 80 --block-size 128 --max-num-seqs  4096 --max-seq_len-to-capture 8192
    sleep 5s
    echo "Waiting vllm gaudi ready"
    n=0
    until [[ "$n" -ge 100 ]] || [[ $ready == true ]]; do
        docker logs test-comps-vllm-gaudi-service &> ${LOG_PATH}/vllm-gaudi-service.log
        n=$((n+1))
        if grep -q "Uvicorn running on" ${LOG_PATH}/vllm-gaudi-service.log; then
            break
        fi
        if grep -q "No such container" ${LOG_PATH}/vllm-gaudi-service.log; then
            echo "container test-comps-vllm-gaudi-service not found"
            exit 1
        fi
        sleep 5s
    done
    sleep 5s
    echo "Service started successfully"
}

function start_vllm_auto_tool_choice_service() {
    # redis endpoint
    echo "token is ${HF_TOKEN}"

    #single card
    echo "start vllm gaudi service"
    echo "**************auto_tool model is $model**************"
    docker run -d --runtime=habana --rm --name "test-comps-vllm-gaudi-service" -e HABANA_VISIBLE_DEVICES=all -p $vllm_port:80 -v $vllm_volume:/data -e HF_TOKEN=$HF_TOKEN -e HF_HOME=/data -e OMPI_MCA_btl_vader_single_copy_mechanism=none -e PT_HPU_ENABLE_LAZY_COLLECTIVES=true -e http_proxy=$http_proxy -e https_proxy=$https_proxy -e VLLM_SKIP_WARMUP=true --cap-add=sys_nice --ipc=host opea/vllm-gaudi:comps --model ${model} --host 0.0.0.0 --port 80 --block-size 128 --max-num-seqs  4096 --max-seq_len-to-capture 8192 --enable-auto-tool-choice --tool-call-parser ${model_parser}
    sleep 5s
    echo "Waiting vllm gaudi ready"
    n=0
    until [[ "$n" -ge 100 ]] || [[ $ready == true ]]; do
        docker logs test-comps-vllm-gaudi-service &> ${LOG_PATH}/vllm-gaudi-service.log
        n=$((n+1))
        if grep -q "Uvicorn running on" ${LOG_PATH}/vllm-gaudi-service.log; then
            break
        fi
        if grep -q "No such container" ${LOG_PATH}/vllm-gaudi-service.log; then
            echo "container test-comps-vllm-gaudi-service not found"
            exit 1
        fi
        sleep 5s
    done
    sleep 5s
    echo "Service started successfully"
}

function start_react_langchain_agent_service() {
    echo "Starting react_langchain agent microservice"
    docker compose -f $WORKPATH/tests/agent/react_langchain.yaml up -d
    sleep 5s
    docker logs test-comps-agent-endpoint
    echo "Service started successfully"
}


function start_react_langgraph_agent_service_openai() {
    echo "Starting react_langchain agent microservice"
    docker compose -f $WORKPATH/tests/agent/react_langgraph_openai.yaml up -d
    sleep 5s
    docker logs test-comps-agent-endpoint
    echo "Service started successfully"
}


function start_react_llama_agent_service() {
    echo "Starting react_langgraph agent microservice"
    docker compose -f $WORKPATH/tests/agent/reactllama.yaml up -d
    sleep 5s
    docker logs test-comps-agent-endpoint
    echo "Service started successfully"
}

function start_react_langgraph_agent_service_vllm() {
    echo "Starting react_langgraph agent microservice"
    docker compose -f $WORKPATH/tests/agent/react_vllm.yaml up -d
    sleep 5s
    docker logs test-comps-agent-endpoint
    echo "Service started successfully"
}

function start_planexec_agent_service_vllm() {
    echo "Starting planexec agent microservice"
    docker compose -f $WORKPATH/tests/agent/planexec_vllm.yaml up -d
    sleep 5s
    docker logs test-comps-agent-endpoint
    echo "Service started successfully"
}

function start_ragagent_agent_service() {
    echo "Starting rag agent microservice"
    docker compose -f $WORKPATH/tests/agent/ragagent.yaml up -d
    sleep 5s
    docker logs test-comps-agent-endpoint
    echo "Service started successfully"
}

function start_ragagent_agent_service_openai() {
    echo "Starting rag agent microservice"
    docker compose -f $WORKPATH/tests/agent/ragagent_openai.yaml up -d
    sleep 5s
    docker logs test-comps-agent-endpoint
    echo "Service started successfully"
}

function start_planexec_agent_service_openai() {
    echo "Starting plan execute agent microservice"
    docker compose -f $WORKPATH/tests/agent/planexec_openai.yaml up -d
    sleep 5s
    docker logs test-comps-agent-endpoint
    echo "Service started successfully"
}

function validate() {
    local CONTENT="$1"
    local EXPECTED_RESULT="$2"
    local SERVICE_NAME="$3"
    # local CONTENT_TO_VALIDATE= "$CONTENT" | grep -oP '(?<=text:).*?(?=prompt)'
    echo "Content: $CONTENT"
    # echo "Content to validate: $CONTENT_TO_VALIDATE"

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
    # local CONTENT=$(http_proxy="" curl http://${ip_address}:9095/v1/chat/completions -X POST -H "Content-Type: application/json" -d '{
    #  "query": "What is OPEA?"
    # }')
    CONTENT=$(python3 $WORKPATH/tests/agent/test.py)
    local EXIT_CODE=$(validate "$CONTENT" "OPEA" "test-agent-langchain")
    echo "$EXIT_CODE"
    local EXIT_CODE="${EXIT_CODE:0-1}"
    echo "return value is $EXIT_CODE"
    if [ "$EXIT_CODE" == "1" ]; then
        echo "==================TGI logs ======================"
        docker logs test-comps-tgi-gaudi-service
        echo "==================Agent logs ======================"
        docker logs test-comps-agent-endpoint
        exit 1
    fi
}


function validate_microservice_streaming() {
    echo "Testing agent service - chat completion API"
    CONTENT=$(python3 $WORKPATH/tests/agent/test.py --stream)
    local EXIT_CODE=$(validate "$CONTENT" "OPEA" "test-agent-langchain")
    echo "$EXIT_CODE"
    local EXIT_CODE="${EXIT_CODE:0-1}"
    echo "return value is $EXIT_CODE"
    if [ "$EXIT_CODE" == "1" ]; then
        echo "==================TGI logs ======================"
        docker logs test-comps-tgi-gaudi-service
        echo "==================Agent logs ======================"
        docker logs test-comps-agent-endpoint
        exit 1
    fi
}

function validate_assistant_api() {
    cd $WORKPATH
    echo "Testing agent service - assistant api"
    local CONTENT=$(python3 comps/agent/langchain/test_assistant_api.py --ip_addr ${ip_address} --ext_port 9095 --assistants_api_test --query 'What is Intel OPEA project?' 2>&1 | tee ${LOG_PATH}/test-agent-langchain-assistantsapi.log)
    local EXIT_CODE=$(validate "$CONTENT" "OPEA" "test-agent-langchain-assistantsapi")
    echo "$EXIT_CODE"
    local EXIT_CODE="${EXIT_CODE:0-1}"
    echo "return value is $EXIT_CODE"
    if [ "$EXIT_CODE" == "1" ]; then
        echo "==================TGI logs ======================"
        docker logs comps-tgi-gaudi-service
        echo "==================Agent logs ======================"
        docker logs comps-langchain-agent-endpoint
        exit 1
    fi
}

function stop_tgi_docker() {
    cid=$(docker ps -aq --filter "name=test-comps-tgi-gaudi-service")
    echo "Stopping the docker containers "${cid}
    if [[ ! -z "$cid" ]]; then docker rm $cid -f && sleep 1s; fi
    echo "Docker containers stopped successfully"
}

function stop_vllm_docker() {
    cid=$(docker ps -aq --filter "name=test-comps-vllm-gaudi-service")
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
    stop_vllm_docker
    stop_agent_docker
}

function main() {
    stop_agent_docker
    stop_docker
    build_docker_images

    # ==================== TGI tests ====================
    start_tgi_service

    # test rag agent
    start_ragagent_agent_service
    echo "=============Testing RAG Agent============="
    validate_microservice
    stop_agent_docker
    echo "============================================="

    # test react_llama
    start_react_llama_agent_service
    echo "===========Testing ReAct Llama ============="
    validate_microservice
    stop_agent_docker
    echo "============================================="


    # test react_langchain
    start_react_langchain_agent_service
    echo "=============Testing ReAct Langchain============="
    validate_microservice_streaming
    validate_assistant_api
    stop_agent_docker
    echo "============================================="

    stop_tgi_docker

    # ==================== VLLM tests ====================
    build_vllm_docker_images

    export model=mistralai/Mistral-7B-Instruct-v0.3
    export LLM_MODEL_ID=${model}
    export model_parser=mistral
    export LLM_ENDPOINT_URL="http://${ip_address}:${vllm_port}"

    # test react with vllm - Mistral
    start_vllm_auto_tool_choice_service
    start_react_langgraph_agent_service_vllm
    echo "===========Testing ReAct Langgraph VLLM Mistral ============="
    validate_microservice
    # stop_agent_docker
    # stop_vllm_docker
    echo "============================================="

    # test plan execute with vllm - Mistral
    start_vllm_service
    start_planexec_agent_service_vllm
    echo "===========Testing Plan Execute VLLM Mistral ============="
    validate_microservice
    stop_agent_docker
    stop_vllm_docker
    echo "============================================="

    export model=meta-llama/Llama-3.1-8B-Instruct
    export LLM_MODEL_ID=${model}
    export model_parser=llama3_json

    # test react with vllm - llama3 support has not been synced to vllm-gaudi yet
    # start_vllm_auto_tool_choice_service
    # start_react_langgraph_agent_service_vllm
    # echo "===========Testing ReAct VLLM ============="
    # validate_microservice
    # stop_agent_docker
    # stop_vllm_docker
    # echo "============================================="

    # test plan execute with vllm - llama3.1
    start_vllm_service
    start_planexec_agent_service_vllm
    echo "===========Testing Plan Execute VLLM Llama3.1 ============="
    validate_microservice
    stop_agent_docker
    stop_vllm_docker
    echo "============================================="


    # # ==================== OpenAI tests ====================
    # start_ragagent_agent_service_openai
    # echo "=============Testing RAG Agent OpenAI============="
    # validate_microservice
    # stop_agent_docker
    # echo "============================================="

    # start_react_langgraph_agent_service_openai
    # echo "===========Testing ReAct Langgraph OpenAI ============="
    # validate_microservice
    # stop_agent_docker
    # echo "============================================="

    # start_planexec_agent_service_openai
    # echo "===========Testing Plan Execute OpenAI ============="
    # validate_microservice
    # stop_agent_docker

    stop_docker
    echo y | docker system prune 2>&1 > /dev/null
}

main
