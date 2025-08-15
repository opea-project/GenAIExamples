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

function ingest_validate_dataprep() {
    # test /v1/dataprep/ingest
    echo "=========== Test ingest ==========="
    local CONTENT=$(python3 $WORKPATH/tests/test_redis_finance.py --port $DATAPREP_PORT --test_option ingest)
    local EXIT_CODE=$(validate "$CONTENT" "200" "dataprep-redis-finance")
    echo "$EXIT_CODE"
    local EXIT_CODE="${EXIT_CODE:0-1}"
    if [ "$EXIT_CODE" == "1" ]; then
        docker logs dataprep-redis-server-finance
        exit 1
    fi

    # test /v1/dataprep/get
    echo "=========== Test get ==========="
    local CONTENT=$(python3 $WORKPATH/tests/test_redis_finance.py --port $DATAPREP_PORT --test_option get)
    local EXIT_CODE=$(validate "$CONTENT" "Request successful" "dataprep-redis-finance")
    echo "$EXIT_CODE"
    local EXIT_CODE="${EXIT_CODE:0-1}"
    if [ "$EXIT_CODE" == "1" ]; then
        docker logs dataprep-redis-server-finance
        exit 1
    fi
}

function main() {
    ingest_validate_dataprep
}

main
