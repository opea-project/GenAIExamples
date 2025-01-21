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

function build_docker_images() {
    cd $WORKPATH/docker_image_build
    if [ ! -d "GenAIComps" ] ; then
        git clone --depth 1 --branch ${opea_branch:-"main"} https://github.com/opea-project/GenAIComps.git
    fi
    docker compose -f build.yaml build --no-cache > ${LOG_PATH}/docker_image_build.log
}

function start_service() {
    export no_proxy="localhost,127.0.0.1,"${ip_address}
    docker run -d --name="text2image-server" -p $text2image_service_port:$text2image_service_port --runtime=habana -e HABANA_VISIBLE_DEVICES=all -e OMPI_MCA_btl_vader_single_copy_mechanism=none --cap-add=sys_nice --ipc=host -e http_proxy=$http_proxy -e https_proxy=$https_proxy -e MODEL=$MODEL -e no_proxy=$no_proxy ${IMAGE_REPO}/text2image-gaudi:${IMAGE_TAG}
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
    SERVICE_NAME="text2image-server - generate image"

    if [ "$HTTP_STATUS" -ne "200" ]; then
        echo "[ $SERVICE_NAME ] HTTP status is not 200. Received status was $HTTP_STATUS"
        docker logs text2image-server >> ${LOG_PATH}/text2image-server_generate_image.log
        exit 1
    else
        echo "[ $SERVICE_NAME ] HTTP status is 200. Checking content..."
    fi
    # Check if the parsed values match the expected values
    if [[ $RESPONSE_BODY == *"images"* ]]; then
        echo "Content correct."
    else
        echo "Content wrong."
        docker logs text2image-server >> ${LOG_PATH}/text2image-server_generate_image.log
        exit 1
    fi
}

function stop_docker() {
    cid=$(docker ps -aq --filter "name=text2image-server*")
    if [[ ! -z "$cid" ]]; then docker stop $cid && docker rm $cid && sleep 1s; fi
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
