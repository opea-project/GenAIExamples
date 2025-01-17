#!/bin/bash
# Copyright (C) 2024 Intel Corporation
# SPDX-License-Identifier: Apache-2.0

set -x

WORKPATH=$(dirname "$PWD")
LOG_PATH="$WORKPATH/tests"
ip_address=$(hostname -I | awk '{print $1}')

function build_docker_images() {
    cd $WORKPATH
    docker build --no-cache --build-arg https_proxy=$https_proxy --build-arg http_proxy=$http_proxy -t opea/llm:comps -f comps/llms/src/text-generation/Dockerfile .
    if [ $? -ne 0 ]; then
        echo "opea/llm built fail"
        exit 1
    else
        echo "opea/llm built successful"
    fi
}

function start_service() {
    tgi_endpoint_port=5004
    export hf_llm_model=$1
    # Remember to set HF_TOKEN before invoking this test!
    export HF_TOKEN=${HF_TOKEN}
    docker run -d --name="test-comps-llm-tgi-endpoint" -p $tgi_endpoint_port:80 -v ~/.cache/huggingface/hub:/data --shm-size 1g -e HF_TOKEN=${HF_TOKEN} ghcr.io/huggingface/text-generation-inference:2.1.0 --model-id ${hf_llm_model} --max-input-tokens 1024 --max-total-tokens 2048
    export LLM_ENDPOINT="http://${ip_address}:${tgi_endpoint_port}"

    # check whether tgi is fully ready
    n=0
    until [[ "$n" -ge 100 ]] || [[ $ready == true ]]; do
        docker logs test-comps-llm-tgi-endpoint >> ${LOG_PATH}/test-comps-vllm-service.log
        n=$((n+1))
        if grep -q Connected ${LOG_PATH}/test-comps-vllm-service.log; then
            break
        fi
        sleep 5s
    done
    sleep 5s

    llm_port=5005
    unset http_proxy
    docker run -d --name="test-comps-llm-tgi-server" -p ${llm_port}:9000 --ipc=host -e LOGFLAG=True -e http_proxy=$http_proxy -e https_proxy=$https_proxy -e LLM_ENDPOINT=$LLM_ENDPOINT -e LLM_MODEL_ID=$hf_llm_model -e HUGGINGFACEHUB_API_TOKEN=$HF_TOKEN opea/llm:comps
    sleep 20s
}

function validate_microservice() {
    llm_port=5005

    result=$(http_proxy="" curl http://${ip_address}:${llm_port}/v1/chat/completions \
        -X POST \
        -d '{"model": "Intel/neural-chat-7b-v3-3", "messages": [{"role": "user", "content": "What is Deep Learning?"}], "max_tokens":17, "stream":false}' \
        -H 'Content-Type: application/json')
    if [[ $result == *"content"* ]]; then
        echo "Result correct."
    else
        echo "Result wrong. Received was $result"
        docker logs test-comps-llm-tgi-endpoint >> ${LOG_PATH}/llm-tgi.log
        docker logs test-comps-llm-tgi-server >> ${LOG_PATH}/llm-server.log
        exit 1
    fi
}

function validate_microservice_with_openai() {
    llm_service_port=5005
    python3 ${WORKPATH}/tests/utils/validate_svc_with_openai.py "$ip_address" "$llm_service_port" "llm"
    if [ $? -ne 0 ]; then
        docker logs test-comps-llm-tgi-endpoint >> ${LOG_PATH}/llm-tgi.log
        docker logs test-comps-llm-tgi-server >> ${LOG_PATH}/llm-server.log
        exit 1
    fi
}

function stop_docker() {
    cid=$(docker ps -aq --filter "name=test-comps-llm-tgi*")
    if [[ ! -z "$cid" ]]; then docker stop $cid && docker rm $cid && sleep 1s; fi
}

function main() {

    stop_docker
    build_docker_images

    pip install --no-cache-dir openai

    llm_models=(
    Intel/neural-chat-7b-v3-3
    # meta-llama/Llama-2-7b-chat-hf
    # meta-llama/Meta-Llama-3-8B-Instruct
    # microsoft/Phi-3-mini-4k-instruct
    )
    for model in "${llm_models[@]}"; do
      start_service "${model}"
      validate_microservice
      validate_microservice_with_openai
      stop_docker
    done

    echo y | docker system prune

}

main
