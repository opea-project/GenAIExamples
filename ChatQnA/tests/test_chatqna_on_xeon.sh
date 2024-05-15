#!/bin/bash
# Copyright (C) 2024 Intel Corporation
# SPDX-License-Identifier: Apache-2.0

set -xe

WORKPATH=$(dirname "$PWD")
LOG_PATH="$WORKPATH/tests"
cd $WORKPATH

function setup_test_env() {
    cd $WORKPATH
    # build conda env
    conda_env_name="test_GenAIExample"
    export PATH="${HOME}/miniconda3/bin:$PATH"
    conda remove --all -y -n ${conda_env_name}
    conda create python=3.10 -y -n ${conda_env_name}
    source activate ${conda_env_name}

    # install comps
    git clone https://github.com/opea-project/GenAIComps.git
    cd GenAIComps
    pip install -r requirements.txt
    pip install .
    pip list
}

function build_docker_image() {
    cd $WORKPATH/GenAIComps

    docker build -t opea/gen-ai-comps:embedding-tei-server -f comps/embeddings/langchain/docker/Dockerfile .
    docker build -t opea/gen-ai-comps:retriever-redis-server -f comps/retrievers/langchain/docker/Dockerfile .
    docker build -t opea/gen-ai-comps:reranking-tei-xeon-server -f comps/reranks/langchain/docker/Dockerfile .
    docker build -t opea/gen-ai-comps:llm-tgi-server -f comps/llms/langchain/docker/Dockerfile .

    docker images
}

function start_microservices() {
    cd $WORKPATH

    ip_name=$(echo $(hostname) | tr '[a-z]-' '[A-Z]_')_$(echo 'IP')
    ip_address=$(eval echo '$'$ip_name)

    export EMBEDDING_MODEL_ID="BAAI/bge-base-en-v1.5"
    export RERANK_MODEL_ID="BAAI/bge-reranker-large"
    export LLM_MODEL_ID="Intel/neural-chat-7b-v3-3"
    export TEI_EMBEDDING_ENDPOINT="http://${ip_address}:6006"
    export TEI_RERANKING_ENDPOINT="http://${ip_address}:8808"
    export TGI_LLM_ENDPOINT="http://${ip_address}:9009"
    export REDIS_URL="redis://${ip_address}:6379"
    export INDEX_NAME="rag-redis"
    export HUGGINGFACEHUB_API_TOKEN=${HUGGINGFACEHUB_API_TOKEN}

    # Start Microservice Docker Containers
    # TODO: Replace the container name with a test-specific name
    cd microservice/xeon
    docker compose -f docker_compose.yaml up -d

    sleep 1m # Waits 1 minutes
}

function check_microservices() {
    # Check if the microservices are running correctly.
    # TODO: Any results check required??
    curl ${ip_address}:6006/embed \
        -X POST \
        -d '{"inputs":"What is Deep Learning?"}' \
        -H 'Content-Type: application/json' > ${LOG_PATH}/embed.log
    sleep 5s

    curl http://${ip_address}:6000/v1/embeddings \
        -X POST \
        -d '{"text":"hello"}' \
        -H 'Content-Type: application/json' > ${LOG_PATH}/embeddings.log
    sleep 10s

    test_embedding=$(python -c "import random; embedding = [random.uniform(-1, 1) for _ in range(768)]; print(embedding)")
    curl http://${ip_address}:7000/v1/retrieval \
        -X POST \
        -d '{"text":"What is the revenue of Nike in 2023?","embedding":${test_embedding}}' \
        -H 'Content-Type: application/json' > ${LOG_PATH}/retrieval.log
    sleep 5s

    curl http://${ip_address}:8808/rerank \
        -X POST \
        -d '{"query":"What is Deep Learning?", "texts": ["Deep Learning is not...", "Deep learning is..."]}' \
        -H 'Content-Type: application/json' > ${LOG_PATH}/rerank.log
    sleep 10s

    curl http://${ip_address}:8000/v1/reranking\
        -X POST \
        -d '{"initial_query":"What is Deep Learning?", "retrieved_docs": [{"text":"Deep Learning is not..."}, {"text":"Deep learning is..."}]}' \
        -H 'Content-Type: application/json' > ${LOG_PATH}/reranking.log
    sleep 30s

    curl http://${ip_address}:9009/generate \
        -X POST \
        -d '{"inputs":"What is Deep Learning?","parameters":{"max_new_tokens":17, "do_sample": true}}' \
        -H 'Content-Type: application/json' > ${LOG_PATH}/generate.log
    sleep 5s

    curl http://${ip_address}:9000/v1/chat/completions \
        -X POST \
        -d '{"text":"What is Deep Learning?"}' \
        -H 'Content-Type: application/json' > ${LOG_PATH}/completions.log
    sleep 5s
}

function run_megaservice() {
    cd $WORKPATH/microservice/xeon
    # Construct Mega Service
    ip_name=$(echo $(hostname) | tr '[a-z]-' '[A-Z]_')_$(echo 'IP')
    ip_address=$(eval echo '$'$ip_name)
    docker build -t opea/gen-ai-comps:chatqna-xeon-server -f docker/Dockerfile .
    docker run -d --name="chatqna-xeon-server" -p 8888:8888 --ipc=host -e SERVICE_SERVICE_HOST_IP=${ip_address} opea/gen-ai-comps:chatqna-xeon-server
    sleep 1m
    docker logs chatqna-xeon-server > $LOG_PATH/run_megaservice.log

    # Access the Mega Service
    curl http://${ip_address}:8888/v1/chatqna -H "Content-Type: application/json" -d '{
        "model": "Intel/neural-chat-7b-v3-3",
        "messages": "What is the revenue of Nike in 2023?"}' > ${LOG_PATH}/curl_megaservice.log
}

function check_results() {

    echo "Checking response results, make sure the output is reasonable. "
    local status=false
    if [[ -f $LOG_PATH/run_megaservice.log ]] && [[ $(grep -c "\$51.2 billion" $LOG_PATH/run_megaservice.log) != 0 ]]; then
        status=true
    fi

    if [[ -f $LOG_PATH/curl_megaservice.log ]] && [[ $(grep -c "\$51.2 billion" $LOG_PATH/curl_megaservice.log) == 0 ]]; then
        status=false
    fi

    if [ $status == false ]; then
        echo "Response check failed, please check the logs in artifacts!"
        exit 1
    else
        echo "Response check succeed!"
    fi

    echo "Checking response format, make sure the output format is acceptable for UI."
    # TODO
}

function stop_docker() {
    cd $WORKPATH/microservice/xeon
    container_list=$(cat docker_compose.yaml | grep container_name | cut -d':' -f2)
    container_list+=" chatqna-xeon-server"
    for container_name in $container_list; do
        cid=$(docker ps -aq --filter "name=$container_name")
        if [[ ! -z "$cid" ]]; then docker stop $cid && docker rm $cid && sleep 1s; fi
    done
}

function main() {

    stop_docker

    setup_test_env
    build_docker_image

    start_microservices
    check_microservices

    run_megaservice
    check_results

    stop_docker
    echo y | docker system prune

}

main
