#!/bin/bash
# Copyright (C) 2024 Intel Corporation
# SPDX-License-Identifier: Apache-2.0

# set -xe

IMAGE_REPO=${IMAGE_REPO:-"opea"}
IMAGE_TAG=${IMAGE_TAG:-"latest"}
echo "REGISTRY=IMAGE_REPO=${IMAGE_REPO}"
echo "TAG=IMAGE_TAG=${IMAGE_TAG}"

WORKPATH=$(dirname "$PWD")
LOG_PATH="$WORKPATH/tests"

host_ip=$(hostname -I | awk '{print $1}')

export REGISTRY=${IMAGE_REPO}
export TAG=${IMAGE_TAG}
export no_proxy="${no_proxy},${host_ip}"

export V2A_SERVICE_HOST_IP=${host_ip}
export V2A_ENDPOINT=http://$host_ip:7078

export A2T_ENDPOINT=http://$host_ip:7066
export A2T_SERVICE_HOST_IP=${host_ip}
export A2T_SERVICE_PORT=9099

export DATA_ENDPOINT=http://$host_ip:7079
export DATA_SERVICE_HOST_IP=${host_ip}
export DATA_SERVICE_PORT=7079

# Get the root folder of the current script
ROOT_FOLDER=$(dirname "$(readlink -f "$0")")

function build_docker_images() {
    cd $WORKPATH
    echo "Current working directory: $(pwd)"

    # Array of Docker build configurations
    declare -A docker_builds=(
        ["opea/whisper:comps"]="comps/asr/whisper/dependency/Dockerfile"
        ["opea/a2t:comps"]="comps/dataprep/multimedia2text/audio2text/Dockerfile"
        ["opea/v2a:comps"]="comps/dataprep/multimedia2text/video2audio/Dockerfile"
        ["opea/multimedia2text:comps"]="comps/dataprep/multimedia2text/Dockerfile"
    )

    # Loop through the array and build each Docker image
    for image in "${!docker_builds[@]}"; do
        dockerfile=${docker_builds[$image]}
        echo "Building Docker image: $image from Dockerfile: $dockerfile"

        docker build --no-cache -t $image --build-arg https_proxy=$https_proxy --build-arg http_proxy=$http_proxy -f $dockerfile .

        if [ $? -ne 0 ]; then
            echo "$image build failed"
            exit 1
        else
            echo "$image build successful"
        fi
    done

    # List Docker images and wait for 1 second
    docker images && sleep 1s
}

function start_services() {

    docker run -d -p 7066:7066 --name="test-comps-mm-whisper-service" --ipc=host -e http_proxy=$http_proxy -e https_proxy=$https_proxy opea/whisper:comps
    if [ $? -ne 0 ]; then
        echo "opea/whisper service fail to start"
        exit 1
    else
        echo "opea/whisper start successful"
    fi


    docker run -d -p 9199:9099 --name="test-comps-mm-a2t-service" --ipc=host -e http_proxy=$http_proxy -e https_proxy=$https_proxy -e A2T_ENDPOINT=http://$host_ip:7066 opea/a2t:comps
    if [ $? -ne 0 ]; then
        echo "opea/a2t service fail to start"
        exit 1
    else
        echo "opea/a2t start successful"
    fi

    docker run -d -p 7078:7078 --name="test-comps-mm-v2a-service" --ipc=host -e http_proxy=$http_proxy -e https_proxy=$https_proxy opea/v2a:comps
    if [ $? -ne 0 ]; then
        echo "opea/v2a service fail to start"
        exit 1
    else
        echo "opea/v2a start successful"
    fi


    docker run -d -p 7079:7079 --name="test-comps-mm-multimedia2text-service" --ipc=host -e http_proxy=$http_proxy -e https_proxy=$https_proxy \
        -e A2T_ENDPOINT=http://$host_ip:7066 \
        -e V2A_ENDPOINT=http://$host_ip:7078 \
        opea/multimedia2text:comps

    if [ $? -ne 0 ]; then
        echo "opea/multimedia2text service fail to start"
        exit 1
    else
        echo "opea/multimedia2text start successful"
    fi

    sleep 120s

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
            # get_base64_str "$ROOT_FOLDER/data/test.wav"
            get_base64_str "$WORKPATH/comps/dataprep/multimedia2text/data/intel_short.wav"
            ;;
        ("video")
            # get_base64_str "$ROOT_FOLDER/data/test.mp4"
            get_base64_str "$WORKPATH/comps/dataprep/multimedia2text/data/intel_short.mp4"
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
        "${host_ip}:9199/v1/audio/transcriptions" \
        '"query":"well"' \
        "a2t" \
        "a2t-service" \
        "{\"byte_str\": \"$(input_data_for_test "audio")\"}"

    # Video2Audio service
    validate_services \
        "${host_ip}:7078/v1/video2audio" \
        "SUQzBAAAAAAAI1RTU0UAAAAPAAADTGF2ZjU4LjI5LjEwMAAAAAAAAAAAAAAA//tQAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAASW5mbwAAAA8AAAAIAAAN3wAtLS0tLS0tLS0tLS1LS0tLS0tLS0tLS0tpaWlpaWlpaWlpaWlph4eHh4eHh4eHh4eHpaWlpaWlpaWlpaWlpcPDw8PDw8PDw8PDw+Hh4eHh4eHh4eHh4eH///////////////8AAAAATGF2YzU4LjU0AAAAAAAAAAAAAAA" \
        "v2a" \
        "v2a-service" \
        "{\"byte_str\": \"$(input_data_for_test "video")\"}"

    # Docsum Data service - video
    validate_services \
        "${host_ip}:7079/v1/multimedia2text" \
        '"query":"well' \
        "multimedia2text-service" \
        "multimedia2text" \
        "{\"video\": \"$(input_data_for_test "video")\"}"

    # Docsum Data service - audio
    validate_services \
        "${host_ip}:7079/v1/multimedia2text" \
        '"query":"well' \
        "multimedia2text-service" \
        "multimedia2text" \
        "{\"audio\": \"$(input_data_for_test "audio")\"}"

    # Docsum Data service - text
    validate_services \
        "${host_ip}:7079/v1/multimedia2text" \
        "THIS IS A TEST >>>> and a number of states are starting to adopt them voluntarily special correspondent john delenco" \
        "multimedia2text-service" \
        "multimedia2text" \
        "{\"text\": \"$(input_data_for_test "text")\"}"

}

function stop_docker() {
    cid=$(docker ps -aq --filter "name=test-comps-mm-*")
    if [[ ! -z "$cid" ]]; then docker stop $cid && docker rm $cid && sleep 1s; fi
    echo "All specified services have been stopped and removed."
}

function main() {

    stop_docker
    if [[ "$IMAGE_REPO" == "opea" ]]; then build_docker_images; fi
    start_services
    validate_microservices
    stop_docker
    echo y | docker system prune
}

main
