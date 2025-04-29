#!/bin/bash
# Copyright (C) 2024 Intel Corporation
# SPDX-License-Identifier: Apache-2.0
set -xe

export WORKPATH=$(dirname "$PWD")
export WORKDIR=$WORKPATH/../../
echo "WORKDIR=${WORKDIR}"
export ip_address=$(hostname -I | awk '{print $1}')
LOG_PATH=$WORKPATH

#### env vars for LLM endpoint #############
model=meta-llama/Llama-3.3-70B-Instruct
vllm_image=opea/vllm-rocm:latest
vllm_port=8086
vllm_image=$vllm_image
HF_CACHE_DIR=${model_cache:-"/data2/huggingface"}
vllm_volume=${HF_CACHE_DIR}
#######################################

#### env vars for dataprep #############
export host_ip=${ip_address}
export DATAPREP_PORT="6007"
export TEI_EMBEDDER_PORT="10221"
export REDIS_URL_VECTOR="redis://${ip_address}:6379"
export REDIS_URL_KV="redis://${ip_address}:6380"
export LLM_MODEL=$model
export LLM_ENDPOINT="http://${ip_address}:${vllm_port}"
export DATAPREP_COMPONENT_NAME="OPEA_DATAPREP_REDIS_FINANCE"
export EMBEDDING_MODEL_ID="BAAI/bge-base-en-v1.5"
export TEI_EMBEDDING_ENDPOINT="http://${ip_address}:${TEI_EMBEDDER_PORT}"
#######################################



function get_genai_comps() {
    if [ ! -d "GenAIComps" ] ; then
        git clone --depth 1 --branch ${opea_branch:-"main"} https://github.com/opea-project/GenAIComps.git
    fi
}

function build_dataprep_agent_and_vllm_images() {
    cd $WORKDIR/GenAIExamples/FinanceAgent/docker_image_build/
    get_genai_comps
    echo "Build agent image with --no-cache..."
    docker compose -f build.yaml build --no-cache
}

function build_agent_image_local(){
    cd $WORKDIR/GenAIComps/
    docker build -t opea/agent:latest -f comps/agent/src/Dockerfile . --build-arg https_proxy=$https_proxy --build-arg http_proxy=$http_proxy
}

function start_vllm_service {
    echo "start vllm gaudi service"
    docker compose -f $WORKPATH/docker_compose/amd/gpu/rocm/compose_vllm.yaml up -d
    sleep 1m
    echo "Waiting vllm rocm ready"
    n=0
    until [[ "$n" -ge 500 ]]; do
        docker logs vllm-service >& "${LOG_PATH}"/vllm-service_start.log
        if grep -q "Application startup complete" "${LOG_PATH}"/vllm-service_start.log; then
            break
        fi
        sleep 10s
        n=$((n+1))
    done
    sleep 10s
    echo "Service started successfully"
}


function stop_llm(){
    cid=$(docker ps -aq --filter "name=vllm-service")
    echo "Stopping container $cid"
    if [[ ! -z "$cid" ]]; then docker rm $cid -f && sleep 1s; fi

}

function start_dataprep(){
    docker compose -f $WORKPATH/docker_compose/amd/gpu/rocm/dataprep_compose.yaml up -d
    sleep 1m
}

function validate() {
    local CONTENT="$1"
    local EXPECTED_RESULT="$2"
    local SERVICE_NAME="$3"
    echo "EXPECTED_RESULT: $EXPECTED_RESULT"
    echo "Content: $CONTENT"
    if echo "$CONTENT" | grep -q "$EXPECTED_RESULT"; then
        echo "[ $SERVICE_NAME ] Content is as expected: $CONTENT"
        echo 0
    else
        echo "[ $SERVICE_NAME ] Content does not match the expected result: $CONTENT"
        echo 1
    fi
}

function ingest_validate_dataprep() {
    # test /v1/dataprep/ingest
    echo "=========== Test ingest ==========="
    local CONTENT=$(python3 $WORKPATH/tests/test_redis_finance.py --port $DATAPREP_PORT --test_option ingest)
    local EXIT_CODE=$(validate "$CONTENT" "200" "dataprep-redis-finance")
    echo "$EXIT_CODE"
    local EXIT_CODE="${EXIT_CODE:0-1}"
    if [ "$EXIT_CODE" == "1" ]; then
        docker logs dataprep-redis-server-finance
        exit 1
    fi

    # test /v1/dataprep/get
    echo "=========== Test get ==========="
    local CONTENT=$(python $WORKPATH/tests/test_redis_finance.py --port $DATAPREP_PORT --test_option get)
    local EXIT_CODE=$(validate "$CONTENT" "Request successful" "dataprep-redis-finance")
    echo "$EXIT_CODE"
    local EXIT_CODE="${EXIT_CODE:0-1}"
    if [ "$EXIT_CODE" == "1" ]; then
        docker logs dataprep-redis-server-finance
        exit 1
    fi
}

