#!/bin/bash
# Copyright (C) 2024 Intel Corporation
# SPDX-License-Identifier: Apache-2.0

set -xe

WORKPATH=$(dirname "$PWD")
ip_address=$(hostname -I | awk '{print $1}')

function build_docker_images() {
    ## Build VLLM Ray docker
    cd $WORKPATH
    docker build \
        -f comps/llms/text-generation/vllm-ray/docker/Dockerfile.vllmray  \
        -t opea/vllm_ray:habana --network=host .

    ## Build OPEA microservice docker
    cd $WORKPATH
    docker build \
        -t opea/llm-vllm-ray:comps \
        -f comps/llms/text-generation/vllm-ray/docker/Dockerfile.microservice .
}

function start_service() {
    export LLM_MODEL="facebook/opt-125m"
    port_number=8006
    docker run -d --rm \
        --name="test-comps-vllm-ray-service" \
        --runtime=habana \
        -v $PWD/data:/data \
        -e HABANA_VISIBLE_DEVICES=all \
        -e OMPI_MCA_btl_vader_single_copy_mechanism=none \
        --cap-add=sys_nice \
        --ipc=host \
        -e HUGGINGFACEHUB_API_TOKEN=$HUGGINGFACEHUB_API_TOKEN \
        -p $port_number:8000 \
        opea/vllm_ray:habana \
        /bin/bash -c "ray start --head && python vllm_ray_openai.py --port_number 8000 --model_id_or_path $LLM_MODEL --tensor_parallel_size 2 --enforce_eager False"

    export vLLM_RAY_ENDPOINT="http://${ip_address}:${port_number}"
    docker run -d --rm\
        --name="test-comps-vllm-ray-microservice" \
        -p 9000:9000 \
        --ipc=host \
        -e vLLM_RAY_ENDPOINT=$vLLM_RAY_ENDPOINT \
        -e HUGGINGFACEHUB_API_TOKEN=$HUGGINGFACEHUB_API_TOKEN \
        -e LLM_MODEL=$LLM_MODEL \
        opea/llm-vllm-ray:comps

    # check whether vllm ray is fully ready
    n=0
    until [[ "$n" -ge 100 ]] || [[ $ready == true ]]; do
        docker logs test-comps-vllm-ray-service > ${WORKPATH}/tests/test-comps-vllm-ray-service.log
        n=$((n+1))
        if grep -q Connected ${WORKPATH}/tests/test-comps-vllm-ray-service.log; then
            break
        fi
        sleep 5s
    done
    sleep 5s
}

function validate_microservice() {
    http_proxy="" curl http://${ip_address}:8006/v1/chat/completions \
        -H "Content-Type: application/json" \
        -d '{"model": "facebook/opt-125m", "messages": [{"role": "user", "content": "How are you?"}]}'
    http_proxy="" curl http://${ip_address}:9000/v1/chat/completions \
        -X POST \
        -d '{"query":"What is Deep Learning?","max_new_tokens":17,"top_k":10,"top_p":0.95,"typical_p":0.95,"temperature":0.01,"repetition_penalty":1.03,"streaming":false}' \
        -H 'Content-Type: application/json'
    docker logs test-comps-vllm-ray-service
    docker logs test-comps-vllm-ray-microservice
}

function stop_docker() {
    cid=$(docker ps -aq --filter "name=test-comps-vllm-ray*")
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
