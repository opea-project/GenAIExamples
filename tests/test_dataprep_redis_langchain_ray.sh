#!/bin/bash
# Copyright (C) 2024 Intel Corporation
# SPDX-License-Identifier: Apache-2.0

set -x

WORKPATH=$(dirname "$PWD")
LOG_PATH="$WORKPATH/tests"
ip_address=$(hostname -I | awk '{print $1}')

function build_docker_images() {
    echo "Building the docker images"
    cd $WORKPATH
    docker build --no-cache -t opea/dataprep-on-ray-redis:comps --build-arg https_proxy=$https_proxy --build-arg http_proxy=$http_proxy -f comps/dataprep/redis/langchain_ray/docker/Dockerfile .
    if $? ; then
        echo "opea/dataprep-on-ray-redis built fail"
        exit 1
    else
        echo "opea/dataprep-on-ray-redis built successful"
    fi
}

function start_service() {
    echo "Starting redis microservice"
    # redis endpoint
    docker run -d --name="test-comps-dataprep-redis-ray" --runtime=runc -p 5038:6379 -p 8004:8001 redis/redis-stack:7.2.0-v9

    # dataprep-redis-server endpoint
    export REDIS_URL="redis://${ip_address}:5038"
    export INDEX_NAME="rag-redis"
    echo "Starting dataprep-redis-server"
    docker run -d --name="test-comps-dataprep-redis-ray-server" --runtime=runc -p 5037:6007 -p 6010:6008 --ipc=host -e http_proxy=$http_proxy -e https_proxy=$https_proxy -e REDIS_URL=$REDIS_URL -e INDEX_NAME=$INDEX_NAME -e TEI_ENDPOINT=$TEI_ENDPOINT -e TIMEOUT_SECONDS=600 opea/dataprep-on-ray-redis:comps

    sleep 10
    echo "Service started successfully"
}

function validate_microservice() {
    cd $LOG_PATH

    dataprep_service_port=5037
    export URL="http://${ip_address}:$dataprep_service_port/v1/dataprep"

    echo "Starting validating the microservice"
    export PATH="${HOME}/miniforge3/bin:$PATH"
    source activate
    echo "Deep learning is a subset of machine learning that utilizes neural networks with multiple layers to analyze various levels of abstract data representations. It enables computers to identify patterns and make decisions with minimal human intervention by learning from large amounts of data." > dataprep_file.txt
    EXIT_CODE=0
    python -c "$(cat << 'EOF'
import requests
import json
import os
proxies = {'http':""}
url = os.environ['URL']

print("test single file ingestion")
file_list = ["dataprep_file.txt"]
files = [('files', (f, open(f, 'rb'))) for f in file_list]
resp = requests.request('POST', url=url, headers={}, files=files, proxies=proxies)
print(resp.text)
resp.raise_for_status()  # Raise an exception for unsuccessful HTTP status codes
print("Request successful!")

print("test 20 files ingestion")
file_list = ["dataprep_file.txt"] * 20
files = [('files', (f, open(f, 'rb'))) for f in file_list]
resp = requests.request('POST', url=url, headers={}, files=files, proxies=proxies)
print(resp.text)
resp.raise_for_status()  # Raise an exception for unsuccessful HTTP status codes
print("Request successful!")

print("test get file structure")
url = 'http://localhost:6010/v1/dataprep/get_file'
resp = requests.request('POST', url=url, headers={}, proxies=proxies)
print(resp.text)
assert "name" in resp.text, "Response does not meet expectation."
print("Request successful!")
EOF
)" || EXIT_CODE=$?
    rm -rf dataprep_file.txt
    if [ $EXIT_CODE -ne 0 ]; then
        echo "[ dataprep ] Validation failed. Entire log as below doc "
        docker container logs test-comps-dataprep-redis-ray-server | tee -a ${LOG_PATH}/dataprep.log
        exit 1
    else
        echo "[ dataprep ] Validation succeed. "
    fi
}


function stop_docker() {
    cid=$(docker ps -aq --filter "name=test-comps-dataprep-redis-ray*")
    echo "Stopping the docker containers "${cid}
    if [[ ! -z "$cid" ]]; then docker stop $cid && docker rm $cid && sleep 1s; fi
    echo "Docker containers stopped successfully"
}

function main() {

    stop_docker

    build_docker_images
    start_service

    validate_microservice

    stop_docker
    echo y | docker system prune 2>&1 > /dev/null

}

main
