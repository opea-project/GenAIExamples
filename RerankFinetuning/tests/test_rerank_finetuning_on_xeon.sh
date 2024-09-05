#!/bin/bash
# Copyright (C) 2024 Intel Corporation
# SPDX-License-Identifier: Apache-2.0

set -x

WORKPATH=$(dirname "$PWD")
LOG_PATH="$WORKPATH/tests"
ip_address=$(hostname -I | awk '{print $1}')
finetuning_service_port=8015
ray_port=8265

function build_docker_images() {
    cd $WORKPATH
    echo $(pwd)
    docker build -t opea/finetuning:latest --build-arg https_proxy=$https_proxy --build-arg http_proxy=$http_proxy --build-arg HF_TOKEN=$HF_TOKEN -f comps/finetuning/docker/Dockerfile_cpu .
    if [ $? -ne 0 ]; then
        echo "opea/finetuning built fail"
        exit 1
    else
        echo "opea/finetuning built successful"
    fi
}

function start_service() {
    export no_proxy="localhost,127.0.0.1,"${ip_address}
    docker run -d --name="finetuning-server" -p $finetuning_service_port:$finetuning_service_port -p $ray_port:$ray_port --runtime=runc --ipc=host -e http_proxy=$http_proxy -e https_proxy=$https_proxy -e no_proxy=$no_proxy opea/finetuning:latest
    sleep 1m
}

function validate_microservice() {
    cd $LOG_PATH
    export no_proxy="localhost,127.0.0.1,"${ip_address}

    # test /v1/dataprep upload file
    URL="http://${ip_address}:$finetuning_service_port/v1/finetune/upload_training_files"
    cat <<EOF > test_data.json
{"query": "Five women walk along a beach wearing flip-flops.", "pos": ["Some women with flip-flops on, are walking along the beach"], "neg": ["The 4 women are sitting on the beach.", "There was a reform in 1996.", "She's not going to court to clear her record.", "The man is talking about hawaii.", "A woman is standing outside.", "The battle was over. ", "A group of people plays volleyball."]}
{"query": "A woman standing on a high cliff on one leg looking over a river.", "pos": ["A woman is standing on a cliff."], "neg": ["A woman sits on a chair.", "George Bush told the Republicans there was no way he would let them even consider this foolish idea, against his top advisors advice.", "The family was falling apart.", "no one showed up to the meeting", "A boy is sitting outside playing in the sand.", "Ended as soon as I received the wire.", "A child is reading in her bedroom."]}
{"query": "Two woman are playing instruments; one a clarinet, the other a violin.", "pos": ["Some people are playing a tune."], "neg": ["Two women are playing a guitar and drums.", "A man is skiing down a mountain.", "The fatal dose was not taken when the murderer thought it would be.", "Person on bike", "The girl is standing, leaning against the archway.", "A group of women watch soap operas.", "No matter how old people get they never forget. "]}
{"query": "A girl with a blue tank top sitting watching three dogs.", "pos": ["A girl is wearing blue."], "neg": ["A girl is with three cats.", "The people are watching a funeral procession.", "The child is wearing black.", "Financing is an issue for us in public schools.", "Kids at a pool.", "It is calming to be assaulted.", "I face a serious problem at eighteen years old. "]}
{"query": "A yellow dog running along a forest path.", "pos": ["a dog is running"], "neg": ["a cat is running", "Steele did not keep her original story.", "The rule discourages people to pay their child support.", "A man in a vest sits in a car.", "Person in black clothing, with white bandanna and sunglasses waits at a bus stop.", "Neither the Globe or Mail had comments on the current state of Canada's road system. ", "The Spring Creek facility is old and outdated."]}
{"query": "It sets out essential activities in each phase along with critical factors related to those activities.", "pos": ["Critical factors for essential activities are set out."], "neg": ["It lays out critical activities but makes no provision for critical factors related to those activities.", "People are assembled in protest.", "The state would prefer for you to do that.", "A girl sits beside a boy.", "Two males are performing.", "Nobody is jumping", "Conrad was being plotted against, to be hit on the head."]}
EOF
    HTTP_RESPONSE=$(curl --silent --write-out "HTTPSTATUS:%{http_code}" -X POST -F 'files=@./test_data.json' -H 'Content-Type: multipart/form-data' "$URL")
    HTTP_STATUS=$(echo $HTTP_RESPONSE | tr -d '\n' | sed -e 's/.*HTTPSTATUS://')
    RESPONSE_BODY=$(echo $HTTP_RESPONSE | sed -e 's/HTTPSTATUS\:.*//g')
    SERVICE_NAME="finetuning-server - upload - file"

    if [ "$HTTP_STATUS" -ne "200" ]; then
        echo "[ $SERVICE_NAME ] HTTP status is not 200. Received status was $HTTP_STATUS"
        docker logs finetuning-server >> ${LOG_PATH}/finetuning-server_upload_file.log
        exit 1
    else
        echo "[ $SERVICE_NAME ] HTTP status is 200. Checking content..."
    fi
    if [[ "$RESPONSE_BODY" != *"Training files uploaded"* ]]; then
        echo "[ $SERVICE_NAME ] Content does not match the expected result: $RESPONSE_BODY"
        docker logs finetuning-server >> ${LOG_PATH}/finetuning-server_upload_file.log
        exit 1
    else
        echo "[ $SERVICE_NAME ] Content is as expected."
    fi

    # test /v1/fine_tuning/jobs
    URL="http://${ip_address}:$finetuning_service_port/v1/fine_tuning/jobs"
    HTTP_RESPONSE=$(curl --silent --write-out "HTTPSTATUS:%{http_code}" -X POST -H 'Content-Type: application/json' -d '{"training_file": "test_data.json","model": "BAAI/bge-reranker-base"}' "$URL")
    HTTP_STATUS=$(echo $HTTP_RESPONSE | tr -d '\n' | sed -e 's/.*HTTPSTATUS://')
    RESPONSE_BODY=$(echo $HTTP_RESPONSE | sed -e 's/HTTPSTATUS\:.*//g')
    SERVICE_NAME="finetuning-server - create finetuning job"

    if [ "$HTTP_STATUS" -ne "200" ]; then
        echo "[ $SERVICE_NAME ] HTTP status is not 200. Received status was $HTTP_STATUS"
        docker logs finetuning-server >> ${LOG_PATH}/finetuning-server_create.log
        exit 1
    else
        echo "[ $SERVICE_NAME ] HTTP status is 200. Checking content..."
    fi
    if [[ "$RESPONSE_BODY" != *'{"id":"ft-job'* ]]; then
        echo "[ $SERVICE_NAME ] Content does not match the expected result: $RESPONSE_BODY"
        docker logs finetuning-server >> ${LOG_PATH}/finetuning-server_create.log
        exit 1
    else
        echo "[ $SERVICE_NAME ] Content is as expected."
    fi

    sleep 3m
}

function stop_docker() {
    cid=$(docker ps -aq --filter "name=finetuning-server*")
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
