# Copyright (C) 2024 Intel Corporation
# SPDX-License-Identifier: Apache-2.0

function stop_agent_and_api_server() {
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

echo "=================== #3 Start agent and API server ===================="
bash 3_launch_and_validate_agent.sh
echo "=================== #3 Agent test completed ===================="

echo "=================== #4 Stop agent and API server ===================="
stop_agent_and_api_server
stop_vllm_docker
echo "=================== #4 Agent and API server stopped ===================="

echo "ALL DONE!"
