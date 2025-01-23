# Copyright (C) 2024 Intel Corporation
# SPDX-License-Identifier: Apache-2.0

set -x
IMAGE_REPO=${IMAGE_REPO:-"opea"}
IMAGE_TAG=${IMAGE_TAG:-"latest"}
echo "REGISTRY=IMAGE_REPO=${IMAGE_REPO}"
echo "TAG=IMAGE_TAG=${IMAGE_TAG}"
export REGISTRY=${IMAGE_REPO}
export TAG=${IMAGE_TAG}

WORKPATH=$(dirname "$PWD")
LOG_PATH="$WORKPATH/tests"
ip_address=$(hostname -I | awk '{print $1}')
text2image_service_port=9379
MODEL=stabilityai/stable-diffusion-2-1
export MODEL=${MODEL}

function build_docker_images() {
    cd $WORKPATH/docker_image_build
    if [ ! -d "GenAIComps" ] ; then
        git clone --depth 1 --branch ${opea_branch:-"main"} https://github.com/opea-project/GenAIComps.git
    fi
    service_list="text2image-gaudi text2image-ui nginx"
    docker compose -f build.yaml build ${service_list} --no-cache > ${LOG_PATH}/docker_image_build.log
}

function start_service() {
    cd $WORKPATH/docker_compose/intel/hpu/gaudi
    export no_proxy="localhost,127.0.0.1,"${ip_address}
    # Start Docker Containers
    docker compose -f compose.yaml up -d > ${LOG_PATH}/start_services_with_compose.log
    sleep 30s
}

function validate_microservice() {
    cd $LOG_PATH
    export no_proxy="localhost,127.0.0.1,"${ip_address}

    # test /v1/text2image generate image
    URL="http://${ip_address}:$text2image_service_port/v1/text2image"
    HTTP_RESPONSE=$(curl --silent --write-out "HTTPSTATUS:%{http_code}" -X POST -d '{"prompt":"An astronaut riding a green horse", "num_images_per_prompt":1}' -H 'Content-Type: application/json' "$URL")
    HTTP_STATUS=$(echo $HTTP_RESPONSE | tr -d '\n' | sed -e 's/.*HTTPSTATUS://')
    RESPONSE_BODY=$(echo $HTTP_RESPONSE | sed -e 's/HTTPSTATUS\:.*//g')
    SERVICE_NAME="text2image-gaudi-server - generate image"

    if [ "$HTTP_STATUS" -ne "200" ]; then
        echo "[ $SERVICE_NAME ] HTTP status is not 200. Received status was $HTTP_STATUS"
        docker logs text2image-gaudi-server >> ${LOG_PATH}/text2image-gaudi-server_generate_image.log
        exit 1
    else
        echo "[ $SERVICE_NAME ] HTTP status is 200. Checking content..."
    fi
    # Check if the parsed values match the expected values
    if [[ $RESPONSE_BODY == *"images"* ]]; then
        echo "Content correct."
    else
        echo "Content wrong."
        docker logs text2image-gaudi-server >> ${LOG_PATH}/text2image-gaudi-server_generate_image.log
        exit 1
    fi
}

function stop_docker() {
    cd $WORKPATH/docker_compose/intel/hpu/gaudi
    docker compose -f compose.yaml down
}

function main() {

    stop_docker

    build_docker_images
    start_service

    validate_microservice

    stop_docker
    echo y | docker system prune

}

main
