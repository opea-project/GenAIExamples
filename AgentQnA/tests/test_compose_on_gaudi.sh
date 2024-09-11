#!/bin/bash
# Copyright (C) 2024 Intel Corporation
# SPDX-License-Identifier: Apache-2.0

set -e

WORKPATH=$(dirname "$PWD")
export WORKDIR=$WORKPATH/../../
echo "WORKDIR=${WORKDIR}"
export ip_address=$(hostname -I | awk '{print $1}')
export HUGGINGFACEHUB_API_TOKEN=${HUGGINGFACEHUB_API_TOKEN}
export TOOLSET_PATH=$WORKDIR/GenAIExamples/AgentQnA/tools/

function stop_crag() {
    cid=$(docker ps -aq --filter "name=kdd-cup-24-crag-service")
    echo "Stopping container kdd-cup-24-crag-service with cid $cid"
    if [[ ! -z "$cid" ]]; then docker rm $cid -f && sleep 1s; fi
}

function stop_agent_docker() {
    cd $WORKPATH/docker_compose/intel/hpu/gaudi/
    # docker compose -f compose.yaml down
    container_list=$(cat compose.yaml | grep container_name | cut -d':' -f2)
    for container_name in $container_list; do
        cid=$(docker ps -aq --filter "name=$container_name")
        echo "Stopping container $container_name"
        if [[ ! -z "$cid" ]]; then docker rm $cid -f && sleep 1s; fi
    done
}

function stop_retrieval_tool() {
    echo "Stopping Retrieval tool"
    local RETRIEVAL_TOOL_PATH=$WORKPATH/../DocIndexRetriever
    cd $RETRIEVAL_TOOL_PATH/docker_compose/intel/cpu/xeon/
    # docker compose -f compose.yaml down
    container_list=$(cat compose.yaml | grep container_name | cut -d':' -f2)
    for container_name in $container_list; do
        cid=$(docker ps -aq --filter "name=$container_name")
        echo "Stopping container $container_name"
        if [[ ! -z "$cid" ]]; then docker rm $cid -f && sleep 1s; fi
    done
}
echo "workpath: $WORKPATH"
echo "=================== Stop containers ===================="
stop_crag
stop_agent_docker
stop_retrieval_tool

cd $WORKPATH/tests

echo "=================== #1 Building docker images===================="
bash 1_build_images.sh
echo "=================== #1 Building docker images completed===================="

echo "=================== #2 Start retrieval tool===================="
bash 2_start_retrieval_tool.sh
echo "=================== #2 Retrieval tool started===================="

echo "=================== #3 Ingest data and validate retrieval===================="
bash 3_ingest_data_and_validate_retrieval.sh
echo "=================== #3 Data ingestion and validation completed===================="

echo "=================== #4 Start agent and API server===================="
bash 4_launch_and_validate_agent_tgi.sh
echo "=================== #4 Agent test passed ===================="

echo "=================== #5 Stop agent and API server===================="
stop_crag
stop_agent_docker
stop_retrieval_tool
echo "=================== #5 Agent and API server stopped===================="

echo "ALL DONE!"
