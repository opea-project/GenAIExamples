#!/bin/bash
# Copyright (C) 2024 Intel Corporation
# SPDX-License-Identifier: Apache-2.0

set -e

WORKPATH=$(dirname "$PWD")
vllm_port=${vllm_port}
[[ -z "$vllm_port" ]] && vllm_port=8084
export WORKDIR=$WORKPATH/../../
echo "WORKDIR=${WORKDIR}"
export SDK_BASE_URL=$1
echo "SDK_BASE_URL=$1"
export SERVING_TOKEN=${SERVING_TOKEN}
export HF_TOKEN=${HUGGINGFACEHUB_API_TOKEN}
export llm_engine=vllm
export ip_address=$(hostname -I | awk '{print $1}')
export llm_endpoint_url=http://${ip_address}:${vllm_port}
export model=mistralai/Mistral-7B-Instruct-v0.3
export recursion_limit=25
export temperature=0
export max_new_tokens=1000
export TOOLSET_PATH=$WORKDIR/GenAIExamples/WorkflowExecAgent/tools/

function start_agent() {
    echo "Starting Agent services"
    cd $WORKDIR/GenAIExamples/WorkflowExecAgent/docker_compose/intel/cpu/xeon
    WORKDIR=$WORKPATH/docker_image_build/ docker compose -f compose_vllm.yaml up -d
    echo "Waiting agent service ready"
    sleep 10s
}

function main() {
    echo "==================== Start agent service ===================="
    start_agent
    echo "==================== Agent service started ===================="
}

main
