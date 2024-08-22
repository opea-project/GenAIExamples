#!/bin/bash
# Copyright (C) 2024 Intel Corporation
# SPDX-License-Identifier: Apache-2.0

set -e

WORKPATH=$(dirname "$PWD")
export WORKDIR=$WORKPATH/../../
echo "WORKDIR=${WORKDIR}"
export ip_address=$(hostname -I | awk '{print $1}')


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

function ingest_data_and_validate() {
    echo "Ingesting data"
    cd $WORKDIR/GenAIExamples/AgentQnA/retrieval_tool/
    local CONTENT=$(bash run_ingest_data.sh)
    local EXIT_CODE=$(validate "$CONTENT" "Data preparation succeeded" "dataprep-redis-server")
    echo "$EXIT_CODE"
    local EXIT_CODE="${EXIT_CODE:0-1}"
    echo "return value is $EXIT_CODE"
    if [ "$EXIT_CODE" == "1" ]; then
        docker logs dataprep-redis-server
        return 1
    fi
}

function validate_retrieval_tool() {
    echo "----------------Test retrieval tool ----------------"
    local CONTENT=$(http_proxy="" curl http://${ip_address}:8889/v1/retrievaltool -X POST -H "Content-Type: application/json" -d '{
     "text": "Who sang Thriller"
    }')
    local EXIT_CODE=$(validate "$CONTENT" "Thriller" "retrieval-tool")
    
    if [ "$EXIT_CODE" == "1" ]; then
        docker logs retrievaltool-xeon-backend-server
        exit 1
    fi
}

function main(){

    echo "==================== Ingest data ===================="
    ingest_data_and_validate
    echo "==================== Data ingestion completed ===================="

    echo "==================== Validate retrieval tool ===================="
    validate_retrieval_tool
    echo "==================== Retrieval tool validated ===================="
}