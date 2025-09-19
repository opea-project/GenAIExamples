#!/bin/bash
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

export image_fn="sample.png"
export video_fn="WeAreGoingOnBullrun.mp4"
export audio_fn="sample.mp3"  # audio_fn and caption_fn are used as captions for image_fn, so they all need the same base name
export caption_fn="sample.txt"
export pdf_fn="nke-10k-2023.pdf"

function check_service_ready() {
    local container_name="$1"
    local max_retries="$2"
    local log_string="$3"

    for i in $(seq 1 "$max_retries")
    do
        service_logs=$(docker logs "$container_name" 2>&1 | grep "$log_string" || true)
        if [[ -z "$service_logs" ]]; then
            echo "The $container_name service is not ready yet, sleeping 30s..."
            sleep 30s
        else
            echo "$container_name service is ready"
            break
        fi
    done

    if [[ $i -ge $max_retries ]]; then
        echo "WARNING: Max retries reached when waiting for the $container_name service to be ready"
        docker logs "$container_name" >> "${LOG_PATH}/$container_name_file.log"
    fi
}

function build_docker_images() {
    opea_branch=${opea_branch:-"main"}

    cd $WORKPATH/docker_image_build
    git clone --depth 1 --branch ${opea_branch} https://github.com/opea-project/GenAIComps.git
    pushd GenAIComps
    echo "GenAIComps test commit is $(git rev-parse HEAD)"
    docker build --no-cache -t ${REGISTRY}/comps-base:${TAG} --build-arg https_proxy=$https_proxy --build-arg http_proxy=$http_proxy -f Dockerfile .
    popd && sleep 1s

    echo "Build all the images with --no-cache, check docker_image_build.log for details..."
    service_list="multimodalqna multimodalqna-ui embedding-multimodal-bridgetower embedding retriever speecht5 lvm-llava lvm dataprep whisper"
    docker compose -f build.yaml build ${service_list} --no-cache > ${LOG_PATH}/docker_image_build.log
    docker images && sleep 1s
}

function setup_env() {
    export host_ip=${ip_address}
    cd $WORKPATH/docker_compose/intel
    source set_env.sh
    export LVM_MODEL_ID="llava-hf/llava-1.5-7b-hf"
}


function start_services() {
    echo "Starting services..."
    cd $WORKPATH/docker_compose/intel/cpu/xeon
    export no_proxy="localhost,127.0.0.1,$ip_address"
    docker compose -f compose.yaml up -d > ${LOG_PATH}/start_services_with_compose.log
    sleep 2m
    echo "Services started."
}

