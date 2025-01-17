#!/usr/bin/env bash
# Copyright (C) 2025 Intel Corporation
# SPDX-License-Identifier: Apache-2.0

set -x

WORKPATH=$(dirname "$PWD")
ip_address=$(hostname -I | awk '{print $1}')

function build_docker_images() {
    echo "Start building docker images for microservice"
    cd $WORKPATH
    docker build --no-cache -t opea/guardrails-hallucination-detection:comps --build-arg https_proxy=$https_proxy --build-arg http_proxy=$http_proxy -f comps/guardrails/src/hallucination_detection/Dockerfile .
    if [ $? -ne 0 ]; then
        echo "opea/guardrails-hallucination-detection built fail"
        exit 1
    else
        echo "opea/guardrails-hallucination-detection built successful"
    fi
}

function start_service() {
    export your_ip=$(hostname -I | awk '{print $1}')
    export port_number=9008
    export vLLM_ENDPOINT="http://${your_ip}:${port_number}"
    export LLM_MODEL="PatronusAI/Llama-3-Patronus-Lynx-8B-Instruct"

    echo "Starting vllm serving"
    docker run -d --runtime=habana \
        --name="test-comps-guardrails-hallucination-detection-vllm-service" \
        -v $PWD/data:/data \
        -p $port_number:80 \
        -e HABANA_VISIBLE_DEVICES=all \
        -e OMPI_MCA_btl_vader_single_copy_mechanism=none \
        --cap-add=sys_nice \
        --ipc=host \
        -e HTTPS_PROXY=$https_proxy \
        -e HTTP_PROXY=$https_proxy \
        -e HF_TOKEN=${HF_TOKEN} \
        opea/vllm-gaudi:latest \
        --model $LLM_MODEL \
        --tensor-parallel-size 1 \
        --host 0.0.0.0 \
        --port 80 \
        --block-size 128 \
        --max-num-seqs  256\
        --max-seq-len-to-capture 2048 \
        --trust-remote-code
    until curl -s http://localhost:$port_number/health > /dev/null; do
        echo "Waiting for vllm serving to start..."
        sleep 2m
    done
    echo "vllm serving started"

    echo "Starting microservice"
    docker run -d --runtime=runc \
        --name="test-comps-guardrails-hallucination-detection-uservice" \
        -p 9080:9000 \
        --ipc=host \
        -e http_proxy=$http_proxy \
        -e https_proxy=$https_proxy \
        -e vLLM_ENDPOINT=$vLLM_ENDPOINT \
        -e HUGGINGFACEHUB_API_TOKEN=$HUGGINGFACEHUB_API_TOKEN \
        -e LLM_MODEL=$LLM_MODEL \
        -e LOGFLAG=$LOGFLAG \
        opea/guardrails-hallucination-detection:comps
    sleep 10
    echo "Microservice started"
}

function validate_microservice() {
    echo "Validate microservice started"
    DATA='{"messages":[{"role": "user", "content": "Given the following QUESTION, DOCUMENT and ANSWER you must analyze the provided answer and determine whether it is faithful to the contents of the DOCUMENT. The ANSWER must not offer new information beyond the context provided in the DOCUMENT. The ANSWER also must not contradict information provided in the DOCUMENT. Output your final verdict by strictly following this format: \"PASS\" is the answer is faithful to the DOCUMENT and \"FAIL\" if the answer is not faithful to the DOCUMENT. Show your reasoning.\n\n--\nQUESTION (THIS DOES NOT COUNT AS BACKGROUND INFORMATION):\n{question}\n\n--\nDOCUMENT:\n{document}\n\n--\nANSWER:\n{answer}\n\n--\n\n Your output should be in JSON FORMAT with the keys \"REASONING\" and \"SCORE\":\n{{\"REASONING\": <your reasoning as bullet points>, \"SCORE\": <your final score>}}"}], "max_tokens":600,"model": "PatronusAI/Llama-3-Patronus-Lynx-8B-Instruct" }'

    echo "test 1 - Case with Hallucination (Invalid or Inconsistent Output)"
    DOCUMENT="750 Seventh Avenue is a 615 ft (187m) tall Class-A office skyscraper in New York City. 101 Park Avenue is a 629 ft tall skyscraper in New York City, New York."
    QUESTION=" 750 7th Avenue and 101 Park Avenue, are located in which city?"
    ANSWER="750 7th Avenue and 101 Park Avenue are located in Albany, New York"

    DATA1=$(echo $DATA | sed "s/{question}/$QUESTION/g; s/{document}/$DOCUMENT/g; s/{answer}/$ANSWER/g")
    printf "$DATA1\n"

    result=$(curl localhost:9080/v1/hallucination_detection -X POST -d "$DATA1" -H 'Content-Type: application/json')
    if [[ $result == *"FAIL"* ]]; then
        echo "Result correct."
    else
        docker logs test-comps-guardrails-hallucination-detection-uservice
        exit 1
    fi

    echo "test 2 - Case without Hallucination (Valid Output)"
    DOCUMENT=".......An important part of CDC’s role during a public health emergency is to develop a test for the pathogen and equip state and local public health labs with testing capacity. CDC developed an rRT-PCR test to diagnose COVID-19. As of the evening of March 17, 89 state and local public health labs in 50 states......"
    QUESTION="What kind of test can diagnose COVID-19?"
    ANSWER=" rRT-PCR test"

    DATA2=$(echo $DATA | sed "s/{question}/$QUESTION/g; s/{document}/$DOCUMENT/g; s/{answer}/$ANSWER/g")
    printf "$DATA2\n"

    result=$(curl localhost:9080/v1/hallucination_detection -X POST -d "$DATA2" -H 'Content-Type: application/json')
    if [[ $result == *"PASS"* ]]; then
        echo "Result correct."
    else
        echo "Result wrong."
        docker logs test-comps-guardrails-hallucination-detection-uservice
        exit 1
    fi
    echo "Validate microservice completed"
}

function stop_docker() {
    cid=$(docker ps -aq --filter "name=test-comps-guardrails-hallucination-detection*")
    echo "Shutdown legacy containers "$cid
    if [[ ! -z "$cid" ]]; then docker stop $cid && docker rm $cid && sleep 1s; fi
}

function main() {

    stop_docker

    build_docker_images
    start_service

    validate_microservice

    stop_docker
    echo "cleanup container images and volumes"
    echo y | docker system prune 2>&1 > /dev/null

}

main
