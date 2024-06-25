#!/bin/bash
# Copyright (C) 2024 Intel Corporation
# SPDX-License-Identifier: Apache-2.0

set -xe

WORKPATH=$(dirname "$PWD")
ip_address=$(hostname -I | awk '{print $1}')

function build_docker_images() {
    echo "Building the docker images"
    cd $WORKPATH
    docker build -t opea/dataprep-on-ray-redis:latest --build-arg https_proxy=$https_proxy --build-arg http_proxy=$http_proxy -f comps/dataprep/redis/langchain_ray/docker/Dockerfile .
    echo "Docker image built successfully"
}

function start_service() {
    echo "Starting redis microservice"
    # redis endpoint
    docker run -d --name="test-dataprep-redis-server" --runtime=runc -p 6379:6379 -p 8001:8001 redis/redis-stack:7.2.0-v9

    # dataprep-redis-server endpoint
    export REDIS_URL="redis://${ip_address}:6379"
    export INDEX_NAME="rag-redis"
    echo "Starting dataprep-redis-server"
    docker run -d --name="test-dataprep-redis-endpoint" --runtime=runc -p 6007:6007 --ipc=host -e http_proxy=$http_proxy -e https_proxy=$https_proxy -e REDIS_URL=$REDIS_URL -e INDEX_NAME=$INDEX_NAME -e TEI_ENDPOINT=$TEI_ENDPOINT -e TIMEOUT_SECONDS=600 opea/dataprep-on-ray-redis:latest

    sleep 5
    echo "Service started successfully"
}

function validate_microservice() {
    echo "Starting validating the microservice"
    export PATH="${HOME}/miniforge3/bin:$PATH"
    source activate
    python -c "$(cat << 'EOF'
import requests
import json
import os
proxies = {'http':""}
url = 'http://localhost:6007/v1/dataprep'

print("test single file ingestion")
file_list = ["test_data.pdf"]
files = [('files', (f, open(os.path.join("comps/dataprep/redis/", f), 'rb'), 'application/pdf')) for f in file_list]
resp = requests.request('POST', url=url, headers={}, files=files, proxies=proxies)
print(resp.text)
resp.raise_for_status()  # Raise an exception for unsuccessful HTTP status codes
print("Request successful!")

print("test 20 files ingestion")
file_list = ["test_data.pdf"] * 20
files = [('files', (f, open(os.path.join("comps/dataprep/redis/", f), 'rb'), 'application/pdf')) for f in file_list]
resp = requests.request('POST', url=url, headers={}, files=files, proxies=proxies)
print(resp.text)
resp.raise_for_status()  # Raise an exception for unsuccessful HTTP status codes
print("Request successful!")
EOF
)"
    echo "Validation successful"
}

function stop_docker() {
    cid=$(docker ps -aq --filter "name=test-dataprep-redis*")
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
