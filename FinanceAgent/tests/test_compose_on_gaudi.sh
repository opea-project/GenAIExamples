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


function stop_agent_docker() {
    cd $WORKPATH/docker_compose/intel/hpu/gaudi/
    container_list=$(cat compose.yaml | grep container_name | cut -d':' -f2)
    for container_name in $container_list; do
        cid=$(docker ps -aq --filter "name=$container_name")
        echo "Stopping container $container_name"
        if [[ ! -z "$cid" ]]; then docker rm $cid -f && sleep 1s; fi
    done
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

function start_dataprep(){
    docker compose -f $WORKPATH/docker_compose/intel/hpu/gaudi/dataprep.yaml up -d
}

function stop_dataprep() {
    echo "Stopping databases"
    cid=$(docker ps -aq --filter "name=dataprep-redis-server*" --filter "name=redis-*" --filter "name=tei-embedding-*")
    if [[ ! -z "$cid" ]]; then docker stop $cid && docker rm $cid && sleep 1s; fi
    
}


echo "workpath: $WORKPATH"
echo "=================== Stop containers ===================="
stop_llm
stop_agent_docker
stop_databases

cd $WORKPATH/tests

echo "=================== #1 Building docker images===================="
bash step1_build_images.sh
echo "=================== #1 Building docker images completed===================="

echo "=================== #2 Start dataprep===================="
start_dataprep
echo "=================== #2 Dataprep started===================="

echo "=================== #3 Ingest data and validate retrieval===================="
bash step3_ingest_data_and_validate_retrieval.sh
echo "=================== #3 Data ingestion and validation completed===================="

echo "=================== #4 Start agents ===================="
bash step4_launch_and_validate_agent_gaudi.sh
echo "=================== #4 Agent test passed ===================="

echo "=================== #5 Stop microservices ===================="
stop_agent_docker
stop_dataprep
stop_llm
echo "=================== #5 Microservices stopped===================="

echo y | docker system prune

echo "ALL DONE!!"
