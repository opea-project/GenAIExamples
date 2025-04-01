#!/bin/bash
# Copyright (C) 2024 Intel Corporation
# SPDX-License-Identifier: Apache-2.0
set -xe

WORKPATH=$(dirname "$PWD")
export WORKDIR=$WORKPATH/../../
echo "WORKDIR=${WORKDIR}"
export ip_address=$(hostname -I | awk '{print $1}')
export HUGGINGFACEHUB_API_TOKEN=${HUGGINGFACEHUB_API_TOKEN}
export TOOLSET_PATH=$WORKDIR/GenAIExamples/AgentQnA/tools/
export no_proxy="$no_proxy,rag-agent-endpoint,sql-agent-endpoint,react-agent-endpoint,agent-ui,vllm-gaudi-server,jaeger,grafana,prometheus,127.0.0.1,localhost,0.0.0.0,$ip_address"


function get_genai_comps() {
    if [ ! -d "GenAIComps" ] ; then
        git clone --depth 1 --branch ${opea_branch:-"main"} https://github.com/opea-project/GenAIComps.git
    fi
}


function build_agent_docker_image() {
    cd $WORKDIR/GenAIExamples/AgentQnA/docker_image_build/
    get_genai_comps
    echo "Build agent image with --no-cache..."
    docker compose -f build.yaml build --no-cache
}

function stop_crag() {
    cid=$(docker ps -aq --filter "name=kdd-cup-24-crag-service")
    echo "Stopping container kdd-cup-24-crag-service with cid $cid"
    if [[ ! -z "$cid" ]]; then docker rm $cid -f && sleep 1s; fi
}

function stop_agent_docker() {
    cd $WORKPATH/docker_compose/intel/hpu/gaudi/
    docker compose -f $WORKDIR/GenAIExamples/DocIndexRetriever/docker_compose/intel/cpu/xeon/compose.yaml -f compose.yaml down
}

function stop_llm(){
    cd $WORKPATH/docker_compose/intel/hpu/gaudi/
    container_list=$(cat tgi_gaudi.yaml | grep container_name | cut -d':' -f2)
    for container_name in $container_list; do
        cid=$(docker ps -aq --filter "name=$container_name")
        echo "Stopping container $container_name"
        if [[ ! -z "$cid" ]]; then docker rm $cid -f && sleep 1s; fi
    done

    cid=$(docker ps -aq --filter "name=vllm-gaudi-server")
    echo "Stopping container $cid"
    if [[ ! -z "$cid" ]]; then docker rm $cid -f && sleep 1s; fi

    cid=$(docker ps -aq --filter "name=test-comps-vllm-gaudi-service")
    echo "Stopping container $cid"
    if [[ ! -z "$cid" ]]; then docker rm $cid -f && sleep 1s; fi

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
echo "workpath: $WORKPATH"
echo "=================== Stop containers ===================="
stop_crag
stop_agent_docker

cd $WORKPATH/tests

echo "=================== #1 Building docker images===================="
build_agent_docker_image
echo "=================== #1 Building docker images completed===================="

echo "=================== #4 Start agent, API server, retrieval, and ingest data===================="
bash $WORKPATH/tests/step4_launch_and_validate_agent_gaudi.sh
echo "=================== #4 Agent, retrieval test passed ===================="

echo "=================== #5 Stop agent and API server===================="
stop_crag
stop_agent_docker
echo "=================== #5 Agent and API server stopped===================="

echo y | docker system prune

echo "ALL DONE!!"
