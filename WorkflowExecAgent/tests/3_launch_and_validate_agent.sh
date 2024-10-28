#!/bin/bash
# Copyright (C) 2024 Intel Corporation
# SPDX-License-Identifier: Apache-2.0

set -e

WORKPATH=$(dirname "$PWD")
workflow_id=9809
vllm_port=${vllm_port}
[[ -z "$vllm_port" ]] && vllm_port=8084
export WORKDIR=$WORKPATH/../../
echo "WORKDIR=${WORKDIR}"
export SDK_BASE_URL=${SDK_BASE_URL}
export SERVING_TOKEN=${SERVING_TOKEN}
export HF_TOKEN=${HUGGINGFACEHUB_API_TOKEN}
export llm_engine=vllm
export ip_address=$(hostname -I | awk '{print $1}')
export llm_endpoint_url=http://${ip_address}:${vllm_port}
export model=mistralai/Mistral-7B-Instruct-v0.3
export recursion_limit=25
export temperature=0
export max_new_tokens=1000
export TOOLSET_PATH=$WORKDIR/GenAIExamples/WorkflowExecAgent/tools/

function start_agent_and_api_server() {
    echo "Starting Agent services"
    cd $WORKDIR/GenAIExamples/WorkflowExecAgent/docker_compose/intel/cpu/xeon
    WORKDIR=$WORKPATH/docker_image_build/ docker compose -f compose_vllm.yaml up -d
    echo "Waiting agent service ready"
    sleep 5s
}

function validate() {
    local CONTENT="$1"
    local EXPECTED_RESULT="$2"
    local SERVICE_NAME="$3"

    if echo "$CONTENT" | grep -q "$EXPECTED_RESULT"; then
        echo "[ $SERVICE_NAME ] Content is as expected: $CONTENT"
        echo "[TEST INFO]: Workflow Executor agent service PASSED"
    else
        echo "[ $SERVICE_NAME ] Content does not match the expected result: $CONTENT"
        echo "[TEST INFO]: Workflow Executor agent service FAILED"
    fi
}

function validate_agent_service() {
    echo "----------------Test agent ----------------"
    local CONTENT=$(curl http://${ip_address}:9090/v1/chat/completions -X POST -H "Content-Type: application/json" -d '{
     "query": "I have a data with gender Female, tenure 55, MonthlyAvgCharges 103.7. Predict if this entry will churn. My workflow id is '${workflow_id}'."
    }')
    validate "$CONTENT" "The entry is not likely to churn" "workflowexec-agent-endpoint"
    docker logs workflowexec-agent-endpoint
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
