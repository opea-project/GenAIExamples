#!/bin/bash
# Copyright (C) 2024 Intel Corporation
# SPDX-License-Identifier: Apache-2.0

set -xe

WORKPATH=$(dirname "$PWD")
LOG_PATH="$WORKPATH/tests"
ip_address=$(hostname -I | awk '{print $1}')
tgi_port=8008
tgi_volume=$WORKPATH/data

export model="meta-llama/Meta-Llama-3-8B-Instruct"
export HUGGINGFACEHUB_API_TOKEN=${HUGGINGFACEHUB_API_TOKEN}
export POSTGRES_USER=postgres
export POSTGRES_PASSWORD=testpwd
export POSTGRES_DB=chinook
export TEXTTOSQL_PORT=9090
export TGI_LLM_ENDPOINT="http://${ip_address}:${tgi_port}"


function build_docker_images() {
    echo $WORKPATH
    OPEAPATH=$(realpath "$WORKPATH/../..")

    echo "Building Text to Sql service..."
    cd $OPEAPATH
    rm -rf GenAIComps/
    git clone https://github.com/opea-project/GenAIComps.git
    cd $OPEAPATH/GenAIComps
    docker build --no-cache -t opea/texttosql:latest -f comps/texttosql/langchain/Dockerfile .

    echo "Building React UI service..."
    cd $OPEAPATH/GenAIExamples/DBQnA/ui
    docker build --no-cache -t opea/dbqna-react-ui:latest -f docker/Dockerfile.react .

}

function start_service() {

    docker run --name test-texttosql-postgres --ipc=host -e POSTGRES_USER=${POSTGRES_USER} -e POSTGRES_HOST_AUTH_METHOD=trust -e POSTGRES_DB=${POSTGRES_DB} -e POSTGRES_PASSWORD=${POSTGRES_PASSWORD} -p 5442:5432 -d -v $WORKPATH/docker_compose/intel/cpu/xeon/chinook.sql:/docker-entrypoint-initdb.d/chinook.sql postgres:latest

    docker run -d --name="test-texttosql-tgi-endpoint" --ipc=host -p $tgi_port:80 -v ./data:/data --shm-size 1g -e HUGGINGFACEHUB_API_TOKEN=${HUGGINGFACEHUB_API_TOKEN} -e HF_TOKEN=${HUGGINGFACEHUB_API_TOKEN} -e model=${model} ghcr.io/huggingface/text-generation-inference:2.1.0 --model-id $model


    docker run -d --name="test-texttosql-server" --ipc=host -p $TEXTTOSQL_PORT:8090 --ipc=host -e http_proxy=$http_proxy -e https_proxy=$https_proxy -e TGI_LLM_ENDPOINT=$TGI_LLM_ENDPOINT opea/texttosql:latest

    # check whether tgi is fully ready.
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

    # Run the UI container
    docker run -d --name="test-dbqna-react-ui-server" --ipc=host -p 5174:80 -e no_proxy=$no_proxy -e https_proxy=$https_proxy -e http_proxy=$http_proxy opea/dbqna-react-ui:latest

}

function validate_microservice() {
    result=$(http_proxy="" curl --connect-timeout 5 --max-time 120000 http://${ip_address}:$TEXTTOSQL_PORT/v1/texttosql\
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
    if conda info --envs | grep -q "$conda_env_name"; then
        echo "$conda_env_name exist!"
    else
        conda create -n ${conda_env_name} python=3.12 -y
    fi

    source activate ${conda_env_name}
    echo "[ TEST INFO ]: --------- conda env activated ---------"

    conda install -c conda-forge nodejs=22.6.0 -y
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
    cid=$(docker ps -aq --filter "name=test-*")
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
