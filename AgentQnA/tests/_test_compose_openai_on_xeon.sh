#!/bin/bash
# Copyright (C) 2024 Intel Corporation
# SPDX-License-Identifier: Apache-2.0

set -e

echo "OPENAI_API_KEY=${OPENAI_API_KEY}"
WORKPATH=$(dirname "$PWD")
export WORKDIR=$WORKPATH/../../
echo "WORKDIR=${WORKDIR}"
export ip_address=$(hostname -I | awk '{print $1}')
export TOOLSET_PATH=$WORKDIR/GenAIExamples/AgentQnA/tools/

function stop_agent_and_api_server() {
    echo "Stopping CRAG server"
    docker stop $(docker ps -q --filter ancestor=docker.io/aicrowd/kdd-cup-24-crag-mock-api:v0)
    echo "Stopping Agent services"
    docker stop $(docker ps -q --filter ancestor=opea/agent:latest)
}

function stop_retrieval_tool() {
    echo "Stopping Retrieval tool"
    local RETRIEVAL_TOOL_PATH=$WORKPATH/../DocIndexRetriever
    cd $RETRIEVAL_TOOL_PATH/docker_compose/intel/cpu/xeon/
    container_list=$(cat compose.yaml | grep container_name | cut -d':' -f2)
    for container_name in $container_list; do
        cid=$(docker ps -aq --filter "name=$container_name")
        echo "Stopping container $container_name"
        if [[ ! -z "$cid" ]]; then docker rm $cid -f && sleep 1s; fi
    done
}

echo "=================== #1 Building docker images===================="
bash step1_build_images.sh xeon
echo "=================== #1 Building docker images completed===================="

echo "=================== #2 Start retrieval tool===================="
bash step2_start_retrieval_tool.sh
echo "=================== #2 Retrieval tool started===================="

echo "=================== #3 Ingest data and validate retrieval===================="
bash step3_ingest_data_and_validate_retrieval.sh
echo "=================== #3 Data ingestion and validation completed===================="

echo "=================== #4 Start agent and API server===================="
bash step4_launch_and_validate_agent_openai.sh
echo "=================== #4 Agent test passed ===================="

echo "=================== #5 Stop agent and API server===================="
stop_agent_and_api_server
echo "=================== #5 Agent and API server stopped===================="

echo "=================== #6 Stop retrieval tool===================="
stop_retrieval_tool
echo "=================== #6 Retrieval tool stopped===================="

echo "ALL DONE!"
