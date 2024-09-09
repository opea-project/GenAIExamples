#!/bin/bash
# Copyright (C) 2024 Intel Corporation
# SPDX-License-Identifier: Apache-2.0

set -e
WORKPATH=$(dirname "$PWD")
export WORKDIR=$WORKPATH/../../
echo "WORKDIR=${WORKDIR}"
export ip_address=$(hostname -I | awk '{print $1}')


function get_genai_comps() {
    cd $WORKPATH/docker
    if [ ! -d "GenAIComps" ] ; then
        git clone https://github.com/opea-project/GenAIComps.git
    fi
}

function build_docker_images_for_retrieval_tool(){
    RETRIEVAL_TOOL_PATH=$WORKPATH/retrieval_tool
    cd $RETRIEVAL_TOOL_PATH/docker/
    echo "==============Building retrieval-tool image================="
    echo "current_path: $PWD"
    bash build_images.sh
    echo "==============Successfully built retrieval-tool image================="
}

function build_agent_docker_image() {
    cd $WORKDIR/GenAIComps
    docker build -t opea/comps-agent-langchain:latest --build-arg https_proxy=$https_proxy --build-arg http_proxy=$http_proxy -f comps/agent/langchain/docker/Dockerfile .
}

function main() {

    echo "==================== Get GenAI components ===================="
    get_genai_comps
    echo "==================== GenAI components downloaded ===================="

    echo "==================== Build docker images for retrieval tool ===================="
    build_docker_images_for_retrieval_tool
    echo "==================== Build docker images for retrieval tool completed ===================="

    echo "==================== Build agent docker image ===================="
    build_agent_docker_image
    echo "==================== Build agent docker image completed ===================="
}

main
