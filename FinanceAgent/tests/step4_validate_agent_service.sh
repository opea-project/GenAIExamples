#!/bin/bash
# Copyright (C) 2025 Intel Corporation
# SPDX-License-Identifier: Apache-2.0
set -xe

export WORKPATH=$(dirname "$PWD")
export WORKDIR=$WORKPATH/../../
echo "WORKDIR=${WORKDIR}"
export IP_ADDRESS=$(hostname -I | awk '{print $1}')
export HOST_IP=${IP_ADDRESS}
LOG_PATH=$WORKPATH

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

function validate_agent_service() {
    # test worker finqa agent
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

    # test worker research agent
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

function main() {
    validate_agent_service
}

main