function stop_dataprep() {
    echo "Stopping databases"
    cid=$(docker ps -aq --filter "name=dataprep-redis-server*" --filter "name=redis-*" --filter "name=tei-embedding-*")
    if [[ ! -z "$cid" ]]; then docker stop $cid && docker rm $cid && sleep 1s; fi

}

function start_agents() {
    echo "Starting Agent services"
    cd $WORKDIR/GenAIExamples/FinanceAgent/docker_compose/amd/gpu/rocm/
    bash launch_agents.sh
    sleep 2m
}


function validate_agent_service() {
    # # test worker finqa agent
    echo "======================Testing worker finqa agent======================"
    export agent_port="9095"
    prompt="What is Gap's revenue in 2024?"
    local CONTENT=$(python3 $WORKDIR/GenAIExamples/FinanceAgent/tests/test.py --prompt "$prompt" --agent_role "worker" --ext_port $agent_port)
    echo $CONTENT
    local EXIT_CODE=$(validate "$CONTENT" "15" "finqa-agent-endpoint")
    echo $EXIT_CODE
    local EXIT_CODE="${EXIT_CODE:0-1}"
    if [ "$EXIT_CODE" == "1" ]; then
        docker logs finqa-agent-endpoint
        exit 1
    fi

    # # test worker research agent
    echo "======================Testing worker research agent======================"
    export agent_port="9096"
    prompt="Johnson & Johnson"
    local CONTENT=$(python3 $WORKDIR/GenAIExamples/AgentQnA/tests/test.py --prompt "$prompt" --agent_role "worker" --ext_port $agent_port --tool_choice "get_current_date" --tool_choice "get_share_performance")
    local EXIT_CODE=$(validate "$CONTENT" "Johnson" "research-agent-endpoint")
    echo $CONTENT
    echo $EXIT_CODE
    local EXIT_CODE="${EXIT_CODE:0-1}"
    if [ "$EXIT_CODE" == "1" ]; then
	docker logs research-agent-endpoint
	exit 1
    fi

    # test supervisor react agent
    echo "======================Testing supervisor agent: single turns ======================"
    export agent_port="9090"
    local CONTENT=$(python3 $WORKDIR/GenAIExamples/FinanceAgent/tests/test.py --agent_role "supervisor" --ext_port $agent_port --stream)
    echo $CONTENT
    local EXIT_CODE=$(validate "$CONTENT" "test completed with success" "supervisor-agent-endpoint")
    echo $EXIT_CODE
    local EXIT_CODE="${EXIT_CODE:0-1}"
    if [ "$EXIT_CODE" == "1" ]; then
        docker logs supervisor-agent-endpoint
        exit 1
    fi

    # echo "======================Testing supervisor agent: multi turns ======================"
    local CONTENT=$(python3 $WORKDIR/GenAIExamples/FinanceAgent/tests/test.py --agent_role "supervisor" --ext_port $agent_port --multi-turn --stream)
    echo $CONTENT
    local EXIT_CODE=$(validate "$CONTENT" "test completed with success" "supervisor-agent-endpoint")
    echo $EXIT_CODE
    local EXIT_CODE="${EXIT_CODE:0-1}"
    if [ "$EXIT_CODE" == "1" ]; then
        docker logs supervisor-agent-endpoint
        exit 1
    fi

}

function stop_agent_docker() {
    cd $WORKPATH/docker_compose/amd/gpu/rocm/
    container_list=$(cat compose.yaml | grep container_name | cut -d':' -f2)
    for container_name in $container_list; do
        cid=$(docker ps -aq --filter "name=$container_name")
        echo "Stopping container $container_name"
        if [[ ! -z "$cid" ]]; then docker rm $cid -f && sleep 1s; fi
    done
}


echo "workpath: $WORKPATH"
echo "=================== Stop containers ===================="
stop_llm
stop_agent_docker
stop_dataprep

cd $WORKPATH/tests

echo "=================== #1 Building docker images===================="
build_dataprep_agent_and_vllm_images

#### for local test
# build_agent_image_local
# echo "=================== #1 Building docker images completed===================="

echo "=================== #2 Start vllm endpoint===================="
start_vllm_service
echo "=================== #2 vllm endpoint started===================="

echo "=================== #3 Start dataprep and ingest data ===================="
start_dataprep
ingest_validate_dataprep
echo "=================== #3 Data ingestion and validation completed===================="

echo "=================== #4 Start agents ===================="
start_agents
validate_agent_service
echo "=================== #4 Agent test passed ===================="

echo "=================== #5 Stop microservices ===================="
stop_agent_docker
stop_dataprep
stop_llm
echo "=================== #5 Microservices stopped===================="

echo y | docker system prune

echo "ALL DONE!!"
