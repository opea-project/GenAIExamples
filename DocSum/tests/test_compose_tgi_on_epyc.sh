#!/bin/bash
# Copyright (C) 2025 Advanced Micro Devices, Inc.
# Copyright (C) 2025 Intel Corporation
# SPDX-License-Identifier: Apache-2.0

set -xe

IMAGE_REPO=${IMAGE_REPO:-"opea"}
IMAGE_TAG=${IMAGE_TAG:-"latest"}
export http_proxy=$http_proxy
export https_proxy=$https_proxy
export host_ip=$(hostname -I | awk '{print $1}')
WORKPATH=$(dirname "$PWD")
mkdir -p "$WORKPATH/tests/logs"
LOG_PATH="$WORKPATH/tests/logs"
echo "REGISTRY=IMAGE_REPO=${IMAGE_REPO}"
echo "TAG=IMAGE_TAG=${IMAGE_TAG}"
export REGISTRY=${IMAGE_REPO}
export TAG=${IMAGE_TAG}

source $WORKPATH/docker_compose/amd/cpu/epyc/set_env.sh
export MODEL_CACHE=${model_cache:-"./data"}

export MAX_INPUT_TOKENS=2048
export MAX_TOTAL_TOKENS=4096

export DocSum_COMPONENT_NAME="OpeaDocSumTgi"

# Get the root folder of the current script
ROOT_FOLDER=$(dirname "$(readlink -f "$0")")

function build_docker_images() {
    opea_branch=${opea_branch:-"main"}
    cd $WORKPATH/docker_image_build
    git clone --depth 1 --branch ${opea_branch} https://github.com/opea-project/GenAIComps.git
    pushd GenAIComps
    echo "GenAIComps test commit is $(git rev-parse HEAD)"
    docker build --no-cache -t ${REGISTRY}/comps-base:${TAG} --build-arg https_proxy=$https_proxy --build-arg http_proxy=$http_proxy -f Dockerfile .
    popd && sleep 1s

    echo "Build all the images with --no-cache, check docker_image_build.log for details..."
    service_list="docsum docsum-gradio-ui whisper llm-docsum"
    docker compose -f build.yaml build ${service_list} --no-cache > ${LOG_PATH}/docker_image_build.log

    docker images && sleep 1s
}

