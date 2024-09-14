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
ip_address=$(hostname -I | awk '{print $1}')

export video_fn="WeAreGoingOnBullrun.mp4"

function build_docker_images() {
    cd $WORKPATH/docker_image_build
    git clone https://github.com/opea-project/GenAIComps.git && cd GenAIComps && git checkout "${opea_branch:-"main"}" && cd ../

    echo "Build all the images with --no-cache, check docker_image_build.log for details..."
    service_list="multimodalqna multimodalqna-ui embedding-multimodal-bridgetower embedding-multimodal retriever-multimodal-redis lvm-llava lvm-llava-svc dataprep-multimodal-redis"
    docker compose -f build.yaml build ${service_list} --no-cache > ${LOG_PATH}/docker_image_build.log

    docker images && sleep 1m
}

function setup_env() {
    export host_ip=${ip_address}
    export EMBEDDER_PORT=6006
    export MMEI_EMBEDDING_ENDPOINT="http://${host_ip}:$EMBEDDER_PORT/v1/encode"
    export MM_EMBEDDING_PORT_MICROSERVICE=6000
    export REDIS_URL="redis://${host_ip}:6379"
    export REDIS_HOST=${host_ip}
    export INDEX_NAME="mm-rag-redis"
    export LLAVA_SERVER_PORT=8399
    export LVM_ENDPOINT="http://${host_ip}:8399"
    export EMBEDDING_MODEL_ID="BridgeTower/bridgetower-large-itm-mlm-itc"
    export WHISPER_MODEL="base"
    export MM_EMBEDDING_SERVICE_HOST_IP=${host_ip}
    export MM_RETRIEVER_SERVICE_HOST_IP=${host_ip}
    export LVM_SERVICE_HOST_IP=${host_ip}
    export MEGA_SERVICE_HOST_IP=${host_ip}
    export BACKEND_SERVICE_ENDPOINT="http://${host_ip}:8888/v1/multimodalqna"
    export DATAPREP_GEN_TRANSCRIPT_SERVICE_ENDPOINT="http://${host_ip}:6007/v1/generate_transcripts"
    export DATAPREP_GEN_CAPTION_SERVICE_ENDPOINT="http://${host_ip}:6007/v1/generate_captions"
    export DATAPREP_GET_VIDEO_ENDPOINT="http://${host_ip}:6007/v1/dataprep/get_videos"
    export DATAPREP_DELETE_VIDEO_ENDPOINT="http://${host_ip}:6007/v1/dataprep/delete_videos"
}

function start_services() {
    cd $WORKPATH/docker_compose/intel/cpu/xeon


    # Start Docker Containers
    docker compose -f compose.yaml up -d > ${LOG_PATH}/start_services_with_compose.log
    sleep 2m
}

