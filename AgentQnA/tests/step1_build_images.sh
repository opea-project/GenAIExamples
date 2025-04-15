#!/bin/bash
# Copyright (C) 2024 Intel Corporation
# SPDX-License-Identifier: Apache-2.0

set -e
WORKPATH=$(dirname "$PWD")
export WORKDIR=$WORKPATH/../../
echo "WORKDIR=${WORKDIR}"
export ip_address=$(hostname -I | awk '{print $1}')


function get_genai_comps() {
    if [ ! -d "GenAIComps" ] ; then
        git clone --depth 1 --branch ${opea_branch:-"main"} https://github.com/opea-project/GenAIComps.git
    fi
}


function build_docker_images_for_retrieval_tool(){
    cd $WORKDIR/GenAIExamples/DocIndexRetriever/docker_image_build/
    get_genai_comps
    echo "Build all the images with --no-cache..."
    service_list="doc-index-retriever dataprep embedding retriever reranking"
    docker compose -f build.yaml build ${service_list} --no-cache
    docker pull ghcr.io/huggingface/text-embeddings-inference:cpu-1.6

    docker images && sleep 1s
}

function build_agent_docker_image() {
    cd $WORKDIR/GenAIExamples/AgentQnA/docker_image_build/
    get_genai_comps
    echo "Build agent image with --no-cache..."
    docker compose -f build.yaml build --no-cache
}

function build_vllm_docker_image() {
    echo "Building the vllm docker image"
    cd $WORKPATH
    echo $WORKPATH
    if [ ! -d "./vllm-fork" ]; then
        git clone https://github.com/HabanaAI/vllm-fork.git
    fi
    cd ./vllm-fork
    VLLM_VER=v0.6.6.post1+Gaudi-1.20.0
    git checkout ${VLLM_VER} &> /dev/null
    docker build --no-cache -f Dockerfile.hpu -t opea/vllm-gaudi:ci --shm-size=128g . --build-arg https_proxy=$https_proxy --build-arg http_proxy=$http_proxy
    if [ $? -ne 0 ]; then
        echo "opea/vllm-gaudi:ci failed"
        exit 1
    else
        echo "opea/vllm-gaudi:ci successful"
    fi
}


function main() {
    echo "==================== Build docker images for retrieval tool ===================="
    build_docker_images_for_retrieval_tool
    echo "==================== Build docker images for retrieval tool completed ===================="

    echo "==================== Build agent docker image ===================="
    build_agent_docker_image
    echo "==================== Build agent docker image completed ===================="

    echo "==================== Build vllm docker image ===================="
    build_vllm_docker_image
    echo "==================== Build vllm docker image completed ===================="

    docker image ls | grep vllm
}

main
