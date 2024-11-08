#!/bin/bash
# Copyright (C) 2024 Intel Corporation
# SPDX-License-Identifier: Apache-2.0

set -x

WORKPATH=$(dirname "$PWD")
LOG_PATH="$WORKPATH/tests"
ip_address=$(hostname -I | awk '{print $1}')
LVM_PORT=5028
LVM_ENDPOINT="http://${ip_address}:${LVM_PORT}/v1/lvm"
WHISPER_MODEL="base"
INDEX_NAME="dataprep"
tmp_dir=$(mktemp -d)
video_name="WeAreGoingOnBullrun"
transcript_fn="${tmp_dir}/${video_name}.vtt"
video_fn="${tmp_dir}/${video_name}.mp4"
audio_name="AudioSample"
audio_fn="${tmp_dir}/${audio_name}.wav"
image_name="apple"
image_fn="${tmp_dir}/${image_name}.png"
caption_fn="${tmp_dir}/${image_name}.txt"

function build_docker_images() {
    cd $WORKPATH
    echo $(pwd)
    docker build --no-cache -t opea/dataprep-multimodal-redis:comps --build-arg https_proxy=$https_proxy --build-arg http_proxy=$http_proxy -f comps/dataprep/multimodal/redis/langchain/Dockerfile .

    if [ $? -ne 0 ]; then
        echo "opea/dataprep-multimodal-redis built fail"
        exit 1
    else
        echo "opea/dataprep-multimodal-redis built successful"
    fi
}

function build_lvm_docker_images() {
    cd $WORKPATH
    echo $(pwd)
    docker build --no-cache -t opea/lvm-llava:comps -f comps/lvms/llava/dependency/Dockerfile .
    if [ $? -ne 0 ]; then
        echo "opea/lvm-llava built fail"
        exit 1
    else
        echo "opea/lvm-llava built successful"
    fi
    docker build --no-cache -t opea/lvm-llava-svc:comps -f comps/lvms/llava/Dockerfile .
    if [ $? -ne 0 ]; then
        echo "opea/lvm-llava-svc built fail"
        exit 1
    else
        echo "opea/lvm-llava-svc built successful"
    fi
}

function start_lvm_service() {
    unset http_proxy
    docker run -d --name="test-comps-lvm-llava" -e http_proxy=$http_proxy -e https_proxy=$https_proxy -p 5029:8399 --ipc=host opea/lvm-llava:comps
    docker run -d --name="test-comps-lvm-llava-svc" -e LVM_ENDPOINT=http://$ip_address:5029 -e http_proxy=$http_proxy -e https_proxy=$https_proxy -p ${LVM_PORT}:9399 --ipc=host opea/lvm-llava-svc:comps
    sleep 5m
}

function start_lvm() {
    cd $WORKPATH
    echo $(pwd)
    echo "Building LVM Docker Images"
    build_lvm_docker_images
    echo "Starting LVM Services"
    start_lvm_service

}

function start_service() {
    # start redis
    echo "Starting Redis server"
    REDIS_PORT=6380
    docker run -d --name="test-redis" -e http_proxy=$http_proxy -e https_proxy=$https_proxy -p $REDIS_PORT:6379 -p 8002:8001 --ipc=host redis/redis-stack:7.2.0-v9

    # start dataprep microservice
    echo "Starting dataprep microservice"
    dataprep_service_port=5013
    REDIS_URL="redis://${ip_address}:${REDIS_PORT}"
    docker run -d --name="test-comps-dataprep-multimodal-redis" -e http_proxy=$http_proxy -e https_proxy=$https_proxy -e REDIS_URL=$REDIS_URL -e INDEX_NAME=$INDEX_NAME -e LVM_ENDPOINT=$LVM_ENDPOINT -p ${dataprep_service_port}:6007 --runtime=runc --ipc=host  opea/dataprep-multimodal-redis:comps

    sleep 1m
}

