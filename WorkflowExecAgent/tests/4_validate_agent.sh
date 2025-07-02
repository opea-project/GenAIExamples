#!/bin/bash
# Copyright (C) 2024 Intel Corporation
# SPDX-License-Identifier: Apache-2.0

set -e

WORKPATH=$(dirname "$PWD")
export WORKDIR=$WORKPATH/../../
echo "WORKDIR=${WORKDIR}"
export ip_address=$(hostname -I | awk '{print $1}')
query=$1
validate_result=$2

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
    local CONTENT=$(curl http://${ip_address}:9091/v1/chat/completions -X POST -H "Content-Type: application/json" -d '{
     "messages": "'"${query}"'"
    }')
    validate "$CONTENT" "$validate_result" "workflowexec-agent-endpoint"
    docker logs workflowexec-agent-endpoint
}

function main() {
    echo "==================== Validate agent service ===================="
    validate_agent_service
    echo "==================== Agent service validated ===================="
}

main
