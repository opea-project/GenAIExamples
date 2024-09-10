#!/bin/bash
# Copyright (C) 2024 Intel Corporation
# SPDX-License-Identifier: Apache-2.0

set -x

WORKPATH=$(dirname "$PWD")
LOG_PATH="$WORKPATH/tests"
ip_address=$(hostname -I | awk '{print $1}')

function build_docker_images() {
    cd $WORKPATH
    docker build --no-cache --build-arg https_proxy=$https_proxy --build-arg http_proxy=$http_proxy -t opea/nginx:comps -f comps/nginx/Dockerfile .
    if [ $? -ne 0 ]; then
        echo "opea/nginx built fail"
        exit 1
    else
        echo "opea/nginx built successful"
    fi
}

function start_service() {
    export NGINX_PORT=80

    # Start Docker Containers
    docker run -d --name test-comps-nginx-server -p 80:80 opea/nginx:comps

    sleep 5s
}

function validate_service() {
    NGINX_PORT=80
    URL="http://${ip_address}:${NGINX_PORT}/home"
    DOCKER_NAME="test-comps-nginx-server"
    SERVICE_NAME="nginx"
    EXPECTED_RESULT="Welcome to nginx!"

    HTTP_RESPONSE=$(curl --silent --write-out "HTTPSTATUS:%{http_code}" "$URL")
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
}

function stop_docker() {
    cid=$(docker ps -aq --filter "name=test-comps-nginx*")
    if [[ ! -z "$cid" ]]; then docker stop $cid && docker rm $cid && sleep 1s; fi
}

function main() {

    stop_docker
    build_docker_images
    start_service

    validate_service

    echo y | docker system prune

}

main
