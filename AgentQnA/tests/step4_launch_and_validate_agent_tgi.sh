#!/bin/bash
# Copyright (C) 2024 Intel Corporation
# SPDX-License-Identifier: Apache-2.0

set -e

WORKPATH=$(dirname "$PWD")
export WORKDIR=$WORKPATH/../../
echo "WORKDIR=${WORKDIR}"
export ip_address=$(hostname -I | awk '{print $1}')
export TOOLSET_PATH=$WORKDIR/GenAIExamples/AgentQnA/tools/
export HUGGINGFACEHUB_API_TOKEN=${HUGGINGFACEHUB_API_TOKEN}
HF_TOKEN=${HUGGINGFACEHUB_API_TOKEN}
model="meta-llama/Meta-Llama-3.1-70B-Instruct"

export HF_CACHE_DIR=$WORKDIR/hf_cache
if [ ! -d "$HF_CACHE_DIR" ]; then
    mkdir -p "$HF_CACHE_DIR"
fi
ls $HF_CACHE_DIR

vllm_port=8085
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
    docker run -d --runtime=habana --rm --name "vllm-gaudi-server" -e HABANA_VISIBLE_DEVICES=0,1,2,3 -p $vllm_port:8000 -v $vllm_volume:/data -e HF_TOKEN=$HF_TOKEN -e HUGGING_FACE_HUB_TOKEN=$HF_TOKEN -e HF_HOME=/data -e OMPI_MCA_btl_vader_single_copy_mechanism=none -e PT_HPU_ENABLE_LAZY_COLLECTIVES=true -e http_proxy=$http_proxy -e https_proxy=$https_proxy -e no_proxy=$no_proxy -e VLLM_SKIP_WARMUP=true --cap-add=sys_nice --ipc=host opea/vllm-gaudi:comps --model ${model} --max-seq-len-to-capture 16384 --tensor-parallel-size 4
    sleep 5s
    echo "Waiting vllm gaudi ready"
    n=0
    until [[ "$n" -ge 100 ]] || [[ $ready == true ]]; do
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


function prepare_data() {
    cd $WORKDIR

    echo "Downloading data..."
    git clone https://github.com/TAG-Research/TAG-Bench.git
    cd TAG-Bench/setup
    chmod +x get_dbs.sh
    ./get_dbs.sh

    echo "Split data..."
    cd $WORKPATH/tests/sql_agent_test
    bash run_data_split.sh

    echo "Data preparation done!"
}

function start_agent_and_api_server() {
    echo "Starting CRAG server"
    docker run -d --runtime=runc --name=kdd-cup-24-crag-service -p=8080:8000 docker.io/aicrowd/kdd-cup-24-crag-mock-api:v0

    echo "Starting Agent services"
    cd $WORKDIR/GenAIExamples/AgentQnA/docker_compose/intel/hpu/gaudi
    bash launch_agent_service_tgi_gaudi.sh
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
    # test worker rag agent
    echo "======================Testing worker rag agent======================"
    export agent_port="9095"
    prompt="Tell me about Michael Jackson song Thriller"
    local CONTENT=$(python3 $WORKDIR/GenAIExamples/AgentQnA/tests/test.py --prompt "$prompt")
    echo $CONTENT
    local EXIT_CODE=$(validate "$CONTENT" "Thriller" "rag-agent-endpoint")
    echo $EXIT_CODE
    if [ "$EXIT_CODE" == "1" ]; then
        docker logs rag-agent-endpoint
        exit 1
    fi

    # test worker sql agent
    echo "======================Testing worker sql agent======================"
    export agent_port="9096"
    prompt="How many schools have average math score greater than 560?"
    local CONTENT=$(python3 $WORKDIR/GenAIExamples/AgentQnA/tests/test.py --prompt "$prompt")
    local EXIT_CODE=$(validate "$CONTENT" "173" "sql-agent-endpoint")
    echo $CONTENT
    echo $EXIT_CODE
    if [ "$EXIT_CODE" == "1" ]; then
        docker logs sql-agent-endpoint
        exit 1
    fi

    # test supervisor react agent
    echo "======================Testing supervisor react agent======================"
    export agent_port="9090"
    prompt="Tell me about Michael Jackson song Thriller"
    local CONTENT=$(python3 $WORKDIR/GenAIExamples/AgentQnA/tests/test.py --prompt "$prompt")
    local EXIT_CODE=$(validate "$CONTENT" "Thriller" "react-agent-endpoint")
    echo $CONTENT
    echo $EXIT_CODE
    if [ "$EXIT_CODE" == "1" ]; then
        docker logs react-agent-endpoint
        exit 1
    fi

    prompt="How many schools have average math score greater than 560?"
    local CONTENT=$(python3 $WORKDIR/GenAIExamples/AgentQnA/tests/test.py --prompt "$prompt")
    local EXIT_CODE=$(validate "$CONTENT" "173" "react-agent-endpoint")
    echo $CONTENT
    echo $EXIT_CODE
    if [ "$EXIT_CODE" == "1" ]; then
        docker logs react-agent-endpoint
        exit 1
    fi

}

function remove_data() {
    echo "Removing data..."
    cd $WORKDIR
    rm -rf TAG-Bench
    echo "Data removed!"
}

function main() {
    echo "==================== Prepare data ===================="
    prepare_data
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

main
remove_data
