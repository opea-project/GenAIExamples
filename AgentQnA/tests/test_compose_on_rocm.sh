#!/bin/bash
# Copyright (C) 2024 Advanced Micro Devices, Inc.
# SPDX-License-Identifier: Apache-2.0

set -xe

WORKPATH=$(dirname "$PWD")
ls $WORKPATH
export WORKDIR=$WORKPATH/../../
echo "WORKDIR=${WORKDIR}"
export ip_address=$(hostname -I | awk '{print $1}')
export HUGGINGFACEHUB_API_TOKEN=${HUGGINGFACEHUB_API_TOKEN}
export TOOLSET_PATH=$WORKPATH/tools/
export MODEL_CACHE="./data"

function stop_crag() {
    cid=$(docker ps -aq --filter "name=kdd-cup-24-crag-service")
    echo "Stopping container kdd-cup-24-crag-service with cid $cid"
    if [[ ! -z "$cid" ]]; then docker rm $cid -f && sleep 1s; fi
}

function stop_agent_docker() {
    cd $WORKPATH/docker_compose/amd/gpu/rocm
    bash stop_agent_service_tgi_rocm.sh
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
echo "::group::=================== Stop containers ===================="
stop_crag
stop_agent_docker
stop_retrieval_tool
echo "::endgroup::=================== Stop containers completed ===================="

cd $WORKPATH/tests

echo "::group::=================== #1 Building docker images===================="
bash step1_build_images.sh
echo "::endgroup::=================== #1 Building docker images completed===================="

echo "::group::=================== #2 Start retrieval tool===================="
bash step2_start_retrieval_tool.sh
echo "::endgroup::=================== #2 Retrieval tool started===================="

echo "::group::=================== #3 Ingest data and validate retrieval===================="
bash step3_ingest_data_and_validate_retrieval.sh
echo "::endgroup::=================== #3 Data ingestion and validation completed===================="

echo "::group::=================== #4 Start agent and API server===================="
bash step4a_launch_and_validate_agent_tgi_on_rocm.sh
echo "::endgroup::=================== #4 Agent test passed ===================="

echo "::group::=================== #5 Stop agent and API server===================="
stop_crag
stop_agent_docker
stop_retrieval_tool
echo "::endgroup::=================== #5 Agent and API server stopped===================="

echo y | docker system prune

echo "ALL DONE!!"
