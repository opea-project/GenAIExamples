#!/bin/bash
# Copyright (C) 2024 Intel Corporation
# SPDX-License-Identifier: Apache-2.0

set -xe
IMAGE_REPO=${IMAGE_REPO:-"opea"}
IMAGE_TAG=${IMAGE_TAG:-"latest"}
echo "REGISTRY=IMAGE_REPO=${IMAGE_REPO}"
echo "TAG=IMAGE_TAG=${IMAGE_TAG}"
export REGISTRY=${IMAGE_REPO}
export TAG=${IMAGE_TAG}
export MODEL_CACHE=${model_cache:-"/var/lib/GenAI/data"}

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
    pushd GenAIComps
    echo "GenAIComps test commit is $(git rev-parse HEAD)"
    docker build --no-cache -t ${REGISTRY}/comps-base:${TAG} --build-arg https_proxy=$https_proxy --build-arg http_proxy=$http_proxy -f Dockerfile .
    popd && sleep 1s

    echo "Build all the images with --no-cache, check docker_image_build.log for details..."
    service_list="avatarchatbot whisper asr speecht5 tts wav2lip animation"
    docker compose -f build.yaml build ${service_list} --no-cache > ${LOG_PATH}/docker_image_build.log

    docker pull ghcr.io/huggingface/text-generation-inference:2.3.1-rocm

    docker images && sleep 3s
}


function start_services() {
    cd $WORKPATH/docker_compose/amd/gpu/rocm
    export OPENAI_API_KEY=$OPENAI_API_KEY
    source set_env.sh

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


function stop_docker() {
    cd $WORKPATH/docker_compose/amd/gpu/rocm
    docker compose down && docker compose rm -f
}


function main() {

    echo "::group::stop_docker"
    stop_docker
    echo "::endgroup::"

    echo "::group::build_docker_images"
    if [[ "$IMAGE_REPO" == "opea" ]]; then build_docker_images; fi
    echo "::endgroup::"

    echo "::group::start_services"
    start_services
    echo "::endgroup::"

    echo "::group::validate_megaservice"
    validate_megaservice
    echo "::endgroup::"

    echo "::group::stop_docker"
    stop_docker
    echo "::endgroup::"

    docker system prune -f

}


main
