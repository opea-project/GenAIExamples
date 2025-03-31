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
    service_list="avatarchatbot whisper asr llm-textgen speecht5 tts wav2lip animation"
    docker compose -f build.yaml build ${service_list} --no-cache > ${LOG_PATH}/docker_image_build.log

    docker pull ghcr.io/huggingface/text-generation-inference:2.3.1-rocm

    docker images && sleep 3s
}


function start_services() {
    cd $WORKPATH/docker_compose/amd/gpu/rocm

    export HUGGINGFACEHUB_API_TOKEN=$HUGGINGFACEHUB_API_TOKEN
    export OPENAI_API_KEY=$OPENAI_API_KEY
    export host_ip=${ip_address}

    export TGI_SERVICE_PORT=3006
    export TGI_LLM_ENDPOINT=http://${host_ip}:${TGI_SERVICE_PORT}
    export LLM_MODEL_ID="Intel/neural-chat-7b-v3-3"

    export ASR_ENDPOINT=http://${host_ip}:7066
    export TTS_ENDPOINT=http://${host_ip}:7055
    export WAV2LIP_ENDPOINT=http://${host_ip}:7860

    export MEGA_SERVICE_HOST_IP=${host_ip}
    export ASR_SERVICE_HOST_IP=${host_ip}
    export TTS_SERVICE_HOST_IP=${host_ip}
    export LLM_SERVICE_HOST_IP=${host_ip}
    export ANIMATION_SERVICE_HOST_IP=${host_ip}
    export WHISPER_SERVER_HOST_IP=${host_ip}
    export WHISPER_SERVER_PORT=7066

    export SPEECHT5_SERVER_HOST_IP=${host_ip}
    export SPEECHT5_SERVER_PORT=7055

    export MEGA_SERVICE_PORT=8888
    export ASR_SERVICE_PORT=3001
    export TTS_SERVICE_PORT=3002
    export LLM_SERVICE_PORT=3007
    export ANIMATION_SERVICE_PORT=3008

    export DEVICE="cpu"
    export WAV2LIP_PORT=7860
    export INFERENCE_MODE='wav2lip+gfpgan'
    export CHECKPOINT_PATH='/usr/local/lib/python3.11/site-packages/Wav2Lip/checkpoints/wav2lip_gan.pth'
    export FACE="/home/user/comps/animation/src/assets/img/avatar5.png"
    # export AUDIO='assets/audio/eg3_ref.wav' # audio file path is optional, will use base64str in the post request as input if is 'None'
    export AUDIO='None'
    export FACESIZE=96
    export OUTFILE="./outputs/result.mp4"
    export GFPGAN_MODEL_VERSION=1.4 # latest version, can roll back to v1.3 if needed
    export UPSCALE_FACTOR=1
    export FPS=5

    # Start Docker Containers
    docker compose up -d --force-recreate

    echo "Check tgi-service status"

    n=0
    until [[ "$n" -ge 100 ]]; do
       docker logs tgi-service > $LOG_PATH/tgi_service_start.log
       if grep -q Connected $LOG_PATH/tgi_service_start.log; then
           break
       fi
       sleep 5s
       n=$((n+1))
    done
    echo "tgi-service are up and running"
    sleep 5s

    echo "Check wav2lip-service status"

    n=0
    until [[ "$n" -ge 100 ]]; do
       docker logs wav2lip-service >& $LOG_PATH/wav2lip-service_start.log
       if grep -q "Application startup complete" $LOG_PATH/wav2lip-service_start.log; then
           break
       fi
       sleep 5s
       n=$((n+1))
    done
    echo "wav2lip-service are up and running"
    sleep 5s
}


function validate_megaservice() {
    cd $WORKPATH
    ls
    result=$(http_proxy="" curl http://${ip_address}:3009/v1/avatarchatbot -X POST -d @assets/audio/sample_whoareyou.json -H 'Content-Type: application/json')
    echo "result is === $result"
    if [[ $result == *"mp4"* ]]; then
        echo "Result correct."
    else
        docker logs whisper-service > $LOG_PATH/whisper-service.log
        docker logs asr-service > $LOG_PATH/asr-service.log
        docker logs speecht5-service > $LOG_PATH/speecht5-service.log
        docker logs tts-service > $LOG_PATH/tts-service.log
        docker logs tgi-service > $LOG_PATH/tgi-service.log
        docker logs llm-tgi-server > $LOG_PATH/llm-tgi-server.log
        docker logs wav2lip-service > $LOG_PATH/wav2lip-service.log
        docker logs animation-server > $LOG_PATH/animation-server.log

        echo "Result wrong."
        exit 1
    fi

}


#function validate_frontend() {

#}


function stop_docker() {
    cd $WORKPATH/docker_compose/amd/gpu/rocm
    docker compose down && docker compose rm -f
}


function main() {

    echo $OPENAI_API_KEY
    echo $OPENAI_KEY

    stop_docker
    if [[ "$IMAGE_REPO" == "opea" ]]; then build_docker_images; fi
    start_services
    # validate_microservices
    sleep 30
    validate_megaservice
    # validate_frontend
    stop_docker

    echo y | docker system prune

}


main