function prepare_data() {
    cd $LOG_PATH
    echo "Downloading image and video"
    wget https://github.com/docarray/docarray/blob/main/tests/toydata/image-data/apple.png?raw=true -O ${image_fn}
    wget https://github.com/intel/intel-extension-for-transformers/raw/refs/tags/v1.5/intel_extension_for_transformers/neural_chat/ui/customized/talkingbot/src/lib/components/talkbot/assets/mid-age-man.mp3 -O ${audio_fn}
    wget http://commondatastorage.googleapis.com/gtv-videos-bucket/sample/WeAreGoingOnBullrun.mp4 -O ${video_fn}
    wget https://raw.githubusercontent.com/opea-project/GenAIComps/v1.3/comps/third_parties/pathway/src/data/nke-10k-2023.pdf -O ${pdf_fn}
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
        HTTP_RESPONSE=$(curl --silent --write-out "HTTPSTATUS:%{http_code}" -X POST -F "files=@./${video_fn}" -F "files=@./${audio_fn}" -H 'Content-Type: multipart/form-data' "$URL")
    elif [[ $SERVICE_NAME == *"dataprep-multimodal-redis-caption"* ]]; then
        cd $LOG_PATH
        HTTP_RESPONSE=$(curl --silent --write-out "HTTPSTATUS:%{http_code}" -X POST -F "files=@./${image_fn}" -H 'Content-Type: multipart/form-data' "$URL")
    elif [[ $SERVICE_NAME == *"dataprep-multimodal-redis-ingest-image-audio"* ]]; then
        cd $LOG_PATH
        HTTP_RESPONSE=$(curl --silent --write-out "HTTPSTATUS:%{http_code}" -X POST -F "files=@./${image_fn}" -F "files=@./${audio_fn}" -H 'Content-Type: multipart/form-data' "$URL")
    elif [[ $SERVICE_NAME == *"dataprep-multimodal-redis-ingest"* ]]; then
        cd $LOG_PATH
        HTTP_RESPONSE=$(curl --silent --write-out "HTTPSTATUS:%{http_code}" -X POST -F "files=@./${image_fn}" -F "files=@./${caption_fn}" -H 'Content-Type: multipart/form-data' "$URL")
    elif [[ $SERVICE_NAME == *"dataprep-multimodal-redis-pdf"* ]]; then
        cd $LOG_PATH
        HTTP_RESPONSE=$(curl --silent --write-out "HTTPSTATUS:%{http_code}" -X POST -F "files=@./${pdf_fn}" -H 'Content-Type: multipart/form-data' "$URL")
    elif [[ $SERVICE_NAME == *"dataprep_get"* ]]; then
        HTTP_RESPONSE=$(curl --silent --write-out "HTTPSTATUS:%{http_code}" -X POST -H 'Content-Type: application/json' "$URL")
    elif [[ $SERVICE_NAME == *"dataprep_del"* ]]; then
        HTTP_RESPONSE=$(curl --silent --write-out "HTTPSTATUS:%{http_code}" -X POST -d '{"file_path": "${caption_fn}"}' -H 'Content-Type: application/json' "$URL")
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
        "http://${host_ip}:${EMM_BRIDGETOWER_PORT}/v1/encode" \
        '"embedding":[' \
        "embedding-multimodal-bridgetower" \
        "embedding-multimodal-bridgetower" \
        '{"text":"This is example"}'

    validate_service \
        "http://${host_ip}:${EMM_BRIDGETOWER_PORT}/v1/encode" \
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
    echo "Validating Data Prep with Generating Transcript for Video"
    validate_service \
        "${DATAPREP_GEN_TRANSCRIPT_SERVICE_ENDPOINT}" \
        "Data preparation succeeded" \
        "dataprep-multimodal-redis-transcript" \
        "dataprep-multimodal-redis"

    echo "Validating Data Prep with Image & Text Caption Ingestion"
    validate_service \
        "${DATAPREP_INGEST_SERVICE_ENDPOINT}" \
        "Data preparation succeeded" \
        "dataprep-multimodal-redis-ingest" \
        "dataprep-multimodal-redis"

    echo "Validating Data Prep with Image & Audio Caption Ingestion"
    validate_service \
        "${DATAPREP_INGEST_SERVICE_ENDPOINT}" \
        "Data preparation succeeded" \
        "dataprep-multimodal-redis-ingest-image-audio" \
        "dataprep-multimodal-redis"

    echo "Validating Data Prep with PDF"
    validate_service \
        "${DATAPREP_INGEST_SERVICE_ENDPOINT}" \
        "Data preparation succeeded" \
        "dataprep-multimodal-redis-pdf" \
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

    sleep 1m

    # multimodal retrieval microservice
    echo "Validating retriever-redis"
    your_embedding=$(python3 -c "import random; embedding = [random.uniform(-1, 1) for _ in range(512)]; print(embedding)")
    validate_service \
        "http://${host_ip}:${REDIS_RETRIEVER_PORT}/v1/retrieval" \
        "retrieved_docs" \
        "retriever-redis" \
        "retriever-redis" \
        "{\"text\":\"test\",\"embedding\":${your_embedding}}"

    echo "Wait for lvm-llava service to be ready"
    check_service_ready "lvm-llava" 10 "Uvicorn running on http://"

    # llava server
    echo "Evaluating lvm-llava"
    validate_service \
        "http://${host_ip}:${LLAVA_SERVER_PORT}/generate" \
        '"text":' \
        "lvm-llava" \
        "lvm-llava" \
        '{"prompt":"Describe the image please.", "img_b64_str": "iVBORw0KGgoAAAANSUhEUgAAAAoAAAAKCAYAAACNMs+9AAAAFUlEQVR42mP8/5+hnoEIwDiqkL4KAcT9GO0U4BxoAAAAAElFTkSuQmCC"}'

    echo "Evaluating lvm-llava with a list of images"
    validate_service \
        "http://${host_ip}:${LLAVA_SERVER_PORT}/generate" \
        '"text":' \
        "lvm-llava" \
        "lvm-llava" \
        '{"prompt":"Describe the image please.", "img_b64_str": ["iVBORw0KGgoAAAANSUhEUgAAAAoAAAAKCAYAAACNMs+9AAAAFUlEQVR42mP8/5+hnoEIwDiqkL4KAcT9GO0U4BxoAAAAAElFTkSuQmCC","iVBORw0KGgoAAAANSUhEUgAAAAoAAAAKCAYAAACNMs+9AAAAFUlEQVR42mNkYPhfz0AEYBxVSF+FAP5FDvcfRYWgAAAAAElFTkSuQmCC"]}'

    # lvm
    echo "Evaluating lvm"
    validate_service \
        "http://${host_ip}:${LVM_PORT}/v1/lvm" \
        '"text":"' \
        "lvm" \
        "lvm" \
        '{"retrieved_docs": [], "initial_query": "What is this?", "top_n": 1, "metadata": [{"b64_img_str": "iVBORw0KGgoAAAANSUhEUgAAAAoAAAAKCAYAAACNMs+9AAAAFUlEQVR42mP8/5+hnoEIwDiqkL4KAcT9GO0U4BxoAAAAAElFTkSuQmCC", "transcript_for_inference": "yellow image", "video_id": "8c7461df-b373-4a00-8696-9a2234359fe0", "time_of_frame_ms":"37000000", "source_video":"WeAreGoingOnBullrun_8c7461df-b373-4a00-8696-9a2234359fe0.mp4"}], "chat_template":"The caption of the image is: '\''{context}'\''. {question}"}'

    # data prep requiring lvm
    echo "Validating Data Prep with Generating Caption for Image"
    validate_service \
        "${DATAPREP_GEN_CAPTION_SERVICE_ENDPOINT}" \
        "Data preparation succeeded" \
        "dataprep-multimodal-redis-caption" \
        "dataprep-multimodal-redis"

    echo "Validating Text to speech service"
    validate_service \
        "${TTS_ENDPOINT}" \
        '"tts_result":' \
        "speecht5-service" \
        "speecht5-service" \
        '{"text": "Who are you?"}'


    sleep 3m
}

