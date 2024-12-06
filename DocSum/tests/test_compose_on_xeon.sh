#!/bin/bash
# Copyright (C) 2024 Intel Corporation
# SPDX-License-Identifier: Apache-2.0

set -xe

IMAGE_REPO=${IMAGE_REPO:-"opea"}
IMAGE_TAG=${IMAGE_TAG:-"latest"}
export http_proxy=$http_proxy
export https_proxy=$https_proxy
export host_ip=$(hostname -I | awk '{print $1}')

echo "REGISTRY=IMAGE_REPO=${IMAGE_REPO}"
echo "TAG=IMAGE_TAG=${IMAGE_TAG}"
export REGISTRY=${IMAGE_REPO}
export TAG=${IMAGE_TAG}

export LLM_MODEL_ID="Intel/neural-chat-7b-v3-3"
export TGI_LLM_ENDPOINT="http://${host_ip}:8008"
export HUGGINGFACEHUB_API_TOKEN=${HUGGINGFACEHUB_API_TOKEN}
export MEGA_SERVICE_HOST_IP=${host_ip}
export LLM_SERVICE_HOST_IP=${host_ip}
export BACKEND_SERVICE_ENDPOINT="http://${host_ip}:8888/v1/docsum"
export no_proxy="${no_proxy},${host_ip}"

export V2A_SERVICE_HOST_IP=${host_ip}
export V2A_ENDPOINT=http://$host_ip:7078

export A2T_ENDPOINT=http://$host_ip:7066
export A2T_SERVICE_HOST_IP=${host_ip}
export A2T_SERVICE_PORT=9099

export DATA_ENDPOINT=http://$host_ip:7079
export DATA_SERVICE_HOST_IP=${host_ip}
export DATA_SERVICE_PORT=7079

WORKPATH=$(dirname "$PWD")
LOG_PATH="$WORKPATH/tests"

# Get the root folder of the current script
ROOT_FOLDER=$(dirname "$(readlink -f "$0")")

function build_docker_images() {
    cd $WORKPATH/docker_image_build
    git clone https://github.com/opea-project/GenAIComps.git && cd GenAIComps && git checkout "${opea_branch:-"main"}" && cd ../

    echo "Build all the images with --no-cache, check docker_image_build.log for details..."
    service_list="docsum docsum-ui whisper dataprep-multimedia2text dataprep-audio2text dataprep-video2audio llm-docsum-tgi"
    docker compose -f build.yaml build ${service_list} --no-cache > ${LOG_PATH}/docker_image_build.log

    docker pull ghcr.io/huggingface/text-generation-inference:1.4
    docker images && sleep 1s
}

function start_services() {
    cd $WORKPATH/docker_compose/intel/cpu/xeon/

    docker compose -f compose.yaml up -d > ${LOG_PATH}/start_services_with_compose.log
    sleep 3m

    until [[ "$n" -ge 100 ]]; do
        docker logs tgi-service > ${LOG_PATH}/tgi_service_start.log
        if grep -q Connected ${LOG_PATH}/tgi_service_start.log; then
            break
        fi
        sleep 5s
        n=$((n+1))
    done
}

function validate_services() {
    local URL="$1"
    local EXPECTED_RESULT="$2"
    local SERVICE_NAME="$3"
    local DOCKER_NAME="$4"
    local INPUT_DATA="$5"

    local HTTP_STATUS=$(curl -s -o /dev/null -w "%{http_code}" -X POST -d "$INPUT_DATA" -H 'Content-Type: application/json' "$URL")

    echo "==========================================="

    if [ "$HTTP_STATUS" -eq 200 ]; then
        echo "[ $SERVICE_NAME ] HTTP status is 200. Checking content..."

        local CONTENT=$(curl -s -X POST -d "$INPUT_DATA" -H 'Content-Type: application/json' "$URL" | tee ${LOG_PATH}/${SERVICE_NAME}.log)

        if echo "$CONTENT" | grep -q "$EXPECTED_RESULT"; then
            echo "[ $SERVICE_NAME ] Content is as expected."
        else
            echo "EXPECTED_RESULT==> $EXPECTED_RESULT"
            echo "CONTENT==> $CONTENT"
            echo "[ $SERVICE_NAME ] Content does not match the expected result: $CONTENT"
            docker logs ${DOCKER_NAME} >> ${LOG_PATH}/${SERVICE_NAME}.log
            exit 1

        fi
    else
        echo "[ $SERVICE_NAME ] HTTP status is not 200. Received status was $HTTP_STATUS"
        docker logs ${DOCKER_NAME} >> ${LOG_PATH}/${SERVICE_NAME}.log
        exit 1
    fi
    sleep 1s
}

