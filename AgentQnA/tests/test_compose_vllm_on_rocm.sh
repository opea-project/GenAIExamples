#!/bin/bash
# Copyright (C) 2024 Advanced Micro Devices, Inc.
# SPDX-License-Identifier: Apache-2.0

set -e

WORKPATH=$(dirname "$PWD")
export WORKDIR=${WORKPATH}/../../
echo "WORKDIR=${WORKDIR}"
export ip_address=$(hostname -I | awk '{print $1}')
export HUGGINGFACEHUB_API_TOKEN=${HUGGINGFACEHUB_API_TOKEN}
export TOOLSET_PATH=$WORKPATH/tools/
IMAGE_REPO=${IMAGE_REPO:-"opea"}
IMAGE_TAG=${IMAGE_TAG:-"latest"}
echo "REGISTRY=IMAGE_REPO=${IMAGE_REPO}"
echo "TAG=IMAGE_TAG=${IMAGE_TAG}"
export REGISTRY=${IMAGE_REPO}
export TAG=${IMAGE_TAG}
export MODEL_CACHE=${model_cache:-"./data"}

function stop_crag() {
    cid=$(docker ps -aq --filter "name=kdd-cup-24-crag-service")
    echo "Stopping container kdd-cup-24-crag-service with cid $cid"
    if [[ ! -z "$cid" ]]; then docker rm $cid -f && sleep 1s; fi
}

function stop_agent_docker() {
    cd $WORKPATH/docker_compose/amd/gpu/rocm
    bash stop_agent_service_vllm_rocm.sh
}

function stop_retrieval_tool() {
    echo "Stopping Retrieval tool"
    local RETRIEVAL_TOOL_PATH=$WORKDIR/GenAIExamples/DocIndexRetriever
    cd $RETRIEVAL_TOOL_PATH/docker_compose/intel/cpu/xeon/
    docker compose -f compose.yaml down
}

echo "workpath: $WORKPATH"
echo "::group::=================== Stop containers ===================="
stop_crag
stop_agent_docker
stop_retrieval_tool
echo "::endgroup::"

cd $WORKPATH/tests

echo "::group::=================== #1 Building docker images===================="
bash step1_build_images.sh rocm_vllm > docker_image_build.log
echo "::endgroup::=================== #1 Building docker images completed===================="

echo "::group::=================== #2 Start retrieval tool===================="
bash step2_start_retrieval_tool_rocm_vllm.sh
echo "::endgroup::=================== #2 Retrieval tool started===================="

echo "::group::=================== #3 Ingest data and validate retrieval===================="
bash step3_ingest_data_and_validate_retrieval_rocm_vllm.sh
echo "::endgroup::=================== #3 Data ingestion and validation completed===================="

echo "::group::=================== #4 Start agent and API server===================="
bash step4_launch_and_validate_agent_rocm_vllm.sh
echo "::endgroup::=================== #4 Agent test passed ===================="

echo "::group::=================== #5 Stop agent and API server===================="
stop_crag
stop_agent_docker
stop_retrieval_tool
echo "::endgroup::=================== #5 Agent and API server stopped===================="

echo y | docker system prune

echo "ALL DONE!!"
