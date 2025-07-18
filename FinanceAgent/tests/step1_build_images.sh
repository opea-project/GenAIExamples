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

function get_genai_comps() {
    if [ ! -d "GenAIComps" ] ; then
        git clone --depth 1 --branch ${opea_branch:-"main"} https://github.com/opea-project/GenAIComps.git
    fi
}

function build_dataprep_agent_images() {
    cd $WORKDIR/GenAIExamples/FinanceAgent/docker_image_build/
    get_genai_comps
    echo "Build agent image with --no-cache..."
    docker compose -f build.yaml build --no-cache
}

function build_agent_image_local(){
    cd $WORKDIR/GenAIComps/
    docker build -t opea/agent:latest -f comps/agent/src/Dockerfile . --build-arg https_proxy=$HTTPS_PROXY --build-arg http_proxy=$HTTP_PROXY
}

function build_vllm_docker_image() {
    echo "Building the vllm docker image"
    cd $WORKPATH
    echo $WORKPATH
    if [ ! -d "./vllm-fork" ]; then
        git clone https://github.com/HabanaAI/vllm-fork.git
    fi
    cd ./vllm-fork

    VLLM_FORK_VER=v0.6.6.post1+Gaudi-1.20.0
    git checkout ${VLLM_FORK_VER} &> /dev/null
    docker build --no-cache -f Dockerfile.hpu -t $VLLM_IMAGE --shm-size=128g . --build-arg https_proxy=$HTTPS_PROXY --build-arg http_proxy=$HTTP_PROXY
    if [ $? -ne 0 ]; then
        echo "$VLLM_IMAGE failed"
        exit 1
    else
        echo "$VLLM_IMAGE successful"
    fi
}

function main() {
    case $1 in
        "gaudi_vllm")
            echo "==================== Build agent docker image for Gaudi ===================="
            echo "Build vLLM docker image if needed"
            # build_vllm_docker_image
            ;;
        "xeon")
            echo "==================== Build agent docker image for Xeon ===================="
            echo "Nothing specific to build for Xeon"
            ;;
        *)
            echo "Invalid argument"
            exit 1
            ;;
    esac

    build_dataprep_agent_images

    # ## for local test
    # # build_agent_image_local
}

main $1