get_base64_str() {
    local file_name=$1
    base64 -w 0 "$file_name"
}

# Function to generate input data for testing based on the document type
input_data_for_test() {
    local document_type=$1
    case $document_type in
        ("text")
            echo "THIS IS A TEST >>>> and a number of states are starting to adopt them voluntarily special correspondent john delenco of education week reports it takes just 10 minutes to cross through gillette wyoming this small city sits in the northeast corner of the state surrounded by 100s of miles of prairie but schools here in campbell county are on the edge of something big the next generation science standards you are going to build a strand of dna and you are going to decode it and figure out what that dna actually says for christy mathis at sage valley junior high school the new standards are about learning to think like a scientist there is a lot of really good stuff in them every standard is a performance task it is not you know the child needs to memorize these things it is the student needs to be able to do some pretty intense stuff we are analyzing we are critiquing we are."
            ;;
        ("audio")
            get_base64_str "$ROOT_FOLDER/data/test.wav"
            ;;
        ("video")
            get_base64_str "$ROOT_FOLDER/data/test.mp4"
            ;;
        (*)
            echo "Invalid document type" >&2
            exit 1
            ;;
    esac
}

function validate_microservices() {
    # Check if the microservices are running correctly.

    # whisper microservice
    ulimit -s 65536
    validate_services \
        "${host_ip}:7066/v1/asr" \
        '{"asr_result":"well"}' \
        "whisper-service" \
        "whisper-service" \
        "{\"audio\": \"$(input_data_for_test "audio")\"}"

    # Audio2Text service
    validate_services \
        "${host_ip}:9099/v1/audio/transcriptions" \
        '"query":"well"' \
        "dataprep-audio2text" \
        "dataprep-audio2text-service" \
        "{\"byte_str\": \"$(input_data_for_test "audio")\"}"

    # Video2Audio service
    validate_services \
        "${host_ip}:7078/v1/video2audio" \
        "SUQzBAAAAAAAI1RTU0UAAAAPAAADTGF2ZjU4LjI5LjEwMAAAAAAAAAAAAAAA//tQAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAASW5mbwAAAA8AAAAIAAAN3wAtLS0tLS0tLS0tLS1LS0tLS0tLS0tLS0tpaWlpaWlpaWlpaWlph4eHh4eHh4eHh4eHpaWlpaWlpaWlpaWlpcPDw8PDw8PDw8PDw+Hh4eHh4eHh4eHh4eH///////////////8AAAAATGF2YzU4LjU0AAAAAAAAAAAAAAAAJAYwAAAAAAAADd9L18KaAAAAAAAAAAAAAAAAAAAAAP/7kGQAAAMhClSVMEACMOAabaCMAREA" \
        "dataprep-video2audio" \
        "dataprep-video2audio-service" \
        "{\"byte_str\": \"$(input_data_for_test "video")\"}"

    # Docsum Data service - video
    validate_services \
        "${host_ip}:7079/v1/multimedia2text" \
        '"query":"well"' \
        "dataprep-multimedia2text-service" \
        "dataprep-multimedia2text" \
        "{\"video\": \"$(input_data_for_test "video")\"}"

    # Docsum Data service - audio
    validate_services \
        "${host_ip}:7079/v1/multimedia2text" \
        '"query":"well"' \
        "dataprep-multimedia2text-service" \
        "dataprep-multimedia2text" \
        "{\"audio\": \"$(input_data_for_test "audio")\"}"

    # Docsum Data service - text
    validate_services \
        "${host_ip}:7079/v1/multimedia2text" \
        "THIS IS A TEST >>>> and a number of states are starting to adopt them voluntarily special correspondent john delenco" \
        "dataprep-multimedia2text-service" \
        "dataprep-multimedia2text" \
        "{\"text\": \"$(input_data_for_test "text")\"}"

    # tgi for llm service
    validate_services \
        "${host_ip}:8008/generate" \
        "generated_text" \
        "tgi-llm" \
        "tgi-service" \
        '{"inputs":"What is Deep Learning?","parameters":{"max_new_tokens":17, "do_sample": true}}'

    # llm microservice
    validate_services \
        "${host_ip}:9000/v1/chat/docsum" \
        "data: " \
        "llm" \
        "llm-docsum-server" \
        '{"query":"Text Embeddings Inference (TEI) is a toolkit for deploying and serving open source text embeddings and sequence classification models. TEI enables high-performance extraction for the most popular models, including FlagEmbedding, Ember, GTE and E5."}'

}

