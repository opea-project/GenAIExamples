#!/bin/bash
# Copyright (C) 2024 Intel Corporation
# SPDX-License-Identifier: Apache-2.0

set -x

WORKPATH=$(dirname "$PWD")
LOG_PATH="$WORKPATH/tests"
ip_address=$(hostname -I | awk '{print $1}')
tgi_port=8080
tgi_volume=$WORKPATH/data

export model="mistralai/Mistral-7B-Instruct-v0.3"
export HUGGINGFACEHUB_API_TOKEN=${HUGGINGFACEHUB_API_TOKEN}
export POSTGRES_USER=postgres
export POSTGRES_PASSWORD=testpwd
export POSTGRES_DB=chinook

function build_docker_images() {
    cd $WORKPATH
    docker build --no-cache -t opea/text2sql:comps -f comps/text2sql/src/Dockerfile .
}


check_tgi_connection() {
  url=$1
  timeout=1200
  interval=10

  local start_time=$(date +%s)

  while true; do
    if curl --silent --head --fail "$url" > /dev/null; then
      echo "Success"
      return 0
    fi
    echo
    local current_time=$(date +%s)

    local elapsed_time=$((current_time - start_time))

    if [ "$elapsed_time" -ge "$timeout" ]; then
      echo "Timeout,$((timeout / 60))min can't connect $url"
      return 1
    fi
    echo "Waiting for service for $elapsed_time seconds"
    sleep "$interval"
  done
}


function start_service() {

    docker run --name test-text2sql-postgres --ipc=host -e POSTGRES_USER=${POSTGRES_USER} -e POSTGRES_HOST_AUTH_METHOD=trust -e POSTGRES_DB=${POSTGRES_DB} -e POSTGRES_PASSWORD=${POSTGRES_PASSWORD} -p 5442:5432 -d -v $WORKPATH/comps/text2sql/src/chinook.sql:/docker-entrypoint-initdb.d/chinook.sql postgres:latest

    docker run -d --name="test-text2sql-tgi-endpoint" --ipc=host -p $tgi_port:80 -v ./data:/data --shm-size 1g -e HUGGINGFACEHUB_API_TOKEN=${HUGGINGFACEHUB_API_TOKEN} -e HF_TOKEN=${HF_TOKEN} -e model=${model} ghcr.io/huggingface/text-generation-inference:2.1.0 --model-id $model

    export TGI_LLM_ENDPOINT="http://${ip_address}:${tgi_port}"
    text2sql_port=9090
    unset http_proxy
    docker run -d --name="test-text2sql-server" --ipc=host -p ${text2sql_port}:8080 --ipc=host -e http_proxy=$http_proxy -e https_proxy=$https_proxy -e TGI_LLM_ENDPOINT=$TGI_LLM_ENDPOINT opea/text2sql:comps

    # check whether tgi is fully ready
    check_tgi_connection "${TGI_LLM_ENDPOINT}/health"
}

function validate_microservice() {
    text2sql_port=9090
    result=$(http_proxy="" curl http://${ip_address}:${text2sql_port}/v1/text2sql\
        -X POST \
        -d '{"input_text": "Find the total number of Albums.","conn_str": {"user": "'${POSTGRES_USER}'","password": "'${POSTGRES_PASSWORD}'","host": "'${ip_address}'", "port": "5442", "database": "'${POSTGRES_DB}'" }}' \
        -H 'Content-Type: application/json')

    if [[ $result == *"output"* ]]; then
        echo $result
        echo "Result correct."
    else
        echo "Result wrong. Received was $result"
        docker logs test-text2sql-server > ${LOG_PATH}/text2sql.log
        docker logs test-text2sql-tgi-endpoint > ${LOG_PATH}/tgi.log
        exit 1
    fi

}

function stop_docker() {
    cid=$(docker ps -aq --filter "name=test-text2sql*")
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
