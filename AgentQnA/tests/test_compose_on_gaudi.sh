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
IMAGE_REPO=${IMAGE_REPO:-"opea"}
IMAGE_TAG=${IMAGE_TAG:-"latest"}
echo "REGISTRY=IMAGE_REPO=${IMAGE_REPO}"
echo "TAG=IMAGE_TAG=${IMAGE_TAG}"
export REGISTRY=${IMAGE_REPO}
export TAG=${IMAGE_TAG}
export MODEL_CACHE=${model_cache:-"./data"}


function stop_crag() {
    cid=$(docker ps -aq --filter "name=kdd-cup-24-crag-service")
    echo "Stopping container kdd-cup-24-crag-service with cid $cid"
    if [[ ! -z "$cid" ]]; then docker rm $cid -f && sleep 1s; fi
}

function stop_agent_containers() {
    cd $WORKPATH/docker_compose/intel/hpu/gaudi/
    container_list=$(cat compose.yaml | grep container_name | cut -d':' -f2)
    for container_name in $container_list; do
        cid=$(docker ps -aq --filter "name=$container_name")
        echo "Stopping container $container_name"
        if [[ ! -z "$cid" ]]; then docker rm $cid -f && sleep 1s; fi
    done
}

function stop_telemetry_containers(){
    cd $WORKPATH/docker_compose/intel/hpu/gaudi/
    container_list=$(cat compose.telemetry.yaml | grep container_name | cut -d':' -f2)
    for container_name in $container_list; do
        cid=$(docker ps -aq --filter "name=$container_name")
        echo "Stopping container $container_name"
        if [[ ! -z "$cid" ]]; then docker rm $cid -f && sleep 1s; fi
    done
    container_list=$(cat compose.telemetry.yaml | grep container_name | cut -d':' -f2)

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
echo "::group::=================== Stop containers ===================="
stop_llm
stop_crag
stop_agent_containers
stop_retrieval_tool
stop_telemetry_containers
echo "::endgroup::"

cd $WORKPATH/tests

echo "::group::=================== Building docker images===================="
bash step1_build_images.sh gaudi_vllm > docker_image_build.log
echo "::endgroup::"

echo "::group::=================== Start agent, API server, retrieval, and ingest data===================="
bash step4_launch_and_validate_agent_gaudi.sh
echo "::endgroup::"

echo "::group::=================== Stop agent and API server===================="
stop_llm
stop_crag
stop_agent_containers
stop_retrieval_tool
stop_telemetry_containers
echo y | docker system prune
echo "::endgroup::"

echo "ALL DONE!!"
