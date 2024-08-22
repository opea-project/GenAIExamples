#!/bin/bash
# Copyright (C) 2024 Intel Corporation
# SPDX-License-Identifier: Apache-2.0

set -e
WORKPATH=$(dirname "$PWD")
export WORKDIR=$WORKPATH/../../
echo "WORKDIR=${WORKDIR}"
export ip_address=$(hostname -I | awk '{print $1}')


function get_genai_comps() {
    cd $WORKDIR
    if [ ! -d "GenAIComps" ] ; then
        git clone https://github.com/opea-project/GenAIComps.git
    fi
}

function build_docker_images_for_retrieval_tool(){
    cd $WORKDIR/GenAIComps/
    echo $PWD
    echo "==============Building dataprep image================="
    docker build --no-cache -t opea/dataprep-redis:latest --build-arg https_proxy=$https_proxy --build-arg http_proxy=$http_proxy -f comps/dataprep/redis/langchain/docker/Dockerfile .
    echo "==============Successfully built dataprep image================="

    echo "==============Building embedding-tei image================="
    docker build --no-cache -t opea/embedding-tei:latest --build-arg https_proxy=$https_proxy --build-arg http_proxy=$http_proxy -f comps/embeddings/langchain/docker/Dockerfile .
    echo "==============Successfully built embedding-tei image================="

    echo "==============Building retriever-redis image================="
    docker build --no-cache -t opea/retriever-redis:latest --build-arg https_proxy=$https_proxy --build-arg http_proxy=$http_proxy -f comps/retrievers/langchain/redis/docker/Dockerfile .
    echo "==============Successfully built retriever-redis image================="

    echo "==============Building reranking-tei image================="
    docker build --no-cache -t opea/reranking-tei:latest --build-arg https_proxy=$https_proxy --build-arg http_proxy=$http_proxy -f comps/reranks/tei/docker/Dockerfile .
    echo "==============Successfully built reranking-tei image================="

    cd $WORKDIR/GenAIExamples/AgentQnA/retrieval_tool/docker/
    echo $PWD
    echo "==============Building retrieval-tool image================="
    docker build --no-cache -t opea/retrievaltool:latest --build-arg https_proxy=$https_proxy --build-arg http_proxy=$http_proxy -f Dockerfile_retrievaltool .
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