function prepare_data() {
    cd $LOG_PATH
    echo "Downloading video"
    wget http://commondatastorage.googleapis.com/gtv-videos-bucket/sample/WeAreGoingOnBullrun.mp4 -O ${video_fn}

    sleep 1m

}
function validate_service() {
    local URL="$1"
    local EXPECTED_RESULT="$2"
    local SERVICE_NAME="$3"
    local DOCKER_NAME="$4"
    local INPUT_DATA="$5"

    if [[ $SERVICE_NAME == *"dataprep-multimodal-redis"* ]]; then
        cd $LOG_PATH
        HTTP_RESPONSE=$(curl --silent --write-out "HTTPSTATUS:%{http_code}" -X POST -F "files=@./${video_fn}" -H 'Content-Type: multipart/form-data' "$URL")
    elif [[ $SERVICE_NAME == *"dataprep_get"* ]]; then
        HTTP_RESPONSE=$(curl --silent --write-out "HTTPSTATUS:%{http_code}" -X POST -H 'Content-Type: application/json' "$URL")
    elif [[ $SERVICE_NAME == *"dataprep_del"* ]]; then
        HTTP_RESPONSE=$(curl --silent --write-out "HTTPSTATUS:%{http_code}" -X POST -H 'Content-Type: application/json' "$URL")
    else
        HTTP_RESPONSE=$(curl --silent --write-out "HTTPSTATUS:%{http_code}" -X POST -d "$INPUT_DATA" -H 'Content-Type: application/json' "$URL")
    fi
    HTTP_STATUS=$(echo $HTTP_RESPONSE | tr -d '\n' | sed -e 's/.*HTTPSTATUS://')
    RESPONSE_BODY=$(echo $HTTP_RESPONSE | sed -e 's/HTTPSTATUS\:.*//g')

    docker logs ${DOCKER_NAME} >> ${LOG_PATH}/${SERVICE_NAME}.log

    # check response status
    if [ "$HTTP_STATUS" -ne "200" ]; then
        echo "[ $SERVICE_NAME ] HTTP status is not 200. Received status was $HTTP_STATUS"
        exit 1
    else
        echo "[ $SERVICE_NAME ] HTTP status is 200. Checking content..."
    fi
    # check response body
    if [[ "$RESPONSE_BODY" != *"$EXPECTED_RESULT"* ]]; then
        echo "[ $SERVICE_NAME ] Content does not match the expected result: $RESPONSE_BODY"
        exit 1
    else
        echo "[ $SERVICE_NAME ] Content is as expected."
    fi

    sleep 1s
}

function validate_microservices() {
    # Check if the microservices are running correctly.

    # Bridgetower Embedding Server
    echo "Validating embedding-multimodal-bridgetower"
    validate_service \
        "http://${host_ip}:${EMBEDDER_PORT}/v1/encode" \
        '"embedding":[' \
        "embedding-multimodal-bridgetower" \
        "embedding-multimodal-bridgetower" \
        '{"text":"This is example"}'

    validate_service \
        "http://${host_ip}:${EMBEDDER_PORT}/v1/encode" \
        '"embedding":[' \
        "embedding-multimodal-bridgetower" \
        "embedding-multimodal-bridgetower" \
        '{"text":"This is example", "img_b64_str": "iVBORw0KGgoAAAANSUhEUgAAAAoAAAAKCAYAAACNMs+9AAAAFUlEQVR42mP8/5+hnoEIwDiqkL4KAcT9GO0U4BxoAAAAAElFTkSuQmCC"}'

    # embedding microservice
    echo "Validating embedding-multimodal"
    validate_service \
        "http://${host_ip}:$MM_EMBEDDING_PORT_MICROSERVICE/v1/embeddings" \
        '"embedding":[' \
        "embedding-multimodal" \
        "embedding-multimodal" \
        '{"text" : "This is some sample text."}'

    validate_service \
        "http://${host_ip}:$MM_EMBEDDING_PORT_MICROSERVICE/v1/embeddings" \
        '"embedding":[' \
        "embedding-multimodal" \
        "embedding-multimodal" \
        '{"text": {"text" : "This is some sample text."}, "image" : {"url": "https://github.com/docarray/docarray/blob/main/tests/toydata/image-data/apple.png?raw=true"}}'

    sleep 1m # retrieval can't curl as expected, try to wait for more time

    # test data prep
    echo "Data Prep with Generating Transcript"
    validate_service \
        "${DATAPREP_GEN_TRANSCRIPT_SERVICE_ENDPOINT}" \
        "Data preparation succeeded" \
        "dataprep-multimodal-redis" \
        "dataprep-multimodal-redis"

    # echo "Data Prep with Generating Caption"
    # validate_service \
    #     "${DATAPREP_GEN_CAPTION_SERVICE_ENDPOINT}" \
    #     "Data preparation succeeded" \
    #     "dataprep-multimodal-redis" \
    #     "dataprep-multimodal-redis"

    echo "Validating get file"
    validate_service \
        "${DATAPREP_GET_VIDEO_ENDPOINT}" \
        '.mp4' \
        "dataprep_get" \
        "dataprep-multimodal-redis"

    sleep 1m

    # multimodal retrieval microservice
    echo "Validating retriever-multimodal-redis"
    your_embedding=$(python3 -c "import random; embedding = [random.uniform(-1, 1) for _ in range(512)]; print(embedding)")
    validate_service \
        "http://${host_ip}:7000/v1/multimodal_retrieval" \
        "retrieved_docs" \
        "retriever-multimodal-redis" \
        "retriever-multimodal-redis" \
        "{\"text\":\"test\",\"embedding\":${your_embedding}}"

    sleep 10s

    # llava server
    echo "Evaluating lvm-llava"
    validate_service \
        "http://${host_ip}:${LLAVA_SERVER_PORT}/generate" \
        '"text":' \
        "lvm-llava" \
        "lvm-llava" \
        '{"prompt":"Describe the image please.", "img_b64_str": "iVBORw0KGgoAAAANSUhEUgAAAAoAAAAKCAYAAACNMs+9AAAAFUlEQVR42mP8/5+hnoEIwDiqkL4KAcT9GO0U4BxoAAAAAElFTkSuQmCC"}'

    # lvm
    echo "Evaluating lvm-llava-svc"
    validate_service \
        "http://${host_ip}:9399/v1/lvm" \
        '"text":"' \
        "lvm-llava-svc" \
        "lvm-llava-svc" \
        '{"retrieved_docs": [], "initial_query": "What is this?", "top_n": 1, "metadata": [{"b64_img_str": "iVBORw0KGgoAAAANSUhEUgAAAAoAAAAKCAYAAACNMs+9AAAAFUlEQVR42mP8/5+hnoEIwDiqkL4KAcT9GO0U4BxoAAAAAElFTkSuQmCC", "transcript_for_inference": "yellow image", "video_id": "8c7461df-b373-4a00-8696-9a2234359fe0", "time_of_frame_ms":"37000000", "source_video":"WeAreGoingOnBullrun_8c7461df-b373-4a00-8696-9a2234359fe0.mp4"}], "chat_template":"The caption of the image is: '\''{context}'\''. {question}"}'

    sleep 3m
}

