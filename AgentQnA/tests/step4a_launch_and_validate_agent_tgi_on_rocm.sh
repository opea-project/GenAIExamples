#!/bin/bash
# Copyright (C) 2024 Intel Corporation
# SPDX-License-Identifier: Apache-2.0

set -ex

WORKPATH=$(dirname "$PWD")
ls $WORKPATH
export WORKDIR=$WORKPATH/../../
echo "WORKDIR=${WORKDIR}"
export ip_address=$(hostname -I | awk '{print $1}')
export TOOLSET_PATH=$WORKPATH/tools/
export HUGGINGFACEHUB_API_TOKEN=${HUGGINGFACEHUB_API_TOKEN}

export HF_CACHE_DIR=${model_cache:-"$WORKDIR/hf_cache"}
if [ ! -d "$HF_CACHE_DIR" ]; then
    mkdir -p "$HF_CACHE_DIR"
fi
ls $HF_CACHE_DIR


function start_agent_and_api_server() {
    echo "Starting Agent services"
    cd $WORKDIR/GenAIExamples/AgentQnA/docker_compose/amd/gpu/rocm
    bash launch_agent_service_tgi_rocm.sh
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
    local CONTENT=$(http_proxy="" curl http://${ip_address}:9095/v1/chat/completions -X POST -H "Content-Type: application/json" -d '{
     "query": "Tell me about Michael Jackson song thriller"
    }')
    local EXIT_CODE=$(validate "$CONTENT" "Thriller" "react-agent-endpoint")
    docker logs rag-agent-endpoint
    if [ "$EXIT_CODE" == "1" ]; then
        exit 1
    fi

    local CONTENT=$(http_proxy="" curl http://${ip_address}:9090/v1/chat/completions -X POST -H "Content-Type: application/json" -d '{
     "query": "Tell me about Michael Jackson song thriller"
    }')
    local EXIT_CODE=$(validate "$CONTENT" "Thriller" "react-agent-endpoint")
    docker logs react-agent-endpoint
    if [ "$EXIT_CODE" == "1" ]; then
        exit 1
    fi

}

function main() {
    echo "==================== Start agent ===================="
    start_agent_and_api_server
    echo "==================== Agent started ===================="

    echo "==================== Validate agent service ===================="
    validate_agent_service
    echo "==================== Agent service validated ===================="
}

main
