#!/bin/bash
# Copyright (C) 2024 Intel Corporation
# SPDX-License-Identifier: Apache-2.0

set -xe

WORKPATH=$(dirname "$PWD")
LOG_PATH="$WORKPATH/tests"
ip_address="10.223.24.242"
tgi_port=8080
tgi_volume=$WORKPATH/data

export model="mistralai/Mistral-7B-Instruct-v0.3"
export HUGGINGFACEHUB_API_TOKEN=${HUGGINGFACEHUB_API_TOKEN}
export POSTGRES_USER=postgres
export POSTGRES_PASSWORD=testpwd
export POSTGRES_DB=chinook

function build_docker_images() {
    echo $WORKPATH
    OPEAPATH=$(realpath "$WORKPATH/../..")
    cd $OPEAPATH
    # git clone --branch texttosql https://github.com/yogeshmpandey/GenAIComps.git
    cd GenAIComps
    echo $PWD
    docker build --no-cache -t opea/texttosql:comps -f comps/texttosql/langchain/Dockerfile .
}

function start_service() {

    docker run --name test-texttosql-postgres --ipc=host -e POSTGRES_USER=${POSTGRES_USER} -e POSTGRES_HOST_AUTH_METHOD=trust -e POSTGRES_DB=${POSTGRES_DB} -e POSTGRES_PASSWORD=${POSTGRES_PASSWORD} -p 5442:5432 -d -v $WORKPATH/comps/texttosql/langchain/chinook.sql:/docker-entrypoint-initdb.d/chinook.sql postgres:latest

    docker run -d --name="test-texttosql-tgi-endpoint" --ipc=host -p $tgi_port:80 -v ./data:/data --shm-size 1g -e HUGGINGFACEHUB_API_TOKEN=${HUGGINGFACEHUB_API_TOKEN} -e HF_TOKEN=${HF_TOKEN} -e model=${model} ghcr.io/huggingface/text-generation-inference:2.1.0 --model-id $model

    export TGI_LLM_ENDPOINT="http://${ip_address}:${tgi_port}"
    texttosql_port=9090
    unset http_proxy
    docker run -d --name="test-texttosql-server" --ipc=host -p ${texttosql_port}:8090 --ipc=host -e http_proxy=$http_proxy -e https_proxy=$https_proxy -e TGI_LLM_ENDPOINT=$TGI_LLM_ENDPOINT opea/texttosql:comps

    # check whether tgi is fully ready
    n=0
    until [[ "$n" -ge 100 ]] || [[ $ready == true ]]; do
        docker logs test-texttosql-tgi-endpoint > ${LOG_PATH}/tgi.log
        n=$((n+1))
        if grep -q Connected ${LOG_PATH}/tgi.log; then
            break
        fi
        sleep 5s
    done
    sleep 5s
}

function validate_microservice() {
    texttosql_port=9090
    echo "http://${ip_address}:${texttosql_port}/v1/texttosql"
    result=$(http_proxy="" curl --connect-timeout 5 --max-time 120000 http://${ip_address}:${texttosql_port}/v1/texttosql\
        -X POST \
        -d '{"input_text": "Find the total number of Albums.","conn_str": {"user": "'${POSTGRES_USER}'","password": "'${POSTGRES_PASSWORD}'","host": "'${ip_address}'", "port": "5442", "database": "'${POSTGRES_DB}'" }}' \
        -H 'Content-Type: application/json')

    if [[ $result == *"output"* ]]; then
        echo $result
        echo "Result correct."
    else
        echo "Result wrong. Received was $result"
        docker logs test-texttosql-server > ${LOG_PATH}/texttosql.log
        docker logs test-texttosql-tgi-endpoint > ${LOG_PATH}/tgi.log
        exit 1
    fi

}

function validate_frontend() {
    echo "[ TEST INFO ]: --------- frontend test started ---------"
    cd $WORKPATH/ui/react
    local conda_env_name="OPEA_e2e"
    export PATH=${HOME}/miniforge3/bin/:$PATH
#    conda remove -n ${conda_env_name} --all -y
    conda create -n ${conda_env_name} python=3.12 -y

    conda info --envs
    source activate ${conda_env_name}
    echo "[ TEST INFO ]: --------- conda env activated ---------"

#    conda install -c conda-forge nodejs -y
    npm install && npm ci
    node -v && npm -v && pip list

    exit_status=0
    npm run test || exit_status=$?

    if [ $exit_status -ne 0 ]; then
        echo "[TEST INFO]: ---------frontend test failed---------"
        exit $exit_status
    else
        echo "[TEST INFO]: ---------frontend test passed---------"
    fi
}

function stop_docker() {
    cid=$(docker ps -aq --filter "name=test-texttosql*")
    if [[ ! -z "$cid" ]]; then docker stop $cid && docker rm $cid && sleep 1s; fi
}

function main() {

    stop_docker

    build_docker_images
    start_service

    validate_microservice
    validate_frontend

    stop_docker
    echo y | docker system prune

}

main