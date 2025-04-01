#!/bin/bash
# Copyright (C) 2024 Intel Corporation
# SPDX-License-Identifier: Apache-2.0

set -e

WORKPATH=$(dirname "$PWD")
export LOG_PATH=${WORKPATH}
export WORKDIR=$WORKPATH/../../
echo "WORKDIR=${WORKDIR}"
export ip_address=$(hostname -I | awk '{print $1}')
export host_ip=${ip_address}
export TOOLSET_PATH=$WORKPATH/tools/

export HF_CACHE_DIR=$WORKPATH/data2/huggingface
if [ ! -d "$HF_CACHE_DIR" ]; then
    HF_CACHE_DIR=$WORKDIR/hf_cache
    mkdir -p "$HF_CACHE_DIR"
fi

function download_chinook_data(){
    echo "Downloading chinook data..."
    cd $WORKDIR
    git clone https://github.com/lerocha/chinook-database.git
    cp chinook-database/ChinookDatabase/DataSources/Chinook_Sqlite.sqlite ${WORKPATH}/tests/
}

function start_agent_and_api_server() {
    echo "Starting Agent services"
    cd $WORKDIR/GenAIExamples/AgentQnA/docker_compose/amd/gpu/rocm
    bash launch_agent_service_vllm_rocm.sh
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
    export agent_port=$(cat ${WORKPATH}/docker_compose/amd/gpu/WORKER_RAG_AGENT_PORT_tmp)
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

     # test worker sql agent
    echo "======================Testing worker sql agent======================"
    export agent_port=$(cat ${WORKPATH}/docker_compose/amd/gpu/WORKER_SQL_AGENT_PORT_tmp)
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
    export agent_port=$(cat ${WORKPATH}/docker_compose/amd/gpu/SUPERVISOR_REACT_AGENT_PORT_tmp)
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
