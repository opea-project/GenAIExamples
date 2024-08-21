#!/bin/bash
# Copyright (C) 2024 Intel Corporation
# SPDX-License-Identifier: Apache-2.0

set -e
echo "IMAGE_REPO=${IMAGE_REPO}"
echo "OPENAI_API_KEY=${OPENAI_API_KEY}"

WORKPATH=$(dirname "$PWD")
export WORKDIR=$WORKPATH/../../
echo "WORKDIR=${WORKDIR}"
export ip_address=$(hostname -I | awk '{print $1}')
export TOOLSET_PATH=$WORKDIR/GenAIExamples/AgentQnA/tools/

function build_agent_docker_image() {
    cd $WORKDIR
    if [ ! -d "GenAIComps" ] ; then
        git clone https://github.com/opea-project/GenAIComps.git
    fi
    cd GenAIComps
    echo PWD: $(pwd)
    docker build -t opea/comps-agent-langchain:latest --build-arg https_proxy=$https_proxy --build-arg http_proxy=$http_proxy -f comps/agent/langchain/docker/Dockerfile .
}

function start_services() {
    echo "Starting CRAG server"
    docker run -d -p=8080:8000 docker.io/aicrowd/kdd-cup-24-crag-mock-api:v0
    echo "Starting Agent services"
    cd $WORKDIR/GenAIExamples/AgentQnA/docker/openai
    bash launch_agent_service_openai.sh
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


function run_tests() {
    echo "----------------Test supervisor agent ----------------"
    local CONTENT=$(http_proxy="" curl http://${ip_address}:9090/v1/chat/completions -X POST -H "Content-Type: application/json" -d '{
     "query": "Most recent album by Taylor Swift"
    }')
    local EXIT_CODE=$(validate "$CONTENT" "Taylor" "react-agent-endpoint")
    docker logs react-agent-endpoint
    if [ "$EXIT_CODE" == "1" ]; then
        exit 1
    fi

}

function stop_services() {
    echo "Stopping CRAG server"
    docker stop $(docker ps -q --filter ancestor=docker.io/aicrowd/kdd-cup-24-crag-mock-api:v0)
    echo "Stopping Agent services"
    docker stop $(docker ps -q --filter ancestor=opea/comps-agent-langchain:latest)
}

function main() {
    build_agent_docker_image
    start_services
    run_tests
    stop_services
}

main
