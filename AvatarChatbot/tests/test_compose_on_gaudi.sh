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
export MODEL_CACHE=${model_cache:-"./data"}

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
    opea_branch=${opea_branch:-"main"}

    cd $WORKPATH/docker_image_build
    git clone --depth 1 --branch ${opea_branch} https://github.com/opea-project/GenAIComps.git
    pushd GenAIComps
    echo "GenAIComps test commit is $(git rev-parse HEAD)"
    docker build --no-cache -t ${REGISTRY}/comps-base:${TAG} --build-arg https_proxy=$https_proxy --build-arg http_proxy=$http_proxy -f Dockerfile .
    popd && sleep 1s

    echo "Build all the images with --no-cache, check docker_image_build.log for details..."
    service_list="avatarchatbot whisper-gaudi speecht5-gaudi wav2lip-gaudi animation"
    docker compose -f build.yaml build ${service_list} --no-cache > ${LOG_PATH}/docker_image_build.log

    docker pull ghcr.io/huggingface/tgi-gaudi:2.0.6

    docker images && sleep 1s
}


function start_services() {
    cd $WORKPATH/docker_compose/intel/hpu/gaudi

    source set_env.sh

    # Start Docker Containers
    docker compose up -d > ${LOG_PATH}/start_services_with_compose.log
    n=0
    until [[ "$n" -ge 200 ]]; do
       docker logs tgi-gaudi-server > $LOG_PATH/tgi_service_start.log && docker logs whisper-service 2>&1 | tee $LOG_PATH/whisper_service_start.log && docker logs speecht5-service 2>&1 | tee $LOG_PATH/speecht5_service_start.log
       if grep -q Connected $LOG_PATH/tgi_service_start.log && grep -q running $LOG_PATH/whisper_service_start.log && grep -q running $LOG_PATH/speecht5_service_start.log; then
           break
       fi
       sleep 10s
       n=$((n+1))
    done
    echo "All services are up and running"
    # sleep 5s
    sleep 1m
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
        docker logs speecht5-service > $LOG_PATH/speecht5-service.log
        docker logs tgi-gaudi-server > $LOG_PATH/tgi-gaudi-server.log
        docker logs wav2lip-service > $LOG_PATH/wav2lip-service.log
        docker logs animation-gaudi-server > $LOG_PATH/animation-gaudi-server.log

        echo "Result wrong."
        exit 1
    fi

}


function stop_docker() {
    cd $WORKPATH/docker_compose/intel/hpu/gaudi
    docker compose down
}


function main() {
    echo "::group::stop_docker"
    stop_docker
    echo "::endgroup::"
    docker builder prune --all -f
    docker image prune -f

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
    docker builder prune --all -f
    docker image prune -f

}


main