function validate_megaservice() {
    # Curl the Mega Service with retrieval
    echo "Validating megaservice with first query"
    validate_service \
        "http://${host_ip}:${MEGA_SERVICE_PORT}/v1/multimodalqna" \
        'red' \
        "multimodalqna" \
        "multimodalqna-backend-server" \
        '{"messages": "Find an apple. What color is it?"}'

    echo "Validating megaservice with audio response"
    validate_service \
        "http://${host_ip}:${MEGA_SERVICE_PORT}/v1/multimodalqna" \
        '"audio":{"data"' \
        "multimodalqna" \
        "multimodalqna-backend-server" \
        '{"messages": "Find an apple. What color is it?", "modalities": ["text", "audio"]}'

    echo "Validating megaservice with first audio query"
    validate_service \
        "http://${host_ip}:${MEGA_SERVICE_PORT}/v1/multimodalqna" \
        '"time_of_frame_ms":' \
        "multimodalqna" \
        "multimodalqna-backend-server" \
        '{"messages": [{"role": "user", "content": [{"type": "audio", "audio": "UklGRigAAABXQVZFZm10IBIAAAABAAEARKwAAIhYAQACABAAAABkYXRhAgAAAAEA"}]}]}'

    echo "Validating megaservice with first query with an image"
    validate_service \
        "http://${host_ip}:${MEGA_SERVICE_PORT}/v1/multimodalqna" \
        '"time_of_frame_ms":' \
        "multimodalqna" \
        "multimodalqna-backend-server" \
        '{"messages": [{"role": "user", "content": [{"type": "text", "text": "hello, "}, {"type": "image_url", "image_url": {"url": "https://www.ilankelman.org/stopsigns/australia.jpg"}}]}], "max_tokens": 10, "modalities": ["text", "audio"]}'
    echo "Validating megaservice with follow-up query"
    validate_service \
        "http://${host_ip}:${MEGA_SERVICE_PORT}/v1/multimodalqna" \
        '"content":"' \
        "multimodalqna" \
        "multimodalqna-backend-server" \
        '{"messages": [{"role": "user", "content": [{"type": "audio", "audio": "UklGRigAAABXQVZFZm10IBIAAAABAAEARKwAAIhYAQACABAAAABkYXRhAgAAAAEA"}, {"type": "image_url", "image_url": {"url": "https://www.ilankelman.org/stopsigns/australia.jpg"}}]}, {"role": "assistant", "content": "opea project! "}, {"role": "user", "content": [{"type": "text", "text": "goodbye"}]}]}'

    echo "Validating megaservice with multiple text queries"
    validate_service \
        "http://${host_ip}:${MEGA_SERVICE_PORT}/v1/multimodalqna" \
        '"content":"' \
        "multimodalqna" \
        "multimodalqna-backend-server" \
        '{"messages": [{"role": "user", "content": [{"type": "text", "text": "hello, "}]}, {"role": "assistant", "content": "opea project! "}, {"role": "user", "content": [{"type": "text", "text": "goodbye"}]}]}'
}

function validate_delete {
    echo "Validating data prep delete files"
    export DATAPREP_DELETE_FILE_ENDPOINT="http://${host_ip}:${DATAPREP_MMR_PORT}/v1/dataprep/delete"
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
    rm -rf ${audio_fn}
    rm -rf ${pdf_fn}
    rm -rf ${caption_fn}
}

function stop_docker() {
    echo "Stopping docker..."
    cd $WORKPATH/docker_compose/intel/cpu/xeon
    docker compose -f compose.yaml stop && docker compose -f compose.yaml rm -f
    echo "Docker stopped."
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
