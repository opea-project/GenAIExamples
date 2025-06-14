#!/bin/bash
# Copyright (C) 2024 Advanced Micro Devices, Inc.
# SPDX-License-Identifier: Apache-2.0

set -ex
IMAGE_REPO=${IMAGE_REPO:-"opea"}
IMAGE_TAG=${IMAGE_TAG:-"latest"}
echo "REGISTRY=IMAGE_REPO=${IMAGE_REPO}"
echo "TAG=IMAGE_TAG=${IMAGE_TAG}"
export REGISTRY=${IMAGE_REPO}
export TAG=${IMAGE_TAG}
export MODEL_CACHE=${model_cache:-"/var/lib/GenAI/data"}

WORKPATH=$(dirname "$PWD")
LOG_PATH="$WORKPATH/tests"
ip_address=$(hostname -I | awk '{print $1}')

export image_fn="apple.png"
export video_fn="WeAreGoingOnBullrun.mp4"
export caption_fn="apple.txt"

function build_docker_images() {
    opea_branch=${opea_branch:-"main"}

    cd $WORKPATH/docker_image_build
    git clone --depth 1 --branch ${opea_branch} https://github.com/opea-project/GenAIComps.git
    pushd GenAIComps
    echo "GenAIComps test commit is $(git rev-parse HEAD)"
    docker build --no-cache -t ${REGISTRY}/comps-base:${TAG} --build-arg https_proxy=$https_proxy --build-arg http_proxy=$http_proxy -f Dockerfile .
    popd && sleep 1s

    echo "Build all the images with --no-cache, check docker_image_build.log for details..."
    service_list="multimodalqna multimodalqna-ui embedding-multimodal-bridgetower embedding retriever lvm dataprep whisper"
    docker compose -f build.yaml build ${service_list} --no-cache > ${LOG_PATH}/docker_image_build.log

    docker images && sleep 1m
}

function setup_env() {
    export host_ip=${ip_address}
    export MODEL_CACHE=${model_cache:-"/var/opea/multimodalqna-service/data"}
    cd $WORKPATH/docker_compose/amd/gpu/rocm
    source set_env.sh
}

function start_services() {
    cd $WORKPATH/docker_compose/amd/gpu/rocm
    docker compose -f compose.yaml up -d > ${LOG_PATH}/start_services_with_compose.log
    n=0
    until [[ "$n" -ge 100 ]]; do
        docker logs tgi-llava-rocm-server >& $LOG_PATH/tgi-llava-rocm-server_start.log
        if grep -q "Connected" $LOG_PATH/tgi-llava-rocm-server_start.log; then
            break
        fi
        sleep 10s
        n=$((n+1))
    done
}

function prepare_data() {
    cd $LOG_PATH
    echo "Downloading image and video"
    wget https://github.com/docarray/docarray/blob/main/tests/toydata/image-data/apple.png?raw=true -O ${image_fn}
    wget http://commondatastorage.googleapis.com/gtv-videos-bucket/sample/WeAreGoingOnBullrun.mp4 -O ${video_fn}
    echo "Writing caption file"
    echo "This is an apple."  > ${caption_fn}
    sleep 1m
}


