#!/bin/bash
# Copyright (C) 2024 Intel Corporation
# SPDX-License-Identifier: Apache-2.0

set -xe

WORKPATH=$(dirname "$PWD")
ip_address=$(hostname -I | awk '{print $1}')
LOG_PATH="$WORKPATH/tests"

function build_docker_images() {
    cd $WORKPATH
    docker build --no-cache -t opea/llm-sum-tgi:comps --build-arg https_proxy=$https_proxy --build-arg http_proxy=$http_proxy -f comps/llms/summarization/tgi/langchain/Dockerfile .
    if [ $? -ne 0 ]; then
        echo "opea/llm-textgen built fail"
        exit 1
    else
        echo "opea/llm-textgen built successful"
    fi
}

function start_service() {
    tgi_endpoint_port=5075
    export LLM_MODEL_ID="Intel/neural-chat-7b-v3-3"
    export MAX_INPUT_TOKENS=2048
    export MAX_TOTAL_TOKENS=4096
    # Remember to set HF_TOKEN before invoking this test!
    export HF_TOKEN=${HF_TOKEN}
    docker run -d --name="test-comps-llm-sum-tgi-endpoint" -p $tgi_endpoint_port:80 -v ./data:/data -e http_proxy=$http_proxy -e https_proxy=$https_proxy --shm-size 1g ghcr.io/huggingface/text-generation-inference:1.4 --model-id ${LLM_MODEL_ID} --max-input-length ${MAX_INPUT_TOKENS} --max-total-tokens ${MAX_TOTAL_TOKENS}
    export TGI_LLM_ENDPOINT="http://${ip_address}:${tgi_endpoint_port}"

    sum_port=5076
    docker run -d --name="test-comps-llm-sum-tgi-server" -p ${sum_port}:9000 --ipc=host -e http_proxy=$http_proxy -e https_proxy=$https_proxy -e TGI_LLM_ENDPOINT=$TGI_LLM_ENDPOINT -e LLM_MODEL_ID=$LLM_MODEL_ID -e MAX_INPUT_TOKENS=$MAX_INPUT_TOKENS -e MAX_TOTAL_TOKENS=$MAX_TOTAL_TOKENS -e HUGGINGFACEHUB_API_TOKEN=$HF_TOKEN -e LOGFLAG=True opea/llm-sum-tgi:comps

    # check whether tgi is fully ready
    n=0
    until [[ "$n" -ge 100 ]] || [[ $ready == true ]]; do
        docker logs test-comps-llm-sum-tgi-endpoint > ${LOG_PATH}/test-comps-llm-sum-tgi-endpoint.log
        n=$((n+1))
        if grep -q Connected ${LOG_PATH}/test-comps-llm-sum-tgi-endpoint.log; then
            break
        fi
        sleep 5s
    done
    sleep 5s
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
    sum_port=5076
    URL="http://${ip_address}:$sum_port/v1/chat/docsum"

    validate_services \
        "$URL" \
        'text' \
        "llm_summarization" \
        "test-comps-llm-sum-tgi-server" \
        '{"query": "What is Deep Learning?"}'

    validate_services \
        "$URL" \
        'text' \
        "llm_summarization" \
        "test-comps-llm-sum-tgi-server" \
        '{"query": "What is Deep Learning?", "summary_type": "truncate"}'

    validate_services \
        "$URL" \
        'text' \
        "llm_summarization" \
        "test-comps-llm-sum-tgi-server" \
        '{"query": "What is Deep Learning?", "summary_type": "map_reduce"}'

    validate_services \
        "$URL" \
        'text' \
        "llm_summarization" \
        "test-comps-llm-sum-tgi-server" \
        '{"query": "What is Deep Learning?", "summary_type": "refine"}'
}

function stop_docker() {
    cid=$(docker ps -aq --filter "name=test-comps-llm-sum-tgi*")
    if [[ ! -z "$cid" ]]; then docker stop $cid && docker rm $cid && sleep 1s; fi
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