function start_services() {
    cd $WORKPATH/docker_compose/amd/cpu/epyc/
    docker compose -f compose_tgi.yaml up -d > ${LOG_PATH}/start_services_with_compose.log
    sleep 1m
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

function validate_service() {
    local URL="$1"
    local EXPECTED_RESULT="$2"
    local SERVICE_NAME="$3"
    local DOCKER_NAME="$4"
    local VALIDATE_TYPE="$5"
    local INPUT_DATA="$6"
    local FORM_DATA1="$7"
    local FORM_DATA2="$8"
    local FORM_DATA3="$9"
    local FORM_DATA4="${10}"
    local FORM_DATA5="${11}"
    local FORM_DATA6="${12}"

    if [[ $VALIDATE_TYPE == *"json"* ]]; then
        HTTP_RESPONSE=$(curl --silent --write-out "HTTPSTATUS:%{http_code}" -X POST -d "$INPUT_DATA" -H 'Content-Type: application/json' "$URL")
    else
        CURL_CMD=(curl --silent --write-out "HTTPSTATUS:%{http_code}" -X POST -F "$FORM_DATA1" -F "$FORM_DATA2" -F "$FORM_DATA3" -F "$FORM_DATA4" -F "$FORM_DATA5" -H 'Content-Type: multipart/form-data' "$URL")
        if [[ -n "$FORM_DATA6" ]]; then
            CURL_CMD+=(-F "$FORM_DATA6")
        fi
        HTTP_RESPONSE=$("${CURL_CMD[@]}")
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
        echo "EXPECTED_RESULT==> $EXPECTED_RESULT"
        echo "RESPONSE_BODY==> $RESPONSE_BODY"
        echo "[ $SERVICE_NAME ] Content does not match the expected result: $RESPONSE_BODY"
        exit 1
    else
        echo "[ $SERVICE_NAME ] Content is as expected."
    fi

    sleep 1s
}

function validate_microservices() {
    # Check if the microservices are running correctly.

    # tgi for llm service
    validate_service \
        "${host_ip}:${LLM_ENDPOINT_PORT}/generate" \
        "generated_text" \
        "tgi-server" \
        "docsum-epyc-tgi-server" \
        "json" \
        '{"inputs":"What is Deep Learning?","parameters":{"max_new_tokens":17, "do_sample": true}}'

    # llm microservice
    validate_service \
        "${host_ip}:${LLM_PORT}/v1/docsum" \
        "text" \
        "llm-docsum-tgi" \
        "docsum-epyc-llm-server" \
        "json" \
        '{"messages":"Text Embeddings Inference (TEI) is a toolkit for deploying and serving open source text embeddings and sequence classification models. TEI enables high-performance extraction for the most popular models, including FlagEmbedding, Ember, GTE and E5."}'

    # whisper microservice
    ulimit -s 65536
    validate_service \
        "${host_ip}:7066/v1/asr" \
        '{"asr_result":"well"}' \
        "whisper" \
        "docsum-epyc-whisper-server" \
        "json" \
        "{\"audio\": \"$(input_data_for_test "audio")\"}"

}

function validate_megaservice_text() {
    echo ">>> Checking text data in json format"
    validate_service \
        "${host_ip}:${BACKEND_SERVICE_PORT}/v1/docsum" \
        "[DONE]" \
        "docsum-epyc-backend-server" \
        "docsum-epyc-backend-server" \
        "json" \
        '{"type": "text", "messages": "Text Embeddings Inference (TEI) is a toolkit for deploying and serving open source text embeddings and sequence classification models. TEI enables high-performance extraction for the most popular models, including FlagEmbedding, Ember, GTE and E5."}'

    echo ">>> Checking text data in form format, set language=en"
    validate_service \
        "${host_ip}:${BACKEND_SERVICE_PORT}/v1/docsum" \
        "[DONE]" \
        "docsum-epyc-backend-server" \
        "docsum-epyc-backend-server" \
        "media" "" \
        "type=text" \
        "messages=Text Embeddings Inference (TEI) is a toolkit for deploying and serving open source text embeddings and sequence classification models. TEI enables high-performance extraction for the most popular models, including FlagEmbedding, Ember, GTE and E5." \
        "max_tokens=32" \
        "language=en" \
        "stream=True"

    echo ">>> Checking text data in form format, set language=zh"
    validate_service \
        "${host_ip}:${BACKEND_SERVICE_PORT}/v1/docsum" \
        "[DONE]" \
        "docsum-epyc-backend-server" \
        "docsum-epyc-backend-server" \
        "media" "" \
        "type=text" \
        "messages=2024年9月26日，北京——今日，英特尔正式发布英特尔® 至强® 6性能核处理器（代号Granite Rapids），为AI、数据分析、科学计算等计算密集型业务提供卓越性能。" \
        "max_tokens=32" \
        "language=zh" \
        "stream=True"

    echo ">>> Checking text data in form format, upload file"
    validate_service \
        "${host_ip}:${BACKEND_SERVICE_PORT}/v1/docsum" \
        "TEI" \
        "docsum-epyc-backend-server" \
        "docsum-epyc-backend-server" \
        "media" "" \
        "type=text" \
        "messages=" \
        "files=@$ROOT_FOLDER/data/short.txt" \
        "max_tokens=32" \
        "language=en" \
        "stream=False"
}

function validate_megaservice_multimedia() {
    echo ">>> Checking audio data in json format"
    validate_service \
        "${host_ip}:${BACKEND_SERVICE_PORT}/v1/docsum" \
        "well" \
        "docsum-epyc-backend-server" \
        "docsum-epyc-backend-server" \
        "json" \
        "{\"type\": \"audio\",  \"messages\": \"$(input_data_for_test "audio")\", \"stream\": \"False\"}"

    echo ">>> Checking audio data in form format"
    validate_service \
        "${host_ip}:${BACKEND_SERVICE_PORT}/v1/docsum" \
        "you" \
        "docsum-epyc-backend-server" \
        "docsum-epyc-backend-server" \
        "media" "" \
        "type=audio" \
        "messages=UklGRigAAABXQVZFZm10IBIAAAABAAEARKwAAIhYAQACABAAAABkYXRhAgAAAAEA" \
        "max_tokens=32" \
        "language=en" \
        "stream=False"

    echo ">>> Checking audio data in form format, upload file"
    validate_service \
        "${host_ip}:${BACKEND_SERVICE_PORT}/v1/docsum" \
        "well" \
        "docsum-epyc-backend-server" \
        "docsum-epyc-backend-server" \
        "media" "" \
        "type=audio" \
        "messages=" \
        "files=@$ROOT_FOLDER/data/test.wav" \
        "max_tokens=32" \
        "language=en" \
        "stream=False"

    echo ">>> Checking video data in json format"
    validate_service \
        "${host_ip}:${BACKEND_SERVICE_PORT}/v1/docsum" \
        "bye" \
        "docsum-epyc-backend-server" \
        "docsum-epyc-backend-server" \
        "json" \
        "{\"type\": \"video\",  \"messages\": \"$(input_data_for_test "video")\", \"stream\": \"False\"}"

    echo ">>> Checking video data in form format"
    validate_service \
        "${host_ip}:${BACKEND_SERVICE_PORT}/v1/docsum" \
        "bye" \
        "docsum-epyc-backend-server" \
        "docsum-epyc-backend-server" \
        "media" "" \
        "type=video" \
        "messages=\"$(input_data_for_test "video")\"" \
        "max_tokens=32" \
        "language=en" \
        "stream=False"

    echo ">>> Checking video data in form format, upload file"
    validate_service \
        "${host_ip}:${BACKEND_SERVICE_PORT}/v1/docsum" \
        "bye" \
        "docsum-epyc-backend-server" \
        "docsum-epyc-backend-server" \
        "media" "" \
        "type=video" \
        "messages=" \
        "files=@$ROOT_FOLDER/data/test.mp4" \
        "max_tokens=32" \
        "language=en" \
        "stream=False"
}

function validate_megaservice_long_text() {
    echo ">>> Checking long text data in form format, set summary_type=auto"
    validate_service \
        "${host_ip}:${BACKEND_SERVICE_PORT}/v1/docsum" \
        "AMD" \
        "docsum-epyc-backend-server" \
        "docsum-epyc-backend-server" \
        "media" "" \
        "type=text" \
        "messages=" \
        "files=@$ROOT_FOLDER/data/long.txt" \
        "max_tokens=128" \
        "summary_type=auto" \
        "stream=False"

    echo ">>> Checking long text data in form format, set summary_type=stuff"
    validate_service \
        "${host_ip}:${BACKEND_SERVICE_PORT}/v1/docsum" \
        "TEI" \
        "docsum-epyc-backend-server" \
        "docsum-epyc-backend-server" \
        "media" "" \
        "type=text" \
        "messages=" \
        "files=@$ROOT_FOLDER/data/short.txt" \
        "max_tokens=128" \
        "summary_type=stuff" \
        "stream=False"

    echo ">>> Checking long text data in form format, set summary_type=truncate"
    validate_service \
        "${host_ip}:${BACKEND_SERVICE_PORT}/v1/docsum" \
        "AMD" \
        "docsum-epyc-backend-server" \
        "docsum-epyc-backend-server" \
        "media" "" \
        "type=text" \
        "messages=" \
        "files=@$ROOT_FOLDER/data/long.txt" \
        "max_tokens=128" \
        "summary_type=truncate" \
        "stream=False"

    echo ">>> Checking long text data in form format, set summary_type=map_reduce"
    validate_service \
        "${host_ip}:${BACKEND_SERVICE_PORT}/v1/docsum" \
        "AMD" \
        "docsum-epyc-backend-server" \
        "docsum-epyc-backend-server" \
        "media" "" \
        "type=text" \
        "messages=" \
        "files=@$ROOT_FOLDER/data/long.txt" \
        "max_tokens=128" \
        "summary_type=map_reduce" \
        "stream=False"

    echo ">>> Checking long text data in form format, set summary_type=refine"
    validate_service \
        "${host_ip}:${BACKEND_SERVICE_PORT}/v1/docsum" \
        "AMD" \
        "docsum-epyc-backend-server" \
        "docsum-epyc-backend-server" \
        "media" "" \
        "type=text" \
        "messages=" \
        "files=@$ROOT_FOLDER/data/long.txt" \
        "max_tokens=128" \
        "summary_type=refine" \
        "stream=False"
}

function stop_docker() {
    cd $WORKPATH/docker_compose/amd/cpu/epyc/
    docker compose -f compose_tgi.yaml stop && docker compose rm -f
}

function main() {

    echo "::group:: Stopping any running Docker containers..."
    stop_docker
    echo "::endgroup::"

    echo "::group::build_docker_images"
    if [[ "$IMAGE_REPO" == "opea" ]]; then build_docker_images; fi
    echo "::endgroup::"

    echo "::group::start_services"
    start_services
    echo "::endgroup::"

    echo "::group:: Validating microservices"
    validate_microservices
    echo "::endgroup::"

    echo "::group::validate_megaservice_text"
    validate_megaservice_text
    echo "::endgroup::"

    echo "::group::validate_megaservice_multimedia"
    validate_megaservice_multimedia
    echo "::endgroup::"

    echo "::group::validate_megaservice_long_text"
    validate_megaservice_long_text
    echo "::endgroup::"

    echo "::group::stop_docker"
    stop_docker
    echo "::endgroup::"

    docker system prune -f

}

main
