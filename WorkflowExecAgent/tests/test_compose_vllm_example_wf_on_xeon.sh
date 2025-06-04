#!/bin/bash
# Copyright (C) 2024 Intel Corporation
# SPDX-License-Identifier: Apache-2.0

wf_api_port=${wf_api_port}
[[ -z "$wf_api_port" ]] && wf_api_port=5005 && export wf_api_port=5005
api_server_url=http://$(hostname -I | awk '{print $1}'):${wf_api_port}/
workflow_id=10071
query="I have a data with gender Female, tenure 55, MonthlyCharges 103.7, TotalCharges 1840.75. Predict if this entry will churn. My workflow id is ${workflow_id}."
validate_result="is No"

function stop_agent_and_api_server() {
    echo "Stopping Agent services"
    docker rm --force $(docker ps -a -q --filter="name=workflowexec-agent-endpoint")
    docker rm --force $(docker ps -a -q --filter="name=example-workflow-service")
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
if [ $? -ne 0 ]; then
    return 1
fi
echo "=================== #2 Start vllm service completed ===================="

echo "=================== #3 Start agent service ===================="
bash 3_launch_agent_service.sh $api_server_url
echo "=================== #3 Agent service started ===================="

echo "=================== #4 Start example workflow API ===================="
bash 3_launch_example_wf_api.sh
echo "=================== #4 Example workflow API started ===================="

echo "=================== #5 Start validate agent ===================="
bash 4_validate_agent.sh "$query" "$validate_result"
echo "=================== #5 Validate agent completed ===================="

echo "=================== #6 Stop all services ===================="
stop_agent_and_api_server
stop_vllm_docker
echo "=================== #6 All services stopped ===================="

echo "ALL DONE!"
