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
    docker compose -f build.yaml build --no-cache
    docker images && sleep 1s
}

function build_agent_docker_image_xeon() {
    cd $WORKDIR/GenAIExamples/AgentQnA/docker_image_build/
    get_genai_comps

    echo "Build agent image with --no-cache..."
    service_list="agent agent-ui"
    docker compose -f build.yaml build ${service_list} --no-cache
}

function build_agent_docker_image_gaudi_vllm() {
    cd $WORKDIR/GenAIExamples/AgentQnA/docker_image_build/
    get_genai_comps

    git clone https://github.com/HabanaAI/vllm-fork.git && cd vllm-fork
    VLLM_FORK_VER=v0.7.2+Gaudi-1.21.0
    git checkout ${VLLM_FORK_VER} &> /dev/null && cd ../

    echo "Build agent image with --no-cache..."
    service_list="agent agent-ui vllm-gaudi"
    docker compose -f build.yaml build ${service_list} --no-cache
}

function build_agent_docker_image_rocm() {
    cd $WORKDIR/GenAIExamples/AgentQnA/docker_image_build/
    get_genai_comps

    echo "Build agent image with --no-cache..."
    service_list="agent agent-ui"
    docker compose -f build.yaml build ${service_list} --no-cache
}

function build_agent_docker_image_rocm_vllm() {
    cd $WORKDIR/GenAIExamples/AgentQnA/docker_image_build/
    get_genai_comps

    echo "Build agent image with --no-cache..."
    service_list="agent agent-ui vllm-rocm"
    docker compose -f build.yaml build ${service_list} --no-cache
}


function main() {
    echo "==================== Build docker images for retrieval tool ===================="
    build_docker_images_for_retrieval_tool
    echo "==================== Build docker images for retrieval tool completed ===================="

    sleep 3s

    case $1 in
        "rocm")
            echo "==================== Build agent docker image for ROCm ===================="
            build_agent_docker_image_rocm
            ;;
        "rocm_vllm")
            echo "==================== Build agent docker image for ROCm VLLM ===================="
            build_agent_docker_image_rocm_vllm
            ;;
        "gaudi_vllm")
            echo "==================== Build agent docker image for Gaudi ===================="
            build_agent_docker_image_gaudi_vllm
            ;;
        "xeon")
            echo "==================== Build agent docker image for Xeon ===================="
            build_agent_docker_image_xeon
            ;;
        *)
            echo "Invalid argument"
            exit 1
            ;;
    esac

    docker image ls | grep vllm
}

main $1
