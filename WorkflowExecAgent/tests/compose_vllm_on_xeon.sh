#!/bin/bash
# Copyright (C) 2024 Intel Corporation
# SPDX-License-Identifier: Apache-2.0

workflow_id=10277
query="I have a data with gender Female, tenure 55, MonthlyAvgCharges 103.7. Predict if this entry will churn. My workflow id is '${workflow_id}'."
validate_result="The entry is not likely to churn"

function stop_agent_server() {
    echo "Stopping Agent services"
    docker rm --force $(docker ps -a -q --filter="name=workflowexec-agent-endpoint")
}

function stop_vllm_docker() {
    cid=$(docker ps -aq --filter "name=test-comps-vllm-service")
    echo "Stopping the docker containers "${cid}
    if [[ ! -z "$cid" ]]; then docker rm $cid -f && sleep 1s; fi
    echo "Docker containers stopped successfully"
}

echo "=================== #1 Building docker images ===================="
bash 1_build_images.sh
echo "=================== #1 Building docker images completed ===================="

echo "=================== #2 Start vllm service ===================="
bash 2_start_vllm_service.sh
echo "=================== #2 Start vllm service completed ===================="

echo "=================== #3 Start agent service ===================="
bash 3_launch_agent_service.sh $SDK_BASE_URL
echo "=================== #3 Agent service started ===================="

echo "=================== #4 Start validate agent ===================="
bash 4_validate_agent.sh "$query" "$validate_result"
echo "=================== #4 Validate agent completed ===================="

echo "=================== #4 Stop agent and vllm server ===================="
stop_agent_server
stop_vllm_docker
echo "=================== #4 Agent and vllm server stopped ===================="

echo "ALL DONE!"
