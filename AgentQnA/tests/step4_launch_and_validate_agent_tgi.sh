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

export HF_CACHE_DIR=$WORKDIR/hf_cache
if [ ! -d "$HF_CACHE_DIR" ]; then
    mkdir -p "$HF_CACHE_DIR"
fi
ls $HF_CACHE_DIR

function start_tgi(){
    echo "Starting tgi-gaudi server"
    cd $WORKDIR/GenAIExamples/AgentQnA/docker_compose/intel/hpu/gaudi
    bash launch_tgi_gaudi.sh

}

function start_agent_and_api_server() {
    echo "Starting CRAG server"
    docker run -d --runtime=runc --name=kdd-cup-24-crag-service -p=8080:8000 docker.io/aicrowd/kdd-cup-24-crag-mock-api:v0

    echo "Starting Agent services"
    cd $WORKDIR/GenAIExamples/AgentQnA/docker_compose/intel/hpu/gaudi
    bash launch_agent_service_tgi_gaudi.sh
    sleep 10
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
    echo "----------------Test agent ----------------"
    # local CONTENT=$(http_proxy="" curl http://${ip_address}:9095/v1/chat/completions -X POST -H "Content-Type: application/json" -d '{
    #  "query": "Tell me about Michael Jackson song thriller"
    # }')
    export agent_port="9095"
    local CONTENT=$(python3 $WORKDIR/GenAIExamples/AgentQnA/tests/test.py)
    local EXIT_CODE=$(validate "$CONTENT" "Thriller" "rag-agent-endpoint")
    docker logs rag-agent-endpoint
    if [ "$EXIT_CODE" == "1" ]; then
        exit 1
    fi

    # local CONTENT=$(http_proxy="" curl http://${ip_address}:9090/v1/chat/completions -X POST -H "Content-Type: application/json" -d '{
    #  "query": "Tell me about Michael Jackson song thriller"
    # }')
    export agent_port="9090"
    local CONTENT=$(python3 $WORKDIR/GenAIExamples/AgentQnA/tests/test.py)
    local EXIT_CODE=$(validate "$CONTENT" "Thriller" "react-agent-endpoint")
    docker logs react-agent-endpoint
    if [ "$EXIT_CODE" == "1" ]; then
        exit 1
    fi

}

function main() {
    echo "==================== Start TGI ===================="
    start_tgi
    echo "==================== TGI started ===================="

    echo "==================== Start agent ===================="
    start_agent_and_api_server
    echo "==================== Agent started ===================="

    echo "==================== Validate agent service ===================="
    validate_agent_service
    echo "==================== Agent service validated ===================="
}

main