function prepare_data() {
    echo "Prepare Transcript .vtt"
    cd ${LOG_PATH}
    echo $(pwd)
    echo """WEBVTT

00:00:00.000 --> 00:00:03.400
Last year the smoking tire went on the bull run live rally in the

00:00:03.400 --> 00:00:09.760
2010 Ford SBT Raptor. I liked it so much. I bought one. Here it is. We're going back

00:00:09.760 --> 00:00:12.920
to bull run this year of course we'll help from our friends at Black Magic and

00:00:12.920 --> 00:00:19.560
we're so serious about it. We got two Valentine one radar detectors. Oh yeah.

00:00:19.560 --> 00:00:23.760
So we're all set up and the reason we got two is because we're going to be going

00:00:23.760 --> 00:00:29.920
a little bit faster. We got a 2011 Shelby GT500. The 550 horsepower

00:00:29.920 --> 00:00:34.560
all-luminum V8. We are going to be right in the action bringing you guys a video

00:00:34.560 --> 00:00:40.120
every single day live from the bull run rally July 9th to 16th and the only

00:00:40.120 --> 00:00:45.240
place to watch it is on BlackmagicShine.com. We're right here on the smoking

00:00:45.240 --> 00:00:47.440
tire.""" > ${transcript_fn}

    echo "This is an apple."  > ${caption_fn}

    echo "Downloading Image"
    wget https://github.com/docarray/docarray/blob/main/tests/toydata/image-data/apple.png?raw=true -O ${image_fn}

    echo "Downloading Video"
    wget http://commondatastorage.googleapis.com/gtv-videos-bucket/sample/WeAreGoingOnBullrun.mp4 -O ${video_fn}

    echo "Downloading Audio"
    wget https://github.com/intel/intel-extension-for-transformers/raw/main/intel_extension_for_transformers/neural_chat/assets/audio/sample.wav -O ${audio_fn}

}

