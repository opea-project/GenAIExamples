#!/bin/bash
# Copyright (C) 2024 Intel Corporation
# SPDX-License-Identifier: Apache-2.0
set -xe

WORKPATH=$(dirname "$PWD")
export WORKDIR=$WORKPATH/../../
echo "WORKDIR=${WORKDIR}"
export ip_address=$(hostname -I | awk '{print $1}')
export HF_TOKEN=${HF_TOKEN}
export TOOLSET_PATH=$WORKDIR/GenAIExamples/AgentQnA/tools/
export no_proxy="$no_proxy,rag-agent-endpoint,sql-agent-endpoint,react-agent-endpoint,agent-ui,vllm-gaudi-server,jaeger,grafana,prometheus,127.0.0.1,localhost,0.0.0.0,$ip_address"
IMAGE_REPO=${IMAGE_REPO:-"opea"}
IMAGE_TAG=${IMAGE_TAG:-"latest"}
echo "REGISTRY=IMAGE_REPO=${IMAGE_REPO}"
echo "TAG=IMAGE_TAG=${IMAGE_TAG}"
export REGISTRY=${IMAGE_REPO}
export TAG=${IMAGE_TAG}
export MODEL_CACHE=${model_cache:-"./data"}

function stop_docker() {
    echo "Stopping Retrieval tool"
    cd $WORKPATH/../DocIndexRetriever/docker_compose/intel/cpu/xeon/
    docker compose -f compose.yaml down

    cd $WORKPATH/docker_compose/intel/hpu/gaudi
    docker compose -f compose.yaml -f compose.telemetry.yaml down
}

echo "workpath: $WORKPATH"
echo "::group::=================== Stop containers ===================="
stop_docker
echo "::endgroup::"

cd $WORKPATH/tests
echo "::group::=================== Building docker images===================="
bash step1_build_images.sh gaudi_vllm > docker_image_build.log
echo "::endgroup::"

echo "::group::=================== Start agent, API server, retrieval, and ingest data===================="
bash step4_launch_and_validate_agent_gaudi.sh
echo "::endgroup::"

echo "::group::=================== Stop containers ===================="
stop_docker
echo "::endgroup::"

docker system prune -f

echo "ALL DONE!!"
