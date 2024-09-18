#!/bin/bash
# Copyright (C) 2024 Intel Corporation
# SPDX-License-Identifier: Apache-2.0

set -e

echo "OPENAI_API_KEY=${OPENAI_API_KEY}"
WORKPATH=$(dirname "$PWD")
export WORKDIR=$WORKPATH/../../
echo "WORKDIR=${WORKDIR}"
export ip_address=$(hostname -I | awk '{print $1}')
export TOOLSET_PATH=$WORKDIR/GenAIExamples/AgentQnA/tools/

function stop_agent_and_api_server() {
    echo "Stopping CRAG server"
    docker stop $(docker ps -q --filter ancestor=docker.io/aicrowd/kdd-cup-24-crag-mock-api:v0)
    echo "Stopping Agent services"
    docker stop $(docker ps -q --filter ancestor=opea/agent-langchain:latest)
}

function stop_retrieval_tool() {
    echo "Stopping Retrieval tool"
    docker compose -f $WORKDIR/GenAIExamples/AgentQnA/retrieval_tool/docker/docker-compose-retrieval-tool.yaml down
}

echo "=================== #1 Building docker images===================="
bash 1_build_images.sh
echo "=================== #1 Building docker images completed===================="

echo "=================== #2 Start retrieval tool===================="
bash 2_start_retrieval_tool.sh
echo "=================== #2 Retrieval tool started===================="

echo "=================== #3 Ingest data and validate retrieval===================="
bash 3_ingest_data_and_validate_retrieval.sh
echo "=================== #3 Data ingestion and validation completed===================="

echo "=================== #4 Start agent and API server===================="
bash 4_launch_and_validate_agent_openai.sh
echo "=================== #4 Agent test passed ===================="

echo "=================== #5 Stop agent and API server===================="
stop_agent_and_api_server
echo "=================== #5 Agent and API server stopped===================="

echo "=================== #6 Stop retrieval tool===================="
stop_retrieval_tool
echo "=================== #6 Retrieval tool stopped===================="

echo "ALL DONE!"
