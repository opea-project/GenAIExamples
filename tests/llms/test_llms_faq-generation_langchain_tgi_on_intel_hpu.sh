#!/bin/bash
# Copyright (C) 2024 Intel Corporation
# SPDX-License-Identifier: Apache-2.0

set -x

WORKPATH=$(dirname "$PWD")
host_ip=$(hostname -I | awk '{print $1}')
LOG_PATH="$WORKPATH/tests"

function build_docker_images() {
    cd $WORKPATH
    docker build --no-cache -t opea/llm-faqgen:latest --build-arg https_proxy=$https_proxy --build-arg http_proxy=$http_proxy -f comps/llms/src/faq-generation/Dockerfile .
    if [ $? -ne 0 ]; then
        echo "opea/llm-faqgen built fail"
        exit 1
    else
        echo "opea/llm-faqgen built successful"
    fi
}

function start_service() {
    export LLM_ENDPOINT_PORT=5062
    export FAQ_PORT=5063
    export host_ip=${host_ip}
    export HUGGINGFACEHUB_API_TOKEN=${HF_TOKEN} # Remember to set HF_TOKEN before invoking this test!
    export LLM_ENDPOINT="http://${host_ip}:${LLM_ENDPOINT_PORT}"
    export LLM_MODEL_ID="Intel/neural-chat-7b-v3-3"
    export FAQGen_COMPONENT_NAME="OPEAFAQGen_TGI"
    export LOGFLAG=True

    cd $WORKPATH/comps/llms/deployment/docker_compose
    docker compose -f faq-generation_tgi_on_intel_hpu.yaml up -d > ${LOG_PATH}/start_services_with_compose.log

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

        if echo "$CONTENT" | grep -q "$EXPECTED_RESULT"; then
            echo "[ $SERVICE_NAME ] Content is as expected."
        else
            echo "[ $SERVICE_NAME ] Content does not match the expected result: $CONTENT"
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

function validate_backend_microservices() {
    # tgi
    validate_services \
        "${host_ip}:${LLM_ENDPOINT_PORT}/generate" \
        "generated_text" \
        "tgi" \
        "tgi-gaudi-server" \
        '{"inputs":"What is Deep Learning?","parameters":{"max_new_tokens":17, "do_sample": true}}'

    # faq
    validate_services \
        "${host_ip}:${FAQ_PORT}/v1/faqgen" \
        "text" \
        "llm - faqgen" \
        "llm-faqgen-server" \
        '{"query":"Text Embeddings Inference (TEI) is a toolkit for deploying and serving open source text embeddings and sequence classification models. TEI enables high-performance extraction for the most popular models, including FlagEmbedding, Ember, GTE and E5.","max_tokens": 32}'

    # faq, non-stream
    validate_services \
        "${host_ip}:${FAQ_PORT}/v1/faqgen" \
        "text" \
        "FAQGen" \
        "llm-faqgen-server" \
        '{"query":"Text Embeddings Inference (TEI) is a toolkit for deploying and serving open source text embeddings and sequence classification models. TEI enables high-performance extraction for the most popular models, including FlagEmbedding, Ember, GTE and E5.","max_tokens": 32, "stream":false}'
}

function stop_docker() {
    cd $WORKPATH/comps/llms/deployment/docker_compose
    docker compose -f faq-generation_tgi_on_intel_hpu.yaml down
}

function main() {

    stop_docker

    build_docker_images
    start_service

    validate_backend_microservices

    stop_docker
    echo y | docker system prune

}

main
