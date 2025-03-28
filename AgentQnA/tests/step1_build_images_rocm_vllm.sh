#!/bin/bash
# Copyright (C) 2024 Intel Corporation
# SPDX-License-Identifier: Apache-2.0

set -e
export WORKPATH=$(dirname "$PWD")
export WORKDIR=${WORKPATH}/../../
echo "WORKDIR=${WORKDIR}"
export ip_address=$(hostname -I | awk '{print $1}')


function get_genai_comps() {
    if [ ! -d "GenAIComps" ] ; then
        git clone --depth 1 --branch ${opea_branch:-"main"} https://github.com/opea-project/GenAIComps.git
    fi
}


function build_docker_images_for_retrieval_tool(){
    cd $WORKPATH/../DocIndexRetriever/docker_image_build/
    get_genai_comps
    echo "Build all the images with --no-cache..."
    service_list="doc-index-retriever dataprep embedding retriever reranking"
    docker compose -f build.yaml build ${service_list} --no-cache
    docker pull ghcr.io/huggingface/text-embeddings-inference:cpu-1.5

    docker images && sleep 3s
}

function build_agent_docker_image() {
    cd $WORKPATH/docker_image_build/
    get_genai_comps
    echo "Build agent image with --no-cache..."
    docker compose -f build.yaml build --no-cache

    docker images && sleep 3s
}

#function build_vllm_docker_image() {
#    echo "Building the vllm docker image"
#    cd $WORKPATH/
#    docker build --no-cache -t opea/llm-vllm-rocm:ci -f Dockerfile-vllm-rocm .
#
#    docker images && sleep 3s
#}


function main() {
    echo "==================== Build docker images for retrieval tool ===================="
    build_docker_images_for_retrieval_tool
    echo "==================== Build docker images for retrieval tool completed ===================="

    echo "==================== Build agent docker image ===================="
    build_agent_docker_image
    echo "==================== Build agent docker image completed ===================="

#    echo "==================== Build vllm docker image ===================="
#    build_vllm_docker_image
#    echo "==================== Build vllm docker image completed ===================="

    docker image ls | grep vllm
}

main
