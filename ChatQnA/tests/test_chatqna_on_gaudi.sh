#!/bin/bash
# Copyright (C) 2024 Intel Corporation
# SPDX-License-Identifier: Apache-2.0

set -xe

function setup_test_env() {
    WORKPATH=$(dirname "$PWD")
    LOG_PATH="$WORKPATH/tests"
    cd $WORKPATH

    # build conda env
    conda_env_name="test_GenAIExample"
    export PATH="${HOME}/miniconda3/bin:$PATH"
    conda remove --all -y -n ${conda_env_name}
    conda create python=3.10 -y -n ${conda_env_name}
    conda activate ${conda_env_name}

    # install comps
    git clone https://github.com/opea-project/GenAIComps.git
    cd GenAIComps
    pip install -r requirements.txt
    python setup.py install
    pip list
}

function build_docker_image() {
    cd $WORKPATH/GenAIComps

    docker build -t opea/gen-ai-comps:embedding-tei-server -f comps/embeddings/docker/Dockerfile .
    docker build -t opea/gen-ai-comps:retriever-redis-server -f comps/retrievers/langchain/docker/Dockerfile .
    docker build -t opea/gen-ai-comps:reranking-tei-gaudi-server -f comps/reranks/docker/Dockerfile .
    docker build -t opea/gen-ai-comps:llm-tgi-server -f comps/llms/langchain/docker/Dockerfile .

    cd ..
    git clone https://github.com/huggingface/tei-gaudi
    cd tei-gaudi/
    docker build -f Dockerfile-hpu -t opea/tei_gaudi .

    docker pull ghcr.io/huggingface/tgi-gaudi:1.2.1
    docker pull intel/gen-ai-examples:qna-rag-redis-server

    docker images
}

function start_microservices() {
    cd $WORKPATH

    ip_name=$(echo $(hostname) | tr '[a-z]-' '[A-Z]_')_$(echo 'IP')
    ip_address=$(eval echo '$'$ip_name)

    export EMBEDDING_MODEL_ID="BAAI/bge-large-en-v1.5"
    export RERANK_MODEL_ID="BAAI/bge-reranker-large"
    export LLM_MODEL_ID="Intel/neural-chat-7b-v3-3"
    export TEI_EMBEDDING_ENDPOINT="http://${ip_address}:8090"
    export TEI_RERANKING_ENDPOINT="http://${ip_address}:6060"
    export TGI_LLM_ENDPOINT="http://${ip_address}:8008"
    export REDIS_URL="redis://${ip_address}:6379"
    export INDEX_NAME="rag_redis"
    export HUGGINGFACEHUB_API_TOKEN=${HUGGINGFACEHUB_API_TOKEN}

    # Start Microservice Docker Containers
    REDIS_VECTOR_DB_CONTAINER_NAME="redis-vector-db"
    QNA_RAG_REDIS_CONTAINER_NAME="qna-rag-redis-server"
    TEI_EMBEDDING_CONTAINER_NAME="tei_embedding_gaudi_server"
    EMBEDDING_CONTAINER_NAME="embedding-tei-server"
    RETRIEVER_CONTAINER_NAME="retriever-redis-server"
    TEI_RERAN_GAUDI_CONTAINER_NAME="tei_reranking_gaudi_server"
    RERANK_TEI_CONTAINER_NAME="reranking-tei-gaudi-server"
    TGI_CONTAINER_NAME="tgi_service"
    LLM_CONTAINER_NAME="llm-tgi-gaudi-server"
    cd microservices/gaudi
    docker compose -f docker_compose.yaml up -d

    sleep 3m # Waits 3 minutes
}

function check_microservices() {
    # TEI Embedding Service
    curl ${IP_NAME}:8090/embed \
        -X POST \
        -d '{"inputs":"What is Deep Learning?"}' \
        -H 'Content-Type: application/json'

    curl http://${IP_NAME}:6000/v1/embeddings \
        -X POST \
        -d '{"text":"hello"}' \
        -H 'Content-Type: application/json'

    curl http://${IP_NAME}:7000/v1/retrieval \
        -X POST \
        -d '{"text":"test","embedding":[1,1,...1]}' \
        -H 'Content-Type: application/json'


    curl http://${IP_NAME}:6060/rerank \
        -X POST \
        -d '{"query":"What is Deep Learning?", "texts": ["Deep Learning is not...", "Deep learning is..."]}' \
        -H 'Content-Type: application/json'

    curl http://${IP_NAME}:8000/v1/reranking \
        -X POST \
        -d '{"initial_query":"What is Deep Learning?", "retrieved_docs": [{"text":"Deep Learning is not..."}, {"text":"Deep learning is..."}]}' \
        -H 'Content-Type: application/json'

    curl http://${IP_NAME}:8008/generate \
        -X POST \
        -d '{"inputs":"What is Deep Learning?","parameters":{"max_new_tokens":64, "do_sample": true}}' \
        -H 'Content-Type: application/json'

    curl http://${IP_NAME}:9000/v1/chat/completions \
        -X POST \
        -d '{"text":"What is Deep Learning?"}' \
        -H 'Content-Type: application/json'
}

function ingest_data() {
    cd $WORKPATH
    docker exec $QNA_RAG_REDIS_CONTAINER_NAME \
        bash -c "cd /ws && python ingest.py > /dev/null"
    sleep 1m
}

function run_megaservice() {
    python chatqna.py > ${LOG_PATH}/run_megaservice.log
}

function check_results() {
    echo "Checking response"
    local status=false
    if [[ -f $LOG_PATH/run_megaservice.log ]] && [[ $(grep -c "\$51.2 billion" $LOG_PATH/run_megaservice.log) != 0 ]]; then
        status=true
    fi

    if [ $status == false ]; then
        echo "Response check failed, please check the logs in artifacts!"
        exit 1
    else
        echo "Response check succeed!"
    fi
}

function stop_docker() {
    local container_name=$1
    cid=$(docker ps -aq --filter "name=$container_name")
    if [[ ! -z "$cid" ]]; then docker stop $cid && docker rm $cid; fi
}

function main() {
    setup_test_env
    build_docker_image
    
    start_microservices
    check_microservices

    ingest_data
    run_megaservice
    check_results

}

main
