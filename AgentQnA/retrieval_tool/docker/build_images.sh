# Copyright (C) 2024 Intel Corporation
# SPDX-License-Identifier: Apache-2.0

set -e
WORKPATH=$(dirname "$PWD")/..
export WORKDIR=$WORKPATH/../../
echo "WORKDIR=${WORKDIR}"
export ip_address=$(hostname -I | awk '{print $1}')

function get_genai_comps() {
    cd $WORKPATH/docker
    echo "current_path: $PWD"
    if [ ! -d "GenAIComps" ] ; then
        git clone https://github.com/opea-project/GenAIComps.git
    fi
}

function build_docker_images_for_retrieval_tool(){
    cd $WORKPATH/docker/GenAIComps/
    echo $PWD
    echo "==============Building dataprep image================="
    docker build -t opea/dataprep-on-ray-redis:latest --build-arg https_proxy=$https_proxy --build-arg http_proxy=$http_proxy -f comps/dataprep/redis/langchain_ray/docker/Dockerfile .
    echo "==============Successfully built dataprep image================="

    echo "==============Building embedding-tei image================="
    docker build -t opea/embedding-tei:latest --build-arg https_proxy=$https_proxy --build-arg http_proxy=$http_proxy -f comps/embeddings/langchain/docker/Dockerfile .
    echo "==============Successfully built embedding-tei image================="

    echo "==============Building retriever-redis image================="
    docker build -t opea/retriever-redis:latest --build-arg https_proxy=$https_proxy --build-arg http_proxy=$http_proxy -f comps/retrievers/langchain/redis/docker/Dockerfile .
    echo "==============Successfully built retriever-redis image================="

    echo "==============Building reranking-tei image================="
    docker build -t opea/reranking-tei:latest --build-arg https_proxy=$https_proxy --build-arg http_proxy=$http_proxy -f comps/reranks/tei/docker/Dockerfile .
    echo "==============Successfully built reranking-tei image================="

    docker pull ghcr.io/huggingface/tgi-gaudi:latest
    docker pull redis/redis-stack:7.2.0-v9

    RETRIEVAL_TOOL_PATH=$WORKPATH/../DocIndexRetriever
    cd $RETRIEVAL_TOOL_PATH/docker/
    if [ ! -d "GenAIComps" ] ; then
        git clone https://github.com/opea-project/GenAIComps.git
    fi
    echo "==============Building retrieval-tool image================="
    docker build -t opea/doc-index-retriever:latest --build-arg https_proxy=$https_proxy --build-arg http_proxy=$http_proxy -f ./Dockerfile .
    echo "==============Successfully built retrieval-tool image================="
}


function main() {
    echo "==================== Get GenAI components ===================="
    get_genai_comps
    echo "==================== GenAI components downloaded ===================="

    echo "==================== Build docker images for retrieval tool ===================="
    build_docker_images_for_retrieval_tool
    echo "==================== Build docker images for retrieval tool completed ===================="
}

main
