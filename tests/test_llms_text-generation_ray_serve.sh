#!/bin/bash
# Copyright (C) 2024 Intel Corporation
# SPDX-License-Identifier: Apache-2.0

set -xe

WORKPATH=$(dirname "$PWD")
ip_address=$(hostname -I | awk '{print $1}')

function build_docker_images() {
    ## Build VLLM Ray docker
    cd $WORKPATH/comps/llms/text-generation/ray_serve/docker
    docker build \
        -f Dockerfile.rayserve ../../ \
        --network=host \
        -t ray_serve:habana

    ## Build OPEA microservice docker
    cd $WORKPATH
    docker build  \
        -t opea/llm-ray:comps \
        -f comps/llms/text-generation/ray_serve/docker/Dockerfile.microservice .
}

function start_service() {
    export LLM_MODEL="facebook/opt-125m"
    port_number=8008

    docker run -d --rm \
        --runtime=habana \
        --name="test-comps-ray-service" \
        -v $PWD/data:/data \
        -e HABANA_VISIBLE_DEVICES=all \
        -e OMPI_MCA_btl_vader_single_copy_mechanism=none \
        --cap-add=sys_nice \
        --ipc=host \
        -p $port_number:80 \
        -e HF_TOKEN=${HUGGINGFACEHUB_API_TOKEN} \
        -e TRUST_REMOTE_CODE=True \
        ray_serve:habana \
        /bin/bash -c "ray start --head && python api_server_openai.py --port_number 80 --model_id_or_path $LLM_MODEL --chat_processor ChatModelLlama --num_cpus_per_worker 8 --num_hpus_per_worker 1"

    export RAY_Serve_ENDPOINT="http://${ip_address}:${port_number}"
    docker run -d --rm \
        --name="test-comps-ray-microserve" \
        -p 9000:9000 \
        --ipc=host \
        -e RAY_Serve_ENDPOINT=$RAY_Serve_ENDPOINT \
        -e HUGGINGFACEHUB_API_TOKEN=$HUGGINGFACEHUB_API_TOKEN \
        -e LLM_MODEL=$LLM_MODEL \
        opea/llm-ray:comps

    # check whether ray is fully ready
    n=0
    until [[ "$n" -ge 100 ]] || [[ $ready == true ]]; do
        docker logs test-comps-ray-service > ${WORKPATH}/tests/test-comps-ray-service.log
        n=$((n+1))
        if grep -q Connected ${WORKPATH}/tests/test-comps-ray-service.log; then
            break
        fi
        sleep 5s
    done
    sleep 5s
}

function validate_microservice() {
    http_proxy="" curl http://${ip_address}:8008/v1/chat/completions   \
        -H "Content-Type: application/json"   \
        -d '{"model": "opt-125m", "messages": [{"role": "user", "content": "What is Deep Learning?"}], "max_tokens": 32 }'
    http_proxy="" curl http://${ip_address}:9000/v1/chat/completions \
        -X POST \
        -d '{"query":"What is Deep Learning?","max_new_tokens":17,"top_k":10,"top_p":0.95,"typical_p":0.95,"temperature":0.01,"repetition_penalty":1.03,"streaming":false}' \
        -H 'Content-Type: application/json'
    docker logs test-comps-ray-service
    docker logs test-comps-ray-microserve
        }


function stop_docker() {
    cid=$(docker ps -aq --filter "name=test-comps-ray*")
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