function validate_microservice() {
    cd $LOG_PATH

    # test v1/generate_transcripts upload file
    echo "Testing generate_transcripts API"
    URL="http://${ip_address}:$dataprep_service_port/v1/generate_transcripts"
    HTTP_RESPONSE=$(curl --silent --write-out "HTTPSTATUS:%{http_code}" -X POST -F "files=@$video_fn" -F "files=@$audio_fn"  -H 'Content-Type: multipart/form-data' "$URL")
    HTTP_STATUS=$(echo $HTTP_RESPONSE | tr -d '\n' | sed -e 's/.*HTTPSTATUS://')
    RESPONSE_BODY=$(echo $HTTP_RESPONSE | sed -e 's/HTTPSTATUS\:.*//g')
    SERVICE_NAME="dataprep - upload - file"

    if [ "$HTTP_STATUS" -ne "200" ]; then
        echo "[ $SERVICE_NAME ] HTTP status is not 200. Received status was $HTTP_STATUS"
        docker logs test-comps-dataprep-multimodal-redis >> ${LOG_PATH}/dataprep_upload_file.log
        exit 1
    else
        echo "[ $SERVICE_NAME ] HTTP status is 200. Checking content..."
    fi
    if [[ "$RESPONSE_BODY" != *"Data preparation succeeded"* ]]; then
        echo "[ $SERVICE_NAME ] Content does not match the expected result: $RESPONSE_BODY"
        docker logs test-comps-dataprep-multimodal-redis >> ${LOG_PATH}/dataprep_upload_file.log
        exit 1
    else
        echo "[ $SERVICE_NAME ] Content is as expected."
    fi

    # test v1/ingest_with_text upload video file
    echo "Testing ingest_with_text API with video+transcripts"
    URL="http://${ip_address}:$dataprep_service_port/v1/ingest_with_text"

    HTTP_RESPONSE=$(curl --silent --write-out "HTTPSTATUS:%{http_code}" -X POST -F "files=@$video_fn" -F "files=@$transcript_fn" -H 'Content-Type: multipart/form-data' "$URL")
    HTTP_STATUS=$(echo $HTTP_RESPONSE | tr -d '\n' | sed -e 's/.*HTTPSTATUS://')
    RESPONSE_BODY=$(echo $HTTP_RESPONSE | sed -e 's/HTTPSTATUS\:.*//g')
    SERVICE_NAME="dataprep - upload - file"

    if [ "$HTTP_STATUS" -ne "200" ]; then
        echo "[ $SERVICE_NAME ] HTTP status is not 200. Received status was $HTTP_STATUS"
        docker logs test-comps-dataprep-multimodal-redis >> ${LOG_PATH}/dataprep_upload_file.log
        exit 1
    else
        echo "[ $SERVICE_NAME ] HTTP status is 200. Checking content..."
    fi
    if [[ "$RESPONSE_BODY" != *"Data preparation succeeded"* ]]; then
        echo "[ $SERVICE_NAME ] Content does not match the expected result: $RESPONSE_BODY"
        docker logs test-comps-dataprep-multimodal-redis >> ${LOG_PATH}/dataprep_upload_file.log
        exit 1
    else
        echo "[ $SERVICE_NAME ] Content is as expected."
    fi

    # test v1/ingest_with_text upload image file
    echo "Testing ingest_with_text API with image+caption"
    URL="http://${ip_address}:$dataprep_service_port/v1/ingest_with_text"

    HTTP_RESPONSE=$(curl --silent --write-out "HTTPSTATUS:%{http_code}" -X POST -F "files=@$image_fn" -F "files=@$caption_fn" -H 'Content-Type: multipart/form-data' "$URL")
    HTTP_STATUS=$(echo $HTTP_RESPONSE | tr -d '\n' | sed -e 's/.*HTTPSTATUS://')
    RESPONSE_BODY=$(echo $HTTP_RESPONSE | sed -e 's/HTTPSTATUS\:.*//g')
    SERVICE_NAME="dataprep - upload - file"

    if [ "$HTTP_STATUS" -ne "200" ]; then
        echo "[ $SERVICE_NAME ] HTTP status is not 200. Received status was $HTTP_STATUS"
        docker logs test-comps-dataprep-multimodal-redis >> ${LOG_PATH}/dataprep_upload_file.log
        exit 1
    else
        echo "[ $SERVICE_NAME ] HTTP status is 200. Checking content..."
    fi
    if [[ "$RESPONSE_BODY" != *"Data preparation succeeded"* ]]; then
        echo "[ $SERVICE_NAME ] Content does not match the expected result: $RESPONSE_BODY"
        docker logs test-comps-dataprep-multimodal-redis >> ${LOG_PATH}/dataprep_upload_file.log
        exit 1
    else
        echo "[ $SERVICE_NAME ] Content is as expected."
    fi

    # test v1/ingest_with_text with video and image
    echo "Testing ingest_with_text API with both video+transcript and image+caption"
    URL="http://${ip_address}:$dataprep_service_port/v1/ingest_with_text"

    HTTP_RESPONSE=$(curl --silent --write-out "HTTPSTATUS:%{http_code}" -X POST -F "files=@$image_fn" -F "files=@$caption_fn" -F "files=@$video_fn" -F "files=@$transcript_fn" -H 'Content-Type: multipart/form-data' "$URL")
    HTTP_STATUS=$(echo $HTTP_RESPONSE | tr -d '\n' | sed -e 's/.*HTTPSTATUS://')
    RESPONSE_BODY=$(echo $HTTP_RESPONSE | sed -e 's/HTTPSTATUS\:.*//g')
    SERVICE_NAME="dataprep - upload - file"

    if [ "$HTTP_STATUS" -ne "200" ]; then
        echo "[ $SERVICE_NAME ] HTTP status is not 200. Received status was $HTTP_STATUS"
        docker logs test-comps-dataprep-multimodal-redis >> ${LOG_PATH}/dataprep_upload_file.log
        exit 1
    else
        echo "[ $SERVICE_NAME ] HTTP status is 200. Checking content..."
    fi
    if [[ "$RESPONSE_BODY" != *"Data preparation succeeded"* ]]; then
        echo "[ $SERVICE_NAME ] Content does not match the expected result: $RESPONSE_BODY"
        docker logs test-comps-dataprep-multimodal-redis >> ${LOG_PATH}/dataprep_upload_file.log
        exit 1
    else
        echo "[ $SERVICE_NAME ] Content is as expected."
    fi

    # test v1/ingest_with_text with invalid input (.png image with .vtt transcript)
    echo "Testing ingest_with_text API with invalid input (.png and .vtt)"
    URL="http://${ip_address}:$dataprep_service_port/v1/ingest_with_text"

    HTTP_RESPONSE=$(curl --silent --write-out "HTTPSTATUS:%{http_code}" -X POST -F "files=@$image_fn" -F "files=@$transcript_fn" -H 'Content-Type: multipart/form-data' "$URL")
    HTTP_STATUS=$(echo $HTTP_RESPONSE | tr -d '\n' | sed -e 's/.*HTTPSTATUS://')
    RESPONSE_BODY=$(echo $HTTP_RESPONSE | sed -e 's/HTTPSTATUS\:.*//g')
    SERVICE_NAME="dataprep - upload - file"

    if [ "$HTTP_STATUS" -ne "400" ]; then
        echo "[ $SERVICE_NAME ] HTTP status is not 400. Received status was $HTTP_STATUS"
        docker logs test-comps-dataprep-multimodal-redis >> ${LOG_PATH}/dataprep_upload_file.log
        exit 1
    else
        echo "[ $SERVICE_NAME ] HTTP status is 400. Checking content..."
    fi
    if [[ "$RESPONSE_BODY" != *"No caption file found for $image_name"* ]]; then
        echo "[ $SERVICE_NAME ] Content does not match the expected result: $RESPONSE_BODY"
        docker logs test-comps-dataprep-multimodal-redis >> ${LOG_PATH}/dataprep_upload_file.log
        exit 1
    else
        echo "[ $SERVICE_NAME ] Content is as expected."
    fi

    # test v1/generate_captions upload video file
    echo "Testing generate_captions API with video"
    URL="http://${ip_address}:$dataprep_service_port/v1/generate_captions"

    HTTP_RESPONSE=$(curl --silent --write-out "HTTPSTATUS:%{http_code}" -X POST -F "files=@$video_fn" -H 'Content-Type: multipart/form-data' "$URL")
    HTTP_STATUS=$(echo $HTTP_RESPONSE | tr -d '\n' | sed -e 's/.*HTTPSTATUS://')
    RESPONSE_BODY=$(echo $HTTP_RESPONSE | sed -e 's/HTTPSTATUS\:.*//g')
    SERVICE_NAME="dataprep - upload - file"

    if [ "$HTTP_STATUS" -ne "200" ]; then
        echo "[ $SERVICE_NAME ] HTTP status is not 200. Received status was $HTTP_STATUS"
        docker logs test-comps-dataprep-multimodal-redis >> ${LOG_PATH}/dataprep_upload_file.log
        exit 1
    else
        echo "[ $SERVICE_NAME ] HTTP status is 200. Checking content..."
    fi
    if [[ "$RESPONSE_BODY" != *"Data preparation succeeded"* ]]; then
        echo "[ $SERVICE_NAME ] Content does not match the expected result: $RESPONSE_BODY"
        docker logs test-comps-dataprep-multimodal-redis >> ${LOG_PATH}/dataprep_upload_file.log
        exit 1
    else
        echo "[ $SERVICE_NAME ] Content is as expected."
    fi

    # test v1/generate_captions upload image file
    echo "Testing generate_captions API with image"
    URL="http://${ip_address}:$dataprep_service_port/v1/generate_captions"

    HTTP_RESPONSE=$(curl --silent --write-out "HTTPSTATUS:%{http_code}" -X POST -F "files=@$image_fn" -H 'Content-Type: multipart/form-data' "$URL")
    HTTP_STATUS=$(echo $HTTP_RESPONSE | tr -d '\n' | sed -e 's/.*HTTPSTATUS://')
    RESPONSE_BODY=$(echo $HTTP_RESPONSE | sed -e 's/HTTPSTATUS\:.*//g')
    SERVICE_NAME="dataprep - upload - file"

    if [ "$HTTP_STATUS" -ne "200" ]; then
        echo "[ $SERVICE_NAME ] HTTP status is not 200. Received status was $HTTP_STATUS"
        docker logs test-comps-dataprep-multimodal-redis >> ${LOG_PATH}/dataprep_upload_file.log
        exit 1
    else
        echo "[ $SERVICE_NAME ] HTTP status is 200. Checking content..."
    fi
    if [[ "$RESPONSE_BODY" != *"Data preparation succeeded"* ]]; then
        echo "[ $SERVICE_NAME ] Content does not match the expected result: $RESPONSE_BODY"
        docker logs test-comps-dataprep-multimodal-redis >> ${LOG_PATH}/dataprep_upload_file.log
        exit 1
    else
        echo "[ $SERVICE_NAME ] Content is as expected."
    fi

    # test /v1/dataprep/get_files
    echo "Testing get_files API"
    URL="http://${ip_address}:$dataprep_service_port/v1/dataprep/get_files"
    HTTP_RESPONSE=$(curl --silent --write-out "HTTPSTATUS:%{http_code}" -X POST "$URL")
    HTTP_STATUS=$(echo $HTTP_RESPONSE | tr -d '\n' | sed -e 's/.*HTTPSTATUS://')
    RESPONSE_BODY=$(echo $HTTP_RESPONSE | sed -e 's/HTTPSTATUS\:.*//g')
    SERVICE_NAME="dataprep - get"

    if [ "$HTTP_STATUS" -ne "200" ]; then
        echo "[ $SERVICE_NAME ] HTTP status is not 200. Received status was $HTTP_STATUS"
        docker logs test-comps-dataprep-multimodal-redis >> ${LOG_PATH}/dataprep_file.log
        exit 1
    else
        echo "[ $SERVICE_NAME ] HTTP status is 200. Checking content..."
    fi
    if [[ "$RESPONSE_BODY" != *${image_name}* || "$RESPONSE_BODY" != *${video_name}* || "$RESPONSE_BODY" != *${audio_name}* ]]; then
        echo "[ $SERVICE_NAME ] Content does not match the expected result: $RESPONSE_BODY"
        docker logs test-comps-dataprep-multimodal-redis >> ${LOG_PATH}/dataprep_file.log
        exit 1
    else
        echo "[ $SERVICE_NAME ] Content is as expected."
    fi

    # test /v1/dataprep/delete_files
    echo "Testing delete_files API"
    URL="http://${ip_address}:$dataprep_service_port/v1/dataprep/delete_files"
    HTTP_RESPONSE=$(curl --silent --write-out "HTTPSTATUS:%{http_code}" -X POST -d '{"file_path": "dataprep_file.txt"}' -H 'Content-Type: application/json' "$URL")
    HTTP_STATUS=$(echo $HTTP_RESPONSE | tr -d '\n' | sed -e 's/.*HTTPSTATUS://')
    RESPONSE_BODY=$(echo $HTTP_RESPONSE | sed -e 's/HTTPSTATUS\:.*//g')
    SERVICE_NAME="dataprep - del"

    # check response status
    if [ "$HTTP_STATUS" -ne "200" ]; then
        echo "[ $SERVICE_NAME ] HTTP status is not 200. Received status was $HTTP_STATUS"
        docker logs test-comps-dataprep-multimodal-redis >> ${LOG_PATH}/dataprep_del.log
        exit 1
    else
        echo "[ $SERVICE_NAME ] HTTP status is 200. Checking content..."
    fi
    # check response body
    if [[ "$RESPONSE_BODY" != *'{"status":true}'* ]]; then
        echo "[ $SERVICE_NAME ] Content does not match the expected result: $RESPONSE_BODY"
        docker logs test-comps-dataprep-multimodal-redis >> ${LOG_PATH}/dataprep_del.log
        exit 1
    else
        echo "[ $SERVICE_NAME ] Content is as expected."
    fi
}

function stop_docker() {
    cid=$(docker ps -aq --filter "name=test-*")
    if [[ ! -z "$cid" ]]; then docker stop $cid && docker rm $cid && sleep 1s; fi
    # cid=$(docker ps -aq --filter "name=test-comps-lvm*")
    # if [[ ! -z "$cid" ]]; then docker stop $cid && docker rm $cid && sleep 1s; fi

}

function delete_data() {
    cd ${LOG_PATH}
    rm -rf ${tmp_dir}
    sleep 1s
}

function main() {

    stop_docker
    start_lvm
    build_docker_images
    start_service
    prepare_data

    validate_microservice
    delete_data
    stop_docker
    echo y | docker system prune

}

main