function validate_service() {
    local URL="$1"
    local EXPECTED_RESULT="$2"
    local SERVICE_NAME="$3"
    local DOCKER_NAME="$4"
    local INPUT_DATA="$5"

    if [[ $SERVICE_NAME == *"dataprep-multimodal-redis-transcript"* ]]; then
        cd $LOG_PATH
        HTTP_RESPONSE=$(curl --silent --write-out "HTTPSTATUS:%{http_code}" -X POST -F "files=@./${video_fn}" -H 'Content-Type: multipart/form-data' "$URL")
    elif [[ $SERVICE_NAME == *"dataprep-multimodal-redis-caption"* ]]; then
        cd $LOG_PATH
        HTTP_RESPONSE=$(curl --silent --write-out "HTTPSTATUS:%{http_code}" -X POST -F "files=@./${image_fn}" -H 'Content-Type: multipart/form-data' "$URL")
    elif [[ $SERVICE_NAME == *"dataprep-multimodal-redis-ingest"* ]]; then
        cd $LOG_PATH
        HTTP_RESPONSE=$(curl --silent --write-out "HTTPSTATUS:%{http_code}" -X POST -F "files=@./${image_fn}" -F "files=@./apple.txt" -H 'Content-Type: multipart/form-data' "$URL")
    elif [[ $SERVICE_NAME == *"dataprep_get"* ]]; then
        HTTP_RESPONSE=$(curl --silent --write-out "HTTPSTATUS:%{http_code}" -X POST -H 'Content-Type: application/json' "$URL")
    elif [[ $SERVICE_NAME == *"dataprep_del"* ]]; then
        HTTP_RESPONSE=$(curl --silent --write-out "HTTPSTATUS:%{http_code}" -X POST -d '{"file_path": "apple.txt"}' -H 'Content-Type: application/json' "$URL")
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
    echo "Validating embedding"
    validate_service \
        "http://${host_ip}:$MM_EMBEDDING_PORT_MICROSERVICE/v1/embeddings" \
        '"embedding":[' \
        "embedding" \
        "embedding" \
        '{"text" : "This is some sample text."}'

    validate_service \
        "http://${host_ip}:$MM_EMBEDDING_PORT_MICROSERVICE/v1/embeddings" \
        '"embedding":[' \
        "embedding" \
        "embedding" \
        '{"text": {"text" : "This is some sample text."}, "image" : {"url": "https://github.com/docarray/docarray/blob/main/tests/toydata/image-data/apple.png?raw=true"}}'

    sleep 1m # retrieval can't curl as expected, try to wait for more time

    # test data prep
    echo "Data Prep with Generating Transcript for Video"
    validate_service \
        "${DATAPREP_GEN_TRANSCRIPT_SERVICE_ENDPOINT}" \
        "Data preparation succeeded" \
        "dataprep-multimodal-redis-transcript" \
        "dataprep-multimodal-redis"

    echo "Data Prep with Image & Caption Ingestion"
    validate_service \
        "${DATAPREP_INGEST_SERVICE_ENDPOINT}" \
        "Data preparation succeeded" \
        "dataprep-multimodal-redis-ingest" \
        "dataprep-multimodal-redis"

    echo "Validating get file returns mp4"
    validate_service \
        "${DATAPREP_GET_FILE_ENDPOINT}" \
        '.mp4' \
        "dataprep_get" \
        "dataprep-multimodal-redis"

    echo "Validating get file returns png"
    validate_service \
        "${DATAPREP_GET_FILE_ENDPOINT}" \
        '.png' \
        "dataprep_get" \
        "dataprep-multimodal-redis"

    sleep 2m

    # multimodal retrieval microservice
    echo "Validating retriever-redis"
    your_embedding=$(python3 -c "import random; embedding = [random.uniform(-1, 1) for _ in range(512)]; print(embedding)")
    validate_service \
        "http://${host_ip}:7000/v1/retrieval" \
        "retrieved_docs" \
        "retriever-redis" \
        "retriever-redis" \
        "{\"text\":\"test\",\"embedding\":${your_embedding}}"

    sleep 5m

    # llava server
    echo "Evaluating lvm-llava"
    validate_service \
        "http://${host_ip}:${LLAVA_SERVER_PORT}/generate" \
        '"generated_text":' \
        "tgi-llava-rocm-server" \
        "tgi-llava-rocm-server" \
        '{"inputs":"![](https://huggingface.co/datasets/huggingface/documentation-images/resolve/main/transformers/rabbit.png)What is this a picture of?\n\n","parameters":{"max_new_tokens":16, "seed": 42}}'

    # lvm
    echo "Evaluating lvm"
    validate_service \
        "http://${host_ip}:9399/v1/lvm" \
        '"text":"' \
        "lvm" \
        "lvm" \
        '{"retrieved_docs": [], "initial_query": "What is this?", "top_n": 1, "metadata": [{"b64_img_str": "iVBORw0KGgoAAAANSUhEUgAAAAoAAAAKCAYAAACNMs+9AAAAFUlEQVR42mP8/5+hnoEIwDiqkL4KAcT9GO0U4BxoAAAAAElFTkSuQmCC", "transcript_for_inference": "yellow image", "video_id": "8c7461df-b373-4a00-8696-9a2234359fe0", "time_of_frame_ms":"37000000", "source_video":"WeAreGoingOnBullrun_8c7461df-b373-4a00-8696-9a2234359fe0.mp4"}], "chat_template":"The caption of the image is: '\''{context}'\''. {question}"}'

    # data prep requiring lvm
    echo "Data Prep with Generating Caption for Image"
    validate_service \
        "${DATAPREP_GEN_CAPTION_SERVICE_ENDPOINT}" \
        "Data preparation succeeded" \
        "dataprep-multimodal-redis-caption" \
        "dataprep-multimodal-redis"

    sleep 3m
}

