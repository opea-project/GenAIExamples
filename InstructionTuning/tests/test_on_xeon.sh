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
    echo '[{"instruction": "Give three tips for staying healthy.", "input": "", "output": "1.Eat a balanced diet and make sure to include plenty of fruits and vegetables. \n2. Exercise regularly to keep your body active and strong. \n3. Get enough sleep and maintain a consistent sleep schedule."},{"instruction": "Give three tips for staying healthy.", "input": "", "output": "1.Eat a balanced diet and make sure to include plenty of fruits and vegetables. \n2. Exercise regularly to keep your body active and strong. \n3. Get enough sleep and maintain a consistent sleep schedule."},{"instruction": "Give three tips for staying healthy.", "input": "", "output": "1.Eat a balanced diet and make sure to include plenty of fruits and vegetables. \n2. Exercise regularly to keep your body active and strong. \n3. Get enough sleep and maintain a consistent sleep schedule."},{"instruction": "Give three tips for staying healthy.", "input": "", "output": "1.Eat a balanced diet and make sure to include plenty of fruits and vegetables. \n2. Exercise regularly to keep your body active and strong. \n3. Get enough sleep and maintain a consistent sleep schedule."},{"instruction": "Give three tips for staying healthy.", "input": "", "output": "1.Eat a balanced diet and make sure to include plenty of fruits and vegetables. \n2. Exercise regularly to keep your body active and strong. \n3. Get enough sleep and maintain a consistent sleep schedule."},{"instruction": "Give three tips for staying healthy.", "input": "", "output": "1.Eat a balanced diet and make sure to include plenty of fruits and vegetables. \n2. Exercise regularly to keep your body active and strong. \n3. Get enough sleep and maintain a consistent sleep schedule."},{"instruction": "Give three tips for staying healthy.", "input": "", "output": "1.Eat a balanced diet and make sure to include plenty of fruits and vegetables. \n2. Exercise regularly to keep your body active and strong. \n3. Get enough sleep and maintain a consistent sleep schedule."},{"instruction": "Give three tips for staying healthy.", "input": "", "output": "1.Eat a balanced diet and make sure to include plenty of fruits and vegetables. \n2. Exercise regularly to keep your body active and strong. \n3. Get enough sleep and maintain a consistent sleep schedule."},{"instruction": "Give three tips for staying healthy.", "input": "", "output": "1.Eat a balanced diet and make sure to include plenty of fruits and vegetables. \n2. Exercise regularly to keep your body active and strong. \n3. Get enough sleep and maintain a consistent sleep schedule."},{"instruction": "Give three tips for staying healthy.", "input": "", "output": "1.Eat a balanced diet and make sure to include plenty of fruits and vegetables. \n2. Exercise regularly to keep your body active and strong. \n3. Get enough sleep and maintain a consistent sleep schedule."},{"instruction": "Give three tips for staying healthy.", "input": "", "output": "1.Eat a balanced diet and make sure to include plenty of fruits and vegetables. \n2. Exercise regularly to keep your body active and strong. \n3. Get enough sleep and maintain a consistent sleep schedule."},{"instruction": "Give three tips for staying healthy.", "input": "", "output": "1.Eat a balanced diet and make sure to include plenty of fruits and vegetables. \n2. Exercise regularly to keep your body active and strong. \n3. Get enough sleep and maintain a consistent sleep schedule."},{"instruction": "Give three tips for staying healthy.", "input": "", "output": "1.Eat a balanced diet and make sure to include plenty of fruits and vegetables. \n2. Exercise regularly to keep your body active and strong. \n3. Get enough sleep and maintain a consistent sleep schedule."},{"instruction": "Give three tips for staying healthy.", "input": "", "output": "1.Eat a balanced diet and make sure to include plenty of fruits and vegetables. \n2. Exercise regularly to keep your body active and strong. \n3. Get enough sleep and maintain a consistent sleep schedule."},{"instruction": "Give three tips for staying healthy.", "input": "", "output": "1.Eat a balanced diet and make sure to include plenty of fruits and vegetables. \n2. Exercise regularly to keep your body active and strong. \n3. Get enough sleep and maintain a consistent sleep schedule."},{"instruction": "Give three tips for staying healthy.", "input": "", "output": "1.Eat a balanced diet and make sure to include plenty of fruits and vegetables. \n2. Exercise regularly to keep your body active and strong. \n3. Get enough sleep and maintain a consistent sleep schedule."},{"instruction": "Give three tips for staying healthy.", "input": "", "output": "1.Eat a balanced diet and make sure to include plenty of fruits and vegetables. \n2. Exercise regularly to keep your body active and strong. \n3. Get enough sleep and maintain a consistent sleep schedule."},{"instruction": "Give three tips for staying healthy.", "input": "", "output": "1.Eat a balanced diet and make sure to include plenty of fruits and vegetables. \n2. Exercise regularly to keep your body active and strong. \n3. Get enough sleep and maintain a consistent sleep schedule."},{"instruction": "Give three tips for staying healthy.", "input": "", "output": "1.Eat a balanced diet and make sure to include plenty of fruits and vegetables. \n2. Exercise regularly to keep your body active and strong. \n3. Get enough sleep and maintain a consistent sleep schedule."},{"instruction": "Give three tips for staying healthy.", "input": "", "output": "1.Eat a balanced diet and make sure to include plenty of fruits and vegetables. \n2. Exercise regularly to keep your body active and strong. \n3. Get enough sleep and maintain a consistent sleep schedule."}]' > $LOG_PATH/test_data.json
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
    HTTP_RESPONSE=$(curl --silent --write-out "HTTPSTATUS:%{http_code}" -X POST -H 'Content-Type: application/json' -d '{"training_file": "test_data.json","model": "facebook/opt-125m"}' "$URL")
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
