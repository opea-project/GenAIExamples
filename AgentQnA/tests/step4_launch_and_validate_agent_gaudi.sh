#!/bin/bash
# Copyright (C) 2024 Intel Corporation
# SPDX-License-Identifier: Apache-2.0

set -e

WORKPATH=$(dirname "$PWD")
export WORKDIR=$WORKPATH/../../
echo "WORKDIR=${WORKDIR}"
export ip_address=$(hostname -I | awk '{print $1}')
export host_ip=$ip_address
echo "ip_address=${ip_address}"
export TOOLSET_PATH=$WORKPATH/tools/
export HF_TOKEN=${HF_TOKEN}
model="meta-llama/Llama-3.3-70B-Instruct" #"meta-llama/Meta-Llama-3.1-70B-Instruct"

export HF_CACHE_DIR=${model_cache:-"/data2/huggingface"}
if [ ! -d "$HF_CACHE_DIR" ]; then
    HF_CACHE_DIR=$WORKDIR/hf_cache
    mkdir -p "$HF_CACHE_DIR"
fi
echo  "HF_CACHE_DIR=$HF_CACHE_DIR"
ls $HF_CACHE_DIR

vllm_port=8086
vllm_volume=${HF_CACHE_DIR}


function start_agent_service() {
    echo "Starting agent service"
    cd $WORKDIR/GenAIExamples/AgentQnA/docker_compose/intel/hpu/gaudi
    source set_env.sh
    docker compose -f compose.yaml up -d
}

function start_all_services() {

    echo "token is ${HF_TOKEN}"

    echo "start vllm gaudi service"
    echo "**************model is $model**************"
    cd $WORKDIR/GenAIExamples/AgentQnA/docker_compose/intel/hpu/gaudi
    source set_env.sh
    docker compose -f $WORKDIR/GenAIExamples/DocIndexRetriever/docker_compose/intel/cpu/xeon/compose.yaml -f compose.yaml -f compose.telemetry.yaml up -d
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
    export agent_ip="127.0.0.1"
    prompt="Tell me about Michael Jackson song Thriller"
    local CONTENT=$(python3 $WORKDIR/GenAIExamples/AgentQnA/tests/test.py --prompt "$prompt" --agent_role "worker" --ip_addr $agent_ip  --ext_port $agent_port)
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
    local CONTENT=$(python3 $WORKDIR/GenAIExamples/AgentQnA/tests/test.py --prompt "$prompt" --agent_role "worker" --ip_addr $agent_ip --ext_port $agent_port)
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
    local CONTENT=$(python3 $WORKDIR/GenAIExamples/AgentQnA/tests/test.py --agent_role "supervisor" --ip_addr $agent_ip  --ext_port $agent_port --stream)
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

function ingest_data_and_validate() {
    echo "Ingesting data"
    cd $WORKDIR/GenAIExamples/AgentQnA/retrieval_tool/
    echo $PWD
    local CONTENT=$(bash run_ingest_data.sh)
    local EXIT_CODE=$(validate "$CONTENT" "Data preparation succeeded" "dataprep-redis-server")
    echo "$EXIT_CODE"
    local EXIT_CODE="${EXIT_CODE:0-1}"
    echo "return value is $EXIT_CODE"
    if [ "$EXIT_CODE" == "1" ]; then
        docker logs dataprep-redis-server
        return 1
    fi
}

function validate_retrieval_tool() {
    echo "----------------Test retrieval tool ----------------"
    local CONTENT=$(http_proxy="" curl http://${ip_address}:8889/v1/retrievaltool -X POST -H "Content-Type: application/json" -d '{
     "text": "Who sang Thriller"
    }')
    local EXIT_CODE=$(validate "$CONTENT" "Thriller" "retrieval-tool")

    if [ "$EXIT_CODE" == "1" ]; then
        docker logs retrievaltool-xeon-backend-server
        exit 1
    fi
}

function main() {
    echo "==================== Prepare data ===================="
    download_chinook_data
    echo "==================== Data prepare done ===================="

    echo "==================== Start all services ===================="
    start_all_services
    echo "==================== all services started ===================="

    echo "==================== Ingest data ===================="
    ingest_data_and_validate
    echo "==================== Data ingestion completed ===================="

    echo "==================== Validate retrieval tool ===================="
    validate_retrieval_tool
    echo "==================== Retrieval tool validated ===================="

    echo "==================== Validate agent service ===================="
    validate_agent_service
    echo "==================== Agent service validated ===================="
}


remove_chinook_data

main

remove_chinook_data
