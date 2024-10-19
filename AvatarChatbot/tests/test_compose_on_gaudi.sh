#!/bin/bash
# Copyright (C) 2024 Intel Corporation
# SPDX-License-Identifier: Apache-2.0

set -e
echo "IMAGE_REPO=${IMAGE_REPO}"

WORKPATH=$(dirname "$PWD")
LOG_PATH="$WORKPATH/tests"
if ls $LOG_PATH/*.log 1> /dev/null 2>&1; then
    rm $LOG_PATH/*.log
    echo "Log files removed."
else
    echo "No log files to remove."
fi
ip_address=$(hostname -I | awk '{print $1}')


function build_docker_images() {
    cd $WORKPATH
    git clone https://github.com/opea-project/GenAIComps.git
    cd GenAIComps

    docker build -t opea/whisper-gaudi:latest --build-arg https_proxy=$https_proxy --build-arg http_proxy=$http_proxy -f comps/asr/whisper/dependency/Dockerfile.intel_hpu .
    docker build -t opea/asr:latest --build-arg https_proxy=$https_proxy --build-arg http_proxy=$http_proxy -f comps/asr/whisper/Dockerfile .
    docker build --no-cache -t opea/llm-tgi:latest --build-arg https_proxy=$https_proxy --build-arg http_proxy=$http_proxy -f comps/llms/text-generation/tgi/Dockerfile .
    docker build -t opea/speecht5-gaudi:latest --build-arg https_proxy=$https_proxy --build-arg http_proxy=$http_proxy -f comps/tts/speecht5/dependency/Dockerfile.intel_hpu .
    docker build -t opea/tts:latest --build-arg https_proxy=$https_proxy --build-arg http_proxy=$http_proxy -f comps/tts/speecht5/Dockerfile .
    docker build -t opea/wav2lip-gaudi:latest --build-arg https_proxy=$https_proxy --build-arg http_proxy=$http_proxy -f comps/animation/wav2lip/dependency/Dockerfile.intel_hpu .
    docker build -t opea/animation:latest --build-arg https_proxy=$https_proxy --build-arg http_proxy=$http_proxy -f comps/animation/wav2lip/Dockerfile .

    cd ..
    git clone https://github.com/opea-project/GenAIExamples.git
    cd GenAIExamples/AvatarChatbot/

    docker build --no-cache -t opea/avatarchatbot:latest --build-arg https_proxy=$https_proxy --build-arg http_proxy=$http_proxy -f Dockerfile .

    docker images
}


function start_services() {
    cd $WORKPATH/docker_compose/intel/hpu/gaudi

    export HUGGINGFACEHUB_API_TOKEN=$HUGGINGFACEHUB_API_TOKEN
    export host_ip=$(hostname -I | awk '{print $1}')

    export TGI_LLM_ENDPOINT=http://$host_ip:3006
    export LLM_MODEL_ID=Intel/neural-chat-7b-v3-3

    export ASR_ENDPOINT=http://$host_ip:7066
    export TTS_ENDPOINT=http://$host_ip:7055
    export WAV2LIP_ENDPOINT=http://$host_ip:7860

    export MEGA_SERVICE_HOST_IP=${host_ip}
    export ASR_SERVICE_HOST_IP=${host_ip}
    export TTS_SERVICE_HOST_IP=${host_ip}
    export LLM_SERVICE_HOST_IP=${host_ip}
    export ANIMATION_SERVICE_HOST_IP=${host_ip}

    export MEGA_SERVICE_PORT=8888
    export ASR_SERVICE_PORT=3001
    export TTS_SERVICE_PORT=3002
    export LLM_SERVICE_PORT=3007
    export ANIMATION_SERVICE_PORT=3008

    export DEVICE="hpu"
    export WAV2LIP_PORT=7860
    export INFERENCE_MODE='wav2lip+gfpgan'
    export CHECKPOINT_PATH='/usr/local/lib/python3.10/dist-packages/Wav2Lip/checkpoints/wav2lip_gan.pth'
    export FACE="assets/img/avatar5.png"
    # export AUDIO='assets/audio/eg3_ref.wav' # audio file path is optional, will use base64str in the post request as input if is 'None'
    export AUDIO='None'
    export FACESIZE=96
    export OUTFILE="/outputs/result.mp4"
    export GFPGAN_MODEL_VERSION=1.4 # latest version, can roll back to v1.3 if needed
    export UPSCALE_FACTOR=1
    export FPS=10

    # Start Docker Containers
    docker compose up -d
    n=0
    until [[ "$n" -ge 500 ]]; do
        # check tgi and whisper services
        docker logs llm-tgi-gaudi-server > $LOG_PATH/llm_tgi_gaudi_server_start.log
        docker logs asr-service > $LOG_PATH/asr_service_start.log

        if grep -q Connected $LOG_PATH/llm_tgi_gaudi_server_start.log && grep -q "initialized" $LOG_PATH/asr_service_start.log; then
            break
        fi
       sleep 1m
       n=$((n+1))
    done
    echo "All services are up and running"
    sleep 5s
}


function validate_megaservice() {
    cd $WORKPATH
    result=$(http_proxy="" curl http://${ip_address}:3009/v1/avatarchatbot -X POST -d @sample_whoareyou.json -H 'Content-Type: application/json')
    echo "result is === $result"
    if [[ $result == *"mp4"* ]]; then
        echo "Result correct."
    else
        docker logs whisper-service > $LOG_PATH/whisper-service.log
        docker logs asr-service > $LOG_PATH/asr-service.log
        docker logs speecht5-service > $LOG_PATH/speecht5-service.log
        docker logs tts-service > $LOG_PATH/tts-service.log
        docker logs tgi-gaudi-server > $LOG_PATH/tgi-gaudi-server.log
        docker logs llm-tgi-gaudi-server > $LOG_PATH/llm-tgi-gaudi-server.log
        docker logs wav2lip-service > $LOG_PATH/wav2lip-service.log
        docker logs animation-gaudi-server > $LOG_PATH/animation-gaudi-server.log

        echo "Result wrong."
        exit 1
    fi

}


#function validate_frontend() {

#}


function stop_docker() {
    cd $WORKPATH/docker_compose/intel/hpu/gaudi
    docker compose down
}


function main() {

    stop_docker
    if [[ "$IMAGE_REPO" == "" ]]; then build_docker_images; fi
    start_services
    validate_microservices
    validate_megaservice
    # validate_frontend
    stop_docker

    echo y | docker builder prune --all
    echo y | docker image prune

}


main
