#!/bin/bash
# Copyright (C) 2024 Intel Corporation
# SPDX-License-Identifier: Apache-2.0

set -xe

WORKPATH=$(dirname "$PWD")
host_ip=$(hostname -I | awk '{print $1}')
LOG_PATH="$WORKPATH/tests"

function build_docker_images() {
    cd $WORKPATH
    git clone https://github.com/HabanaAI/vllm-fork.git
    cd vllm-fork/
    docker build --no-cache -f Dockerfile.hpu -t opea/vllm-gaudi:latest --shm-size=128g .
    if [ $? -ne 0 ]; then
        echo "opea/vllm-gaudi built fail"
        exit 1
    else
        echo "opea/vllm-gaudi built successful"
    fi

    cd $WORKPATH
    docker build --no-cache -t opea/llm-docsum:latest --build-arg https_proxy=$https_proxy --build-arg http_proxy=$http_proxy -f comps/llms/src/doc-summarization/Dockerfile .
    if [ $? -ne 0 ]; then
        echo "opea/llm-docsum built fail"
        exit 1
    else
        echo "opea/llm-docsum built successful"
    fi
}

function start_service() {
    export host_ip=${host_ip}
    export LLM_ENDPOINT_PORT=5076
    export DOCSUM_PORT=5077
    export HUGGINGFACEHUB_API_TOKEN=${HF_TOKEN}
    export LLM_ENDPOINT="http://${host_ip}:${LLM_ENDPOINT_PORT}"
    export LLM_MODEL_ID="Intel/neural-chat-7b-v3-3"
    export MAX_INPUT_TOKENS=2048
    export MAX_TOTAL_TOKENS=4096
    export DocSum_COMPONENT_NAME="OPEADocSum_vLLM" # or "vllm"
    export VLLM_SKIP_WARMUP=true
    export LOGFLAG=True

    cd $WORKPATH/comps/llms/deployment/docker_compose
    docker compose -f doc-summarization_vllm_on_intel_hpu.yaml up -d > ${LOG_PATH}/start_services_with_compose.log

    sleep 30s
}

function validate_services() {
    local URL="$1"
    local EXPECTED_RESULT="$2"
    local SERVICE_NAME="$3"
    local DOCKER_NAME="$4"
    local INPUT_DATA="$5"

    local HTTP_STATUS=$(curl -s -o /dev/null -w "%{http_code}" -X POST -d "$INPUT_DATA" -H 'Content-Type: application/json' "$URL")

    echo "==========================================="

    if [ "$HTTP_STATUS" -eq 200 ]; then
        echo "[ $SERVICE_NAME ] HTTP status is 200. Checking content..."

        local CONTENT=$(curl -s -X POST -d "$INPUT_DATA" -H 'Content-Type: application/json' "$URL" | tee ${LOG_PATH}/${SERVICE_NAME}.log)

        echo $CONTENT

        if echo "$CONTENT" | grep -q "$EXPECTED_RESULT"; then
            echo "[ $SERVICE_NAME ] Content is as expected."
        else
            echo "[ $SERVICE_NAME ] Content does not match the expected result"
            docker logs ${DOCKER_NAME} >> ${LOG_PATH}/${SERVICE_NAME}.log
            exit 1
        fi
    else
        echo "[ $SERVICE_NAME ] HTTP status is not 200. Received status was $HTTP_STATUS"
        docker logs ${DOCKER_NAME} >> ${LOG_PATH}/${SERVICE_NAME}.log
        exit 1
    fi
    sleep 1s
}

function validate_microservices() {
    URL="http://${host_ip}:$DOCSUM_PORT/v1/docsum"

    echo "Validate vllm..."
    validate_services \
        "${LLM_ENDPOINT}/v1/completions" \
        "text" \
        "vllm" \
        "vllm-gaudi-server" \
        '{"model": "Intel/neural-chat-7b-v3-3", "prompt": "What is Deep Learning?", "max_tokens": 32, "temperature": 0}'

    echo "Validate stream=True..."
    validate_services \
        "$URL" \
        'text' \
        "llm_summarization" \
        "llm-docsum-server" \
        '{"query": "Text Embeddings Inference (TEI) is a toolkit for deploying and serving open source text embeddings and sequence classification models. TEI enables high-performance extraction for the most popular models, including FlagEmbedding, Ember, GTE and E5.", "max_tokens":32, "language":"en"}'

    echo "Validate stream=False..."
    validate_services \
        "$URL" \
        'text' \
        "llm_summarization" \
        "llm-docsum-server" \
        '{"query":"Text Embeddings Inference (TEI) is a toolkit for deploying and serving open source text embeddings and sequence classification models. TEI enables high-performance extraction for the most popular models, including FlagEmbedding, Ember, GTE and E5.", "max_tokens":32, "language":"en", "stream":false}'

    echo "Validate Chinese mode..."
    validate_services \
        "$URL" \
        'text' \
        "llm_summarization" \
        "llm-docsum-server" \
        '{"query":"2024年9月26日，北京——今日，英特尔正式发布英特尔® 至强® 6性能核处理器（代号Granite Rapids），为AI、数据分析、科学计算等计算密集型业务提供卓越性能。", "max_tokens":32, "language":"zh", "stream":false}'

    echo "Validate truncate mode..."
    validate_services \
        "$URL" \
        'text' \
        "llm_summarization" \
        "llm-docsum-server" \
        '{"query":"Text Embeddings Inference (TEI) is a toolkit for deploying and serving open source text embeddings and sequence classification models. TEI enables high-performance extraction for the most popular models, including FlagEmbedding, Ember, GTE and E5.", "max_tokens":32, "language":"en", "summary_type": "truncate", "chunk_size": 2000}'

    echo "Validate map_reduce mode..."
    validate_services \
        "$URL" \
        'text' \
        "llm_summarization" \
        "llm-docsum-server" \
        '{"query":"Text Embeddings Inference (TEI) is a toolkit for deploying and serving open source text embeddings and sequence classification models. TEI enables high-performance extraction for the most popular models, including FlagEmbedding, Ember, GTE and E5.", "max_tokens":32, "language":"en", "summary_type": "map_reduce", "chunk_size": 2000, "stream":false}'

    echo "Validate refine mode..."
    validate_services \
        "$URL" \
        'text' \
        "llm_summarization" \
        "llm-docsum-server" \
        '{"query":"Text Embeddings Inference (TEI) is a toolkit for deploying and serving open source text embeddings and sequence classification models. TEI enables high-performance extraction for the most popular models, including FlagEmbedding, Ember, GTE and E5.", "max_tokens":32, "language":"en", "summary_type": "refine", "chunk_size": 2000}'
}

function stop_docker() {
    cd $WORKPATH/comps/llms/deployment/docker_compose
    docker compose -f doc-summarization_vllm_on_intel_hpu.yaml down
}

function main() {

    stop_docker

    build_docker_images
    start_service

    validate_microservices

    stop_docker
    echo y | docker system prune

}

main
