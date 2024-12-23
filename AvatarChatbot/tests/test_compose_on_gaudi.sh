#!/bin/bash
# Copyright (C) 2024 Intel Corporation
# SPDX-License-Identifier: Apache-2.0

set -e
IMAGE_REPO=${IMAGE_REPO:-"opea"}
IMAGE_TAG=${IMAGE_TAG:-"latest"}
echo "REGISTRY=IMAGE_REPO=${IMAGE_REPO}"
echo "TAG=IMAGE_TAG=${IMAGE_TAG}"
export REGISTRY=${IMAGE_REPO}
export TAG=${IMAGE_TAG}

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
    cd $WORKPATH/docker_image_build
    git clone https://github.com/opea-project/GenAIComps.git && cd GenAIComps && git checkout "${opea_branch:-"main"}" && cd ../

    echo "Build all the images with --no-cache, check docker_image_build.log for details..."
    service_list="avatarchatbot whisper-gaudi asr llm-tgi speecht5-gaudi tts wav2lip-gaudi animation"
    docker compose -f build.yaml build ${service_list} --no-cache > ${LOG_PATH}/docker_image_build.log

    docker pull ghcr.io/huggingface/tgi-gaudi:2.0.6

    docker images && sleep 1s
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
    export FACE="assets/img/avatar1.jpg"
    # export AUDIO='assets/audio/eg3_ref.wav' # audio file path is optional, will use base64str in the post request as input if is 'None'
    export AUDIO='None'
    export FACESIZE=96
    export OUTFILE="/outputs/result.mp4"
    export GFPGAN_MODEL_VERSION=1.4 # latest version, can roll back to v1.3 if needed
    export UPSCALE_FACTOR=1
    export FPS=10

    # Start Docker Containers
    docker compose up -d > ${LOG_PATH}/start_services_with_compose.log

    n=0
    until [[ "$n" -ge 100 ]]; do
       docker logs tgi-gaudi-server > $LOG_PATH/tgi_service_start.log
       if grep -q Connected $LOG_PATH/tgi_service_start.log; then
           break
       fi
       sleep 5s
       n=$((n+1))
    done

    echo "All services are up and running"
    sleep 5s
}


function validate_megaservice() {
    cd $WORKPATH
    result=$(http_proxy="" curl http://${ip_address}:3009/v1/avatarchatbot -X POST -d @assets/audio/sample_whoareyou.json -H 'Content-Type: application/json')
    echo "result is === $result"
    if [[ $result == *"mp4"* ]]; then
        echo "Result correct."
    else
        echo "Result wrong, print docker logs."
        docker logs whisper-service > $LOG_PATH/whisper-service.log
        docker logs asr-service > $LOG_PATH/asr-service.log
        docker logs speecht5-service > $LOG_PATH/speecht5-service.log
        docker logs tts-service > $LOG_PATH/tts-service.log
        docker logs tgi-gaudi-server > $LOG_PATH/tgi-gaudi-server.log
        docker logs llm-tgi-gaudi-server > $LOG_PATH/llm-tgi-gaudi-server.log
        docker logs wav2lip-service > $LOG_PATH/wav2lip-service.log
        docker logs animation-gaudi-server > $LOG_PATH/animation-gaudi-server.log
        echo "Exit test."
        exit 1
    fi

}


function stop_docker() {
    cd $WORKPATH/docker_compose/intel/hpu/gaudi
    docker compose down
}


function main() {
    stop_docker
    echo y | docker builder prune --all
    echo y | docker image prune

    if [[ "$IMAGE_REPO" == "opea" ]]; then build_docker_images; fi
    start_services
    # validate_microservices
    validate_megaservice
    # validate_frontend

    stop_docker
    echo y | docker builder prune --all
    echo y | docker image prune

}


main
