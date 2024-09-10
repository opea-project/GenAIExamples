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
    docker build -t opea/finetuning-gaudi:latest --build-arg https_proxy=$https_proxy --build-arg http_proxy=$http_proxy -f comps/finetuning/Dockerfile.intel_hpu .
    if [ $? -ne 0 ]; then
        echo "opea/finetuning-gaudi built fail"
        exit 1
    else
        echo "opea/finetuning-gaudi built successful"
    fi
}

function start_service() {
    export no_proxy="localhost,127.0.0.1,"${ip_address}
    docker run -d --name="test-comps-finetuning-gaudi-server" --runtime=habana -e HABANA_VISIBLE_DEVICES=all -p $finetuning_service_port:$finetuning_service_port -p $ray_port:$ray_port -e OMPI_MCA_btl_vader_single_copy_mechanism=none --cap-add=sys_nice --net=host --ipc=host -e https_proxy=$https_proxy -e http_proxy=$http_proxy -e no_proxy=$no_proxy -e HF_TOKEN=$HF_TOKEN opea/finetuning-gaudi:latest
    sleep 1m
}


function validate_microservice() {
    cd $LOG_PATH
    export no_proxy="localhost,127.0.0.1,"${ip_address}

    # test /v1/dataprep upload file
    URL="http://${ip_address}:$finetuning_service_port/v1/files"
    echo '{"query": "A girl with a blue tank top sitting watching three dogs.", "pos": ["A girl is wearing blue."], "neg": ["A girl is with three cats.", "The people are watching a funeral procession.", "The child is wearing black.", "Financing is an issue for us in public schools.", "Kids at a pool.", "It is calming to be assaulted.", "I face a serious problem at eighteen years old. "]}' >> $LOG_PATH/test_embed_data.json
    echo '{"query": "A girl with a blue tank top sitting watching three dogs.", "pos": ["A girl is wearing blue."], "neg": ["A girl is with three cats.", "The people are watching a funeral procession.", "The child is wearing black.", "Financing is an issue for us in public schools.", "Kids at a pool.", "It is calming to be assaulted.", "I face a serious problem at eighteen years old. "]}' >> $LOG_PATH/test_embed_data.json
    echo '{"query": "A girl with a blue tank top sitting watching three dogs.", "pos": ["A girl is wearing blue."], "neg": ["A girl is with three cats.", "The people are watching a funeral procession.", "The child is wearing black.", "Financing is an issue for us in public schools.", "Kids at a pool.", "It is calming to be assaulted.", "I face a serious problem at eighteen years old. "]}' >> $LOG_PATH/test_embed_data.json
    echo '{"query": "A girl with a blue tank top sitting watching three dogs.", "pos": ["A girl is wearing blue."], "neg": ["A girl is with three cats.", "The people are watching a funeral procession.", "The child is wearing black.", "Financing is an issue for us in public schools.", "Kids at a pool.", "It is calming to be assaulted.", "I face a serious problem at eighteen years old. "]}' >> $LOG_PATH/test_embed_data.json
    echo '{"query": "A girl with a blue tank top sitting watching three dogs.", "pos": ["A girl is wearing blue."], "neg": ["A girl is with three cats.", "The people are watching a funeral procession.", "The child is wearing black.", "Financing is an issue for us in public schools.", "Kids at a pool.", "It is calming to be assaulted.", "I face a serious problem at eighteen years old. "]}' >> $LOG_PATH/test_embed_data.json
    echo '{"query": "A girl with a blue tank top sitting watching three dogs.", "pos": ["A girl is wearing blue."], "neg": ["A girl is with three cats.", "The people are watching a funeral procession.", "The child is wearing black.", "Financing is an issue for us in public schools.", "Kids at a pool.", "It is calming to be assaulted.", "I face a serious problem at eighteen years old. "]}' >> $LOG_PATH/test_embed_data.json
    echo '{"query": "A girl with a blue tank top sitting watching three dogs.", "pos": ["A girl is wearing blue."], "neg": ["A girl is with three cats.", "The people are watching a funeral procession.", "The child is wearing black.", "Financing is an issue for us in public schools.", "Kids at a pool.", "It is calming to be assaulted.", "I face a serious problem at eighteen years old. "]}' >> $LOG_PATH/test_embed_data.json
    echo '{"query": "A girl with a blue tank top sitting watching three dogs.", "pos": ["A girl is wearing blue."], "neg": ["A girl is with three cats.", "The people are watching a funeral procession.", "The child is wearing black.", "Financing is an issue for us in public schools.", "Kids at a pool.", "It is calming to be assaulted.", "I face a serious problem at eighteen years old. "]}' >> $LOG_PATH/test_embed_data.json
    echo '{"query": "A girl with a blue tank top sitting watching three dogs.", "pos": ["A girl is wearing blue."], "neg": ["A girl is with three cats.", "The people are watching a funeral procession.", "The child is wearing black.", "Financing is an issue for us in public schools.", "Kids at a pool.", "It is calming to be assaulted.", "I face a serious problem at eighteen years old. "]}' >> $LOG_PATH/test_embed_data.json
    echo '{"query": "A girl with a blue tank top sitting watching three dogs.", "pos": ["A girl is wearing blue."], "neg": ["A girl is with three cats.", "The people are watching a funeral procession.", "The child is wearing black.", "Financing is an issue for us in public schools.", "Kids at a pool.", "It is calming to be assaulted.", "I face a serious problem at eighteen years old. "]}' >> $LOG_PATH/test_embed_data.json

    HTTP_RESPONSE=$(curl --silent --write-out "HTTPSTATUS:%{http_code}" -X POST -F 'file=@./test_embed_data.json' -F purpose="fine-tune" -H 'Content-Type: multipart/form-data' "$URL")
    HTTP_STATUS=$(echo $HTTP_RESPONSE | tr -d '\n' | sed -e 's/.*HTTPSTATUS://')
    RESPONSE_BODY=$(echo $HTTP_RESPONSE | sed -e 's/HTTPSTATUS\:.*//g')
    SERVICE_NAME="finetuning-server - upload - file"

    # Parse the JSON response
    purpose=$(echo "$RESPONSE_BODY" | jq -r '.purpose')
    filename=$(echo "$RESPONSE_BODY" | jq -r '.filename')

    # Define expected values
    expected_purpose="fine-tune"
    expected_filename="test_embed_data.json"

    if [ "$HTTP_STATUS" -ne "200" ]; then
        echo "[ $SERVICE_NAME ] HTTP status is not 200. Received status was $HTTP_STATUS"
        docker logs test-comps-finetuning-gaudi-server > ${LOG_PATH}/finetuning-server_upload_file.log
        exit 1
    else
        echo "[ $SERVICE_NAME ] HTTP status is 200. Checking content..."
    fi
    # Check if the parsed values match the expected values
    if [[ "$purpose" != "$expected_purpose" || "$filename" != "$expected_filename" ]]; then
        echo "[ $SERVICE_NAME ] Content does not match the expected result: $RESPONSE_BODY"
        docker logs test-comps-finetuning-gaudi-server > ${LOG_PATH}/finetuning-server_upload_file.log
        exit 1
    else
        echo "[ $SERVICE_NAME ] Content is as expected."
    fi

    # test /v1/fine_tuning/jobs
    URL="http://${ip_address}:$finetuning_service_port/v1/fine_tuning/jobs"
    HTTP_RESPONSE=$(curl --silent --write-out "HTTPSTATUS:%{http_code}" -X POST -H 'Content-Type: application/json' -d '{"training_file": "test_embed_data.json","model": "BAAI/bge-base-en-v1.5","General":{"task":"embedding","lora_cofig":null,"save_strategy":"epoch"},"Dataset":{"query_max_len":128,"passage_max_len":128,"padding":"max_length"},"Training":{"epochs":3}}' "$URL")
    HTTP_STATUS=$(echo $HTTP_RESPONSE | tr -d '\n' | sed -e 's/.*HTTPSTATUS://')
    RESPONSE_BODY=$(echo $HTTP_RESPONSE | sed -e 's/HTTPSTATUS\:.*//g')
    FINTUNING_ID=$(echo "$RESPONSE_BODY" | jq -r '.id')
    SERVICE_NAME="finetuning-server - create finetuning job"


    if [ "$HTTP_STATUS" -ne "200" ]; then
        echo "[ $SERVICE_NAME ] HTTP status is not 200. Received status was $HTTP_STATUS"
        docker logs test-comps-finetuning-gaudi-server >> ${LOG_PATH}/finetuning-server_create.log
        exit 1
    else
        echo "[ $SERVICE_NAME ] HTTP status is 200. Checking content..."
    fi
    if [[ "$RESPONSE_BODY" != *'{"id":"ft-job'* ]]; then
        echo "[ $SERVICE_NAME ] Content does not match the expected result: $RESPONSE_BODY"
        docker logs test-comps-finetuning-gaudi-server >> ${LOG_PATH}/finetuning-server_create.log
        exit 1
    else
        echo "[ $SERVICE_NAME ] Content is as expected."
    fi

    # test /v1/fine_tuning/jobs/retrieve
    URL="http://${ip_address}:$finetuning_service_port/v1/fine_tuning/jobs/retrieve"
    for((i=1;i<=10;i++));
    do
	HTTP_RESPONSE=$(curl --silent --write-out "HTTPSTATUS:%{http_code}" -X POST -H "Content-Type: application/json" -d '{"fine_tuning_job_id": "'$FINTUNING_ID'"}' "$URL")
	echo $HTTP_RESPONSE
	RESPONSE_BODY=$(echo $HTTP_RESPONSE | sed -e 's/HTTPSTATUS\:.*//g')
	STATUS=$(echo "$RESPONSE_BODY" | jq -r '.status')
	if [[ "$STATUS" == "succeeded" ]]; then
	    echo "training: succeeded."
	    break
	elif [[ "$STATUS" == "failed" ]]; then
	    echo "training: failed."
	    exit 1
	else
	    echo "training: '$STATUS'"
	fi
	sleep 1m
    done

    # test /v1/finetune/list_checkpoints
    URL="http://${ip_address}:$finetuning_service_port/v1/finetune/list_checkpoints"
    HTTP_RESPONSE=$(curl --silent --write-out "HTTPSTATUS:%{http_code}" -X POST -H "Content-Type: application/json" -d '{"fine_tuning_job_id": "'$FINTUNING_ID'"}' "$URL")
    echo $HTTP_RESPONSE
    RESPONSE_BODY=$(echo $HTTP_RESPONSE | sed -e 's/HTTPSTATUS\:.*//g')
    fine_tuned_model_checkpoint=$(echo "$RESPONSE_BODY" | jq -r '.[0].fine_tuned_model_checkpoint')
    echo $fine_tuned_model_checkpoint

    echo "start resume checkpoint............................................."
    # resume checkpoint /v1/fine_tuning/jobs
    URL="http://${ip_address}:$finetuning_service_port/v1/fine_tuning/jobs"
    HTTP_RESPONSE=$(curl --silent --write-out "HTTPSTATUS:%{http_code}" -X POST -H 'Content-Type: application/json' -d '{"training_file": "test_embed_data.json","model": "BAAI/bge-base-en-v1.5","General":{"task":"embedding","lora_cofig":null,"save_strategy":"epoch","resume_from_checkpoint":"'$fine_tuned_model_checkpoint'"},"Dataset":{"query_max_len":128,"passage_max_len":128,"padding":"max_length"},"Training":{"epochs":5}}' "$URL")
    HTTP_STATUS=$(echo $HTTP_RESPONSE | tr -d '\n' | sed -e 's/.*HTTPSTATUS://')
    RESPONSE_BODY=$(echo $HTTP_RESPONSE | sed -e 's/HTTPSTATUS\:.*//g')
    FINTUNING_ID=$(echo "$RESPONSE_BODY" | jq -r '.id')
    SERVICE_NAME="finetuning-server - resume checkpoint"


    if [ "$HTTP_STATUS" -ne "200" ]; then
        echo "[ $SERVICE_NAME ] HTTP status is not 200. Received status was $HTTP_STATUS"
        docker logs test-comps-finetuning-gaudi-server > ${LOG_PATH}/finetuning-server_create.log
        exit 1
    else
        echo "[ $SERVICE_NAME ] HTTP status is 200. Checking content..."
    fi
    if [[ "$RESPONSE_BODY" != *'{"id":"ft-job'* ]]; then
        echo "[ $SERVICE_NAME ] Content does not match the expected result: $RESPONSE_BODY"
        docker logs test-comps-finetuning-gaudi-server > ${LOG_PATH}/finetuning-server_create.log
        exit 1
    else
        echo "[ $SERVICE_NAME ] Content is as expected."
    fi

    # check training status /v1/fine_tuning/jobs/retrieve
    URL="http://${ip_address}:$finetuning_service_port/v1/fine_tuning/jobs/retrieve"
    for((i=1;i<=10;i++));
    do
        HTTP_RESPONSE=$(curl --silent --write-out "HTTPSTATUS:%{http_code}" -X POST -H "Content-Type: application/json" -d '{"fine_tuning_job_id": "'$FINTUNING_ID'"}' "$URL")
        echo $HTTP_RESPONSE
        RESPONSE_BODY=$(echo $HTTP_RESPONSE | sed -e 's/HTTPSTATUS\:.*//g')
        STATUS=$(echo "$RESPONSE_BODY" | jq -r '.status')
        if [[ "$STATUS" == "succeeded" ]]; then
            echo "training: succeeded."
            break
        elif [[ "$STATUS" == "failed" ]]; then
            echo "training: failed."
            exit 1
        else
            echo "training: '$STATUS'"
        fi
        sleep 1m
    done

    # get logs
    docker logs test-comps-finetuning-gaudi-server >> ${LOG_PATH}/finetuning-server_create.log
}

function stop_docker() {
    cid=$(docker ps -aq --filter "name=test-comps-finetuning-gaudi-server*")
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
