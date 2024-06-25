#!/bin/bash
# Copyright (C) 2024 Intel Corporation
# SPDX-License-Identifier: Apache-2.0

set -xe

function test_env_setup() {
    WORKPATH=$(dirname "$PWD")/audio/docker
    OUTPUT_PATH=$(dirname "$PWD")/tests/output.wav
    TTS_CONTAINER_NAME="test-audioqna-tts"
    cd $WORKPATH
}

function start_tts_service() {
    cd $WORKPATH
    rm -rf pretrained_tts_models
    git clone https://huggingface.co/lj1995/GPT-SoVITS pretrained_tts_models
    docker build . --build-arg http_proxy=${http_proxy} --build-arg https_proxy=${http_proxy} -f Dockerfile_tts -t intel/gen-ai-examples:$TTS_CONTAINER_NAME
    docker run -d --name=$TTS_CONTAINER_NAME -v ./pretrained_tts_models:/GPT-SoVITS/GPT_SoVITS/pretrained_models -e http_proxy=${http_proxy} -e https_proxy=${https_proxy} -p 9888:9880 intel/gen-ai-examples:$TTS_CONTAINER_NAME --bf16
    sleep 1m
}

function run_tests() {
    cd $WORKPATH
    rm -f ${OUTPUT_PATH}
    rm -f sample.wav

    # Upload reference audio as default voice
    wget https://github.com/intel/intel-extension-for-transformers/raw/main/intel_extension_for_transformers/neural_chat/assets/audio/sample.wav
    curl --location 'localhost:9888/upload_as_default' \
    --form 'default_refer_file=@"sample.wav"' \
    --form 'default_refer_text="Who is Pat Gelsinger?"' \
    --form 'default_refer_language="en"'

    # Do text to speech conversion
    curl --location 'localhost:9888/v1/audio/speech' \
    --header 'Content-Type: application/json' \
    --data '{
        "text": "You can have a look, but you should not touch this item.",
        "text_language": "en"
    }' \
    --output ${OUTPUT_PATH}
    rm -f sample.wav
}

function check_response() {
    cd $WORKPATH
    echo "Checking response"
    local status=false

    if [[ -f $OUTPUT_PATH ]]; then
        status=true
    fi

    if [ $status == false ]; then
        echo "Response check failed"
        exit 1
    else
        echo "Response check succeed"
    fi

    # clear resources
    rm -f ${OUTPUT_PATH}
}

function docker_stop() {
    local container_name=$1
    cid=$(docker ps -aq --filter "name=$container_name")
    if [[ ! -z "$cid" ]]; then docker stop $cid && docker rm $cid; fi
}

function main() {
    test_env_setup
    docker_stop $TTS_CONTAINER_NAME && sleep 5s

    start_tts_service
    run_tests
    check_response

    docker_stop $TTS_CONTAINER_NAME && sleep 5s
    echo y | docker system prune
}

main
