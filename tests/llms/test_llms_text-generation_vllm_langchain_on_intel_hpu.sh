#!/bin/bash
# Copyright (C) 2024 Intel Corporation
# SPDX-License-Identifier: Apache-2.0

set -x

WORKPATH=$(dirname "$PWD")
ip_address=$(hostname -I | awk '{print $1}')

function build_docker_images() {
    ## Build VLLM docker
    cd $WORKPATH
    git clone https://github.com/HabanaAI/vllm-fork.git
    cd vllm-fork/
    git checkout 3c39626
    docker build --no-cache -f Dockerfile.hpu -t opea/vllm-gaudi:comps --shm-size=128g .
    if [ $? -ne 0 ]; then
        echo "opea/vllm-gaudi built fail"
        exit 1
    else
        echo "opea/vllm-gaudi built successful"
    fi

    ## Build OPEA microservice docker
    cd $WORKPATH
    docker build  \
        --no-cache -t opea/llm-vllm:comps \
        -f comps/llms/text-generation/vllm/langchain/Dockerfile .
    if [ $? -ne 0 ]; then
        echo "opea/llm-vllm built fail"
        exit 1
    else
        echo "opea/llm-vllm built successful"
    fi
}

function start_service() {
    export LLM_MODEL="Intel/neural-chat-7b-v3-3"
    port_number=5025
    docker run -d --rm \
        --runtime=habana \
        --name="test-comps-vllm-service" \
        -v $PWD/data:/data \
        -p $port_number:80 \
        -e HABANA_VISIBLE_DEVICES=all \
        -e OMPI_MCA_btl_vader_single_copy_mechanism=none \
        --cap-add=sys_nice \
        --ipc=host \
        -e HF_TOKEN=${HUGGINGFACEHUB_API_TOKEN} \
        opea/vllm-gaudi:comps \
        --enforce-eager --model $LLM_MODEL  --tensor-parallel-size 1 --host 0.0.0.0 --port 80 --block-size 128 --max-num-seqs 256 --max-seq_len-to-capture 2048

    export vLLM_ENDPOINT="http://${ip_address}:${port_number}"
    docker run -d --rm \
        --name="test-comps-vllm-microservice" \
        -p 5030:9000 \
        --ipc=host \
        -e vLLM_ENDPOINT=$vLLM_ENDPOINT \
        -e HUGGINGFACEHUB_API_TOKEN=$HUGGINGFACEHUB_API_TOKEN \
        -e LLM_MODEL=$LLM_MODEL \
        opea/llm-vllm:comps

    # check whether vllm ray is fully ready
    n=0
    until [[ "$n" -ge 120 ]] || [[ $ready == true ]]; do
        docker logs test-comps-vllm-service > ${WORKPATH}/tests/test-comps-vllm-service.log
        n=$((n+1))
        if grep -q throughput ${WORKPATH}/tests/test-comps-vllm-service.log; then
            break
        fi
        sleep 5s
    done
    sleep 5s
}

function validate_microservice() {
    result=$(http_proxy="" curl http://${ip_address}:5025/v1/completions \
        -H "Content-Type: application/json" \
        -d '{
        "model": "Intel/neural-chat-7b-v3-3",
        "prompt": "What is Deep Learning?",
        "max_tokens": 32,
        "temperature": 0
        }')
    if [[ $result == *"text"* ]]; then
        echo "Result correct."
    else
        echo "Result wrong. Received was $result"
        docker logs test-comps-vllm-service
        docker logs test-comps-vllm-microservice
        exit 1
    fi
    result=$(http_proxy="" curl http://${ip_address}:5030/v1/chat/completions \
        -X POST \
        -d '{"query":"What is Deep Learning?","max_tokens":17,"top_p":1,"temperature":0.7,"frequency_penalty":0,"presence_penalty":0, "streaming":false}' \
        -H 'Content-Type: application/json')
    if [[ $result == *"text"* ]]; then
        echo "Result correct."
    else
        echo "Result wrong. Received was $result"
        docker logs test-comps-vllm-service
        docker logs test-comps-vllm-microservice
        exit 1
    fi
}

function stop_docker() {
    cid=$(docker ps -aq --filter "name=test-comps-vllm*")
    if [[ ! -z "$cid" ]]; then docker rm $cid -f && sleep 1s; fi
}

function main() {

    stop_docker

    build_docker_images
    start_service

    validate_microservice

    stop_docker
    echo y | docker system prune

}

main