function validate_megaservice() {
    # Curl the Mega Service with retrieval
    echo "Validate megaservice with first query"
    validate_service \
        "http://${host_ip}:8888/v1/multimodalqna" \
        'red' \
        "multimodalqna" \
        "multimodalqna-backend-server" \
        '{"messages": "Find an apple. What color is it?"}'

    echo "Validate megaservice with first audio query"
    validate_service \
        "http://${host_ip}:8888/v1/multimodalqna" \
        '"time_of_frame_ms":' \
        "multimodalqna" \
        "multimodalqna-backend-server" \
        '{"messages": [{"role": "user", "content": [{"type": "audio", "audio": "UklGRigAAABXQVZFZm10IBIAAAABAAEARKwAAIhYAQACABAAAABkYXRhAgAAAAEA"}]}]}'

    echo "Validate megaservice with follow-up query"
    validate_service \
        "http://${host_ip}:8888/v1/multimodalqna" \
        '"content":"' \
        "multimodalqna" \
        "multimodalqna-backend-server" \
        '{"messages": [{"role": "user", "content": [{"type": "audio", "audio": "UklGRigAAABXQVZFZm10IBIAAAABAAEARKwAAIhYAQACABAAAABkYXRhAgAAAAEA"}, {"type": "image_url", "image_url": {"url": "https://www.ilankelman.org/stopsigns/australia.jpg"}}]}, {"role": "assistant", "content": "opea project! "}, {"role": "user", "content": [{"type": "text", "text": "goodbye"}]}]}'

    echo "Validate megaservice with multiple text queries"
    validate_service \
        "http://${host_ip}:8888/v1/multimodalqna" \
        '"content":"' \
        "multimodalqna" \
        "multimodalqna-backend-server" \
        '{"messages": [{"role": "user", "content": [{"type": "text", "text": "hello, "}]}, {"role": "assistant", "content": "opea project! "}, {"role": "user", "content": [{"type": "text", "text": "goodbye"}]}]}'
}

function validate_delete {
    echo "Validate data prep delete files"
    export DATAPREP_DELETE_FILE_ENDPOINT="http://${HOST_IP}:6007/v1/dataprep/delete"
    validate_service \
        "${DATAPREP_DELETE_FILE_ENDPOINT}" \
        '{"status":true}' \
        "dataprep_del" \
        "dataprep-multimodal-redis"
}

function delete_data() {
    cd $LOG_PATH
    echo "Deleting image, video, and caption"
    rm -rf ${image_fn}
    rm -rf ${video_fn}
    rm -rf ${caption_fn}
}

function stop_docker() {
    cd $WORKPATH/docker_compose/amd/gpu/rocm
    docker compose -f compose.yaml stop && docker compose -f compose.yaml rm -f
}

function main() {

    setup_env

    echo "::group::stop_docker"
    stop_docker
    echo "::endgroup::"

    echo "::group::build_docker_images"
    if [[ "$IMAGE_REPO" == "opea" ]]; then build_docker_images; fi
    echo "::endgroup::"

    echo "::group::start_services"
    start_services
    echo "::endgroup::"

    echo "::group::prepare_data"
    prepare_data
    echo "::endgroup::"

    echo "::group::validate_microservices"
    validate_microservices
    echo "::endgroup::"

    echo "::group::validate_megaservice"
    validate_megaservice
    echo "::endgroup::"

    echo "::group::validate_delete"
    validate_delete
    echo "::endgroup::"

    echo "::group::delete_data"
    delete_data
    echo "::endgroup::"

    echo "::group::stop_docker"
    stop_docker
    echo "::endgroup::"

    docker system prune -f

}

main
