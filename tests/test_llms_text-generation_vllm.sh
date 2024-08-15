#!/bin/bash
# Copyright (C) 2024 Intel Corporation
# SPDX-License-Identifier: Apache-2.0

set -x

WORKPATH=$(dirname "$PWD")
ip_address=$(hostname -I | awk '{print $1}')

function build_docker_images() {
    ## Build VLLM Ray docker
    cd $WORKPATH/comps/llms/text-generation/vllm
    docker build \
        -f docker/Dockerfile.hpu \
        -t opea/vllm-hpu:comps \
        --shm-size=128g .
    if $? ; then
        echo "opea/vllm-hpu built fail"
        exit 1
    else
        echo "opea/vllm-hpu built successful"
    fi

    ## Build OPEA microservice docker
    cd $WORKPATH
    docker build  \
        -t opea/llm-vllm:comps \
        -f comps/llms/text-generation/vllm/docker/Dockerfile.microservice .
    if $? ; then
        echo "opea/llm-vllm built fail"
        exit 1
    else
        echo "opea/llm-vllm built successful"
    fi
}

function start_service() {
    export LLM_MODEL="facebook/opt-125m"
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
        opea/vllm-hpu:comps \
        /bin/bash -c "export VLLM_CPU_KVCACHE_SPACE=40 && python3 -m vllm.entrypoints.openai.api_server --enforce-eager --model $LLM_MODEL  --tensor-parallel-size 1 --host 0.0.0.0 --port 80 --block-size 128 --max-num-seqs 256 --max-seq_len-to-capture 2048"

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
        if grep -q Connected ${WORKPATH}/tests/test-comps-vllm-service.log; then
            break
        fi
        sleep 5s
    done
    sleep 5s
}

function validate_microservice() {
    result=$(http_proxy="" curl http://${ip_address}:8008/v1/completions \
        -H "Content-Type: application/json" \
        -d '{
        "model": "facebook/opt-125m",
        "prompt": "What is Deep Learning?",
        "max_tokens": 32,
        "temperature": 0
        }')
    result_2=$(http_proxy="" curl http://${ip_address}:5030/v1/chat/completions \
        -X POST \
        -d '{"query":"What is Deep Learning?","max_new_tokens":17,"top_p":0.95,"temperature":0.01,"streaming":false}' \
        -H 'Content-Type: application/json')
            docker logs test-comps-vllm-service
            docker logs test-comps-vllm-microservice
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
    # echo y | docker system prune

}

main