function validate_megaservice() {
    local SERVICE_NAME="docsum-xeon-backend-server"
    local DOCKER_NAME="docsum-xeon-backend-server"
    local EXPECTED_RESULT="[DONE]"
    local INPUT_DATA="messages=Text Embeddings Inference (TEI) is a toolkit for deploying and serving open source text embeddings and sequence classification models. TEI enables high-performance extraction for the most popular models, including FlagEmbedding, Ember, GTE and E5."
    local URL="${host_ip}:8888/v1/docsum"
    local DATA_TYPE="type=text"

    local HTTP_STATUS=$(curl -s -o /dev/null -w "%{http_code}" -X POST -F "$DATA_TYPE" -F "$INPUT_DATA" -H 'Content-Type: multipart/form-data' "$URL")

    if [ "$HTTP_STATUS" -eq 200 ]; then
        echo "[ $SERVICE_NAME ] HTTP status is 200. Checking content..."

        local CONTENT=$(curl -s -X POST -F "$DATA_TYPE" -F "$INPUT_DATA" -H 'Content-Type: multipart/form-data' "$URL" | tee ${LOG_PATH}/${SERVICE_NAME}.log)

        if echo "$CONTENT" | grep -q "$EXPECTED_RESULT"; then
            echo "[ $SERVICE_NAME ] Content is as expected."
        else
            echo "[ $SERVICE_NAME ] Content does not match the expected result: $CONTENT"
            docker logs ${DOCKER_NAME} >> ${LOG_PATH}/${SERVICE_NAME}.log
            exit 1
        fi
    else
        echo "[ $SERVICE_NAME ] HTTP status is not 200. Received status was $HTTP_STATUS"
        docker logs ${DOCKER_NAME} >> ${LOG_PATH}/${SERVICE_NAME}.log
        exit 1
    fi
    sleep 1s
}

function validate_megaservice_json() {
    # Curl the Mega Service
    echo ""
    echo ">>> Checking text data with Content-Type: application/json"
    validate_services \
        "${host_ip}:8888/v1/docsum" \
        "[DONE]" \
        "docsum-xeon-backend-server" \
        "docsum-xeon-backend-server" \
        '{"type": "text", "messages": "Text Embeddings Inference (TEI) is a toolkit for deploying and serving open source text embeddings and sequence classification models. TEI enables high-performance extraction for the most popular models, including FlagEmbedding, Ember, GTE and E5."}'

    echo ">>> Checking audio data"
    validate_services \
        "${host_ip}:8888/v1/docsum" \
        "[DONE]" \
        "docsum-xeon-backend-server" \
        "docsum-xeon-backend-server" \
        "{\"type\": \"audio\",  \"messages\": \"$(input_data_for_test "audio")\"}"

    echo ">>> Checking video data"
    validate_services \
        "${host_ip}:8888/v1/docsum" \
        "[DONE]" \
        "docsum-xeon-backend-server" \
        "docsum-xeon-backend-server" \
        "{\"type\": \"video\",  \"messages\": \"$(input_data_for_test "video")\"}"

}

function stop_docker() {
    cd $WORKPATH/docker_compose/intel/cpu/xeon/
    docker compose stop && docker compose rm -f
}

function main() {
    echo "==========================================="
    echo ">>>> Stopping any running Docker containers..."
    stop_docker

    echo "==========================================="
    if [[ "$IMAGE_REPO" == "opea" ]]; then
        echo ">>>> Building Docker images..."
        build_docker_images
    fi

    echo "==========================================="
    echo ">>>> Starting Docker services..."
    start_services

    echo "==========================================="
    echo ">>>> Validating microservices..."
    validate_microservices

    echo "==========================================="
    echo ">>>> Validating megaservice..."
    validate_megaservice
    echo ">>>> Validating validate_megaservice_json..."
    validate_megaservice_json

    echo "==========================================="
    echo ">>>> Stopping Docker containers..."
    stop_docker

    echo "==========================================="
    echo ">>>> Pruning Docker system..."
    echo y | docker system prune
    echo ">>>> Docker system pruned successfully."
    echo "==========================================="
}

main