function validate_megaservice() {
    # Curl the Mega Service with retrieval
    echo "Validate megaservice with first query"
    validate_service \
        "http://${host_ip}:8888/v1/multimodalqna" \
        '"time_of_frame_ms":' \
        "multimodalqna" \
        "multimodalqna-backend-server" \
        '{"messages": "What is the revenue of Nike in 2023?"}'

    echo "Validate megaservice with follow-up query"
    validate_service \
        "http://${host_ip}:8888/v1/multimodalqna" \
        '"content":"' \
        "multimodalqna" \
        "multimodalqna-backend-server" \
        '{"messages": [{"role": "user", "content": [{"type": "text", "text": "hello, "}, {"type": "image_url", "image_url": {"url": "https://www.ilankelman.org/stopsigns/australia.jpg"}}]}, {"role": "assistant", "content": "opea project! "}, {"role": "user", "content": "chao, "}], "max_tokens": 10}'

}

function validate_delete {
    echo "Validate data prep delete videos"
    validate_service \
        "${DATAPREP_DELETE_VIDEO_ENDPOINT}" \
        '{"status":true}' \
        "dataprep_del" \
        "dataprep-multimodal-redis"
}

function stop_docker() {
    cd $WORKPATH/docker_compose/intel/cpu/xeon
    docker compose -f compose.yaml stop && docker compose -f compose.yaml rm -f
}

function main() {

    setup_env
    stop_docker
    if [[ "$IMAGE_REPO" == "opea" ]]; then build_docker_images; fi
    start_time=$(date +%s)
    start_services
    end_time=$(date +%s)
    duration=$((end_time-start_time))
    echo "Mega service start duration is $duration s" && sleep 1s
    prepare_data

    validate_microservices
    echo "==== microservices validated ===="
    validate_megaservice
    echo "==== megaservice validated ===="
    validate_delete
    echo "==== delete validated ===="

    stop_docker
    echo y | docker system prune

}

main
