#!/bin/bash
# Copyright (C) 2024 Intel Corporation
# SPDX-License-Identifier: Apache-2.0

set -e

wf_api_port=${wf_api_port}
[[ -z "$wf_api_port" ]] && wf_api_port=5005
WORKPATH=$(dirname "$PWD")
LOG_PATH="$WORKPATH/tests/example_workflow"
export WORKDIR=$WORKPATH/../../
echo "WORKDIR=${WORKDIR}"

function start_example_workflow_api() {
    echo "Starting example workflow API"
    cd $WORKDIR/GenAIExamples/WorkflowExecAgent/tests/example_workflow
    docker build -f Dockerfile.example_workflow_api -t example-workflow-service .
    docker run -d -p ${wf_api_port}:${wf_api_port} --rm --network=host --name example-workflow-service -it example-workflow-service
    echo "Waiting example workflow API ready"
    until [[ "$n" -ge 100 ]] || [[ $ready == true ]]; do
        docker logs example-workflow-service &> ${LOG_PATH}/example-workflow-service.log
        n=$((n+1))
        if grep -q "Uvicorn running on" ${LOG_PATH}/example-workflow-service.log; then
            break
        fi
        if grep -q "No such container" ${LOG_PATH}/example-workflow-service.log; then
            echo "container example-workflow-service not found"
            exit 1
        fi
        sleep 5s
    done
}

function main() {
    echo "==================== Start example workflow API ===================="
    start_example_workflow_api
    echo "==================== Example workflow API started ===================="
}

main
