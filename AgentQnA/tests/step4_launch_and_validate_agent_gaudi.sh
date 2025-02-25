#!/bin/bash
# Copyright (C) 2024 Intel Corporation
# SPDX-License-Identifier: Apache-2.0

set -e

WORKPATH=$(dirname "$PWD")
export WORKDIR=$WORKPATH/../../
echo "WORKDIR=${WORKDIR}"
export ip_address=$(hostname -I | awk '{print $1}')
export TOOLSET_PATH=$WORKPATH/tools/
export HUGGINGFACEHUB_API_TOKEN=${HUGGINGFACEHUB_API_TOKEN}
HF_TOKEN=${HUGGINGFACEHUB_API_TOKEN}
model="meta-llama/Llama-3.3-70B-Instruct" #"meta-llama/Meta-Llama-3.1-70B-Instruct"

export HF_CACHE_DIR=/data2/huggingface
if [ ! -d "$HF_CACHE_DIR" ]; then
    HF_CACHE_DIR=$WORKDIR/hf_cache
    mkdir -p "$HF_CACHE_DIR"
fi
echo  "HF_CACHE_DIR=$HF_CACHE_DIR"
ls $HF_CACHE_DIR

vllm_port=8086
vllm_volume=${HF_CACHE_DIR}

function start_tgi(){
    echo "Starting tgi-gaudi server"
    cd $WORKDIR/GenAIExamples/AgentQnA/docker_compose/intel/hpu/gaudi
    bash launch_tgi_gaudi.sh

}

function start_vllm_service_70B() {

    echo "token is ${HF_TOKEN}"

    echo "start vllm gaudi service"
    echo "**************model is $model**************"
    vllm_image=opea/vllm-gaudi:ci
    docker run -d --runtime=habana --rm --name "vllm-gaudi-server" -e HABANA_VISIBLE_DEVICES=0,1,2,3 -p $vllm_port:8000 -v $vllm_volume:/data -e HF_TOKEN=$HF_TOKEN -e HUGGING_FACE_HUB_TOKEN=$HF_TOKEN -e HF_HOME=/data -e OMPI_MCA_btl_vader_single_copy_mechanism=none -e PT_HPU_ENABLE_LAZY_COLLECTIVES=true -e http_proxy=$http_proxy -e https_proxy=$https_proxy -e no_proxy=$no_proxy -e VLLM_SKIP_WARMUP=true --cap-add=sys_nice --ipc=host $vllm_image --model ${model} --max-seq-len-to-capture 16384 --tensor-parallel-size 4
    sleep 5s
    echo "Waiting vllm gaudi ready"
    n=0
    LOG_PATH=$PWD
    until [[ "$n" -ge 100 ]] || [[ $ready == true ]]; do
        docker logs vllm-gaudi-server
        docker logs vllm-gaudi-server &> ${LOG_PATH}/vllm-gaudi-service.log
        n=$((n+1))
        if grep -q "Uvicorn running on" ${LOG_PATH}/vllm-gaudi-service.log; then
            break
        fi
        if grep -q "No such container" ${LOG_PATH}/vllm-gaudi-service.log; then
            echo "container vllm-gaudi-server not found"
            exit 1
        fi
        sleep 5s
    done
    sleep 5s
    echo "Service started successfully"
}

function download_chinook_data(){
    echo "Downloading chinook data..."
    cd $WORKDIR
    git clone https://github.com/lerocha/chinook-database.git
    cp chinook-database/ChinookDatabase/DataSources/Chinook_Sqlite.sqlite $WORKDIR/GenAIExamples/AgentQnA/tests/
}

function start_agent_and_api_server() {
    echo "Starting CRAG server"
    docker run -d --runtime=runc --name=kdd-cup-24-crag-service -p=8080:8000 docker.io/aicrowd/kdd-cup-24-crag-mock-api:v0

    echo "Starting Agent services"
    cd $WORKDIR/GenAIExamples/AgentQnA/docker_compose/intel/hpu/gaudi
    bash launch_agent_service_gaudi.sh
    sleep 2m
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

function validate_agent_service() {
    # # test worker rag agent
    echo "======================Testing worker rag agent======================"
    export agent_port="9095"
    prompt="Tell me about Michael Jackson song Thriller"
    local CONTENT=$(python3 $WORKDIR/GenAIExamples/AgentQnA/tests/test.py --prompt "$prompt" --agent_role "worker" --ext_port $agent_port)
    # echo $CONTENT
    local EXIT_CODE=$(validate "$CONTENT" "Thriller" "rag-agent-endpoint")
    echo $EXIT_CODE
    local EXIT_CODE="${EXIT_CODE:0-1}"
    if [ "$EXIT_CODE" == "1" ]; then
        docker logs rag-agent-endpoint
        exit 1
    fi

    # # test worker sql agent
    echo "======================Testing worker sql agent======================"
    export agent_port="9096"
    prompt="How many employees are there in the company?"
    local CONTENT=$(python3 $WORKDIR/GenAIExamples/AgentQnA/tests/test.py --prompt "$prompt" --agent_role "worker" --ext_port $agent_port)
    local EXIT_CODE=$(validate "$CONTENT" "8" "sql-agent-endpoint")
    echo $CONTENT
    # echo $EXIT_CODE
    local EXIT_CODE="${EXIT_CODE:0-1}"
    if [ "$EXIT_CODE" == "1" ]; then
        docker logs sql-agent-endpoint
        exit 1
    fi

    # test supervisor react agent
    echo "======================Testing supervisor react agent======================"
    export agent_port="9090"
    local CONTENT=$(python3 $WORKDIR/GenAIExamples/AgentQnA/tests/test.py --agent_role "supervisor" --ext_port $agent_port --stream)
    local EXIT_CODE=$(validate "$CONTENT" "Iron" "react-agent-endpoint")
    # echo $CONTENT
    echo $EXIT_CODE
    local EXIT_CODE="${EXIT_CODE:0-1}"
    if [ "$EXIT_CODE" == "1" ]; then
        docker logs react-agent-endpoint
        exit 1
    fi

}

function remove_chinook_data(){
    echo "Removing chinook data..."
    cd $WORKDIR
    if [ -d "chinook-database" ]; then
        rm -rf chinook-database
    fi
    echo "Chinook data removed!"
}

function main() {
    echo "==================== Prepare data ===================="
    download_chinook_data
    echo "==================== Data prepare done ===================="

    echo "==================== Start VLLM service ===================="
    start_vllm_service_70B
    echo "==================== VLLM service started ===================="

    echo "==================== Start agent ===================="
    start_agent_and_api_server
    echo "==================== Agent started ===================="

    echo "==================== Validate agent service ===================="
    validate_agent_service
    echo "==================== Agent service validated ===================="
}


remove_chinook_data

main

remove_chinook_data
