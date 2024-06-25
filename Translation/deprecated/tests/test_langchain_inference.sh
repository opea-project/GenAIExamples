#!/bin/bash
# Copyright (C) 2024 Intel Corporation
# SPDX-License-Identifier: Apache-2.0

set -xe

function test_env_setup() {
    WORKPATH=$(dirname "$PWD")
    LOG_PATH="$WORKPATH/tests/langchain.log"

    TGI_CONTAINER_NAME="test-tgi-gaudi-server"
    LANGCHAIN_CONTAINER_NAME="test-translation-gaudi"
}

function rename() {
    # Rename the docker container/image names to avoid conflict with local test
    cd ${WORKPATH}
    sed -i "s/tgi-gaudi-server-translation/${TGI_CONTAINER_NAME}/g" serving/tgi_gaudi/launch_tgi_service.sh
}

function launch_tgi_gaudi_service() {
    local card_num=1
    local port=8870
    local model_name="haoranxu/ALMA-13B"

    cd ${WORKPATH}/serving/tgi_gaudi

    bash build_docker.sh
    bash launch_tgi_service.sh $card_num $port $model_name
    sleep 2m
}

function launch_langchain_service() {
    cd $WORKPATH
    local port=8875
    cd langchain/docker
    docker build . --build-arg http_proxy=${http_proxy} --build-arg https_proxy=${http_proxy} -t intel/gen-ai-examples:${LANGCHAIN_CONTAINER_NAME}

    docker run -d --name=${LANGCHAIN_CONTAINER_NAME} --net=host -e TGI_ENDPOINT=http://localhost:8870 -e HUGGINGFACEHUB_API_TOKEN=${HUGGINGFACEHUB_API_TOKEN} \
    -e SERVER_PORT=${port} -e http_proxy=${http_proxy} -e https_proxy=${https_proxy} --ipc=host intel/gen-ai-examples:${LANGCHAIN_CONTAINER_NAME}
    sleep 2m
}


function run_tests() {
    cd $WORKPATH
    local port=8875

    # response: {"target_language":"I love machine translation"}
    curl http://localhost:${port}/v1/translation \
        -X POST \
        -d '{"language_from": "zh","language_to": "en","source_language": "我爱机器翻译。"}' \
        -H 'Content-Type: application/json' > $LOG_PATH

    #response: {"target_language":"我是一名翻译"}
    curl http://localhost:${port}/v1/translation \
        -X POST \
        -d '{"language_from": "English","language_to": "Chinese","source_language": "I am a translator"}' \
        -H 'Content-Type: application/json' >> $LOG_PATH

    # response: {"target_language":"Hallo Welt"}
    curl http://localhost:${port}/v1/translation \
        -X POST \
        -d '{"language_from": "en","language_to": "de","source_language": "hello world"}' \
        -H 'Content-Type: application/json' >> $LOG_PATH

    # response: {"target_language":"Machine learning"}
    curl http://localhost:${port}/v1/translation \
        -X POST \
        -d '{"language_from": "German","language_to": "English","source_language": "Maschinelles Lernen"}' \
        -H 'Content-Type: application/json' >> $LOG_PATH

    # response: {"target_language":"Ég er glöð"}
    curl http://localhost:${port}/v1/translation \
        -X POST \
        -d '{"language_from": "en","language_to": "is","source_language": "I am happy"}' \
        -H 'Content-Type: application/json' >> $LOG_PATH

    # response: {"target_language":"Hello world"}
    curl http://localhost:${port}/v1/translation \
        -X POST \
        -d '{"language_from": "Icelandic","language_to": "English","source_language": "Halló heimur"}' \
        -H 'Content-Type: application/json' >> $LOG_PATH

    # response: {"target_language":"Velká jazyková model"}
    curl http://localhost:${port}/v1/translation \
        -X POST \
        -d '{"language_from": "en","language_to": "cs","source_language": "Large Language Model"}' \
        -H 'Content-Type: application/json' >> $LOG_PATH

    # response: {"target_language":"I'm glad to see you"}
    curl http://localhost:${port}/v1/translation \
        -X POST \
        -d '{"language_from": "Czech","language_to": "English","source_language": "rád tě vidím"}' \
        -H 'Content-Type: application/json' >> $LOG_PATH

    # response: {"target_language":"Хотите танцевать"}
    curl http://localhost:${port}/v1/translation \
        -X POST \
        -d '{"language_from": "English","language_to": "ru","source_language": "Shall we dance?"}' \
        -H 'Content-Type: application/json' >> $LOG_PATH

    # response: {"target_language":"operating system"}
    curl http://localhost:${port}/v1/translation \
        -X POST \
        -d '{"language_from": "Russian","language_to": "English","source_language": "операционная система"}' \
        -H 'Content-Type: application/json' >> $LOG_PATH
}

function check_response() {
    cd $WORKPATH
    echo "Checking response"
    local status=false
    if [[ -f $LOG_PATH ]] && [[ $(grep -c "I love machine translation" $LOG_PATH) != 0 ]] && \
       [[ $(grep -c "我是一名翻译" $LOG_PATH) != 0 ]] && [[ $(grep -c "Hallo Welt" $LOG_PATH) != 0 ]] && \
       [[ $(grep -c "Machine learning" $LOG_PATH) != 0 ]] && [[ $(grep -c "Ég er glöð" $LOG_PATH) != 0 ]] && \
       [[ $(grep -c "Velká jazyková model" $LOG_PATH) != 0 ]] && [[ $(grep -c "I'm glad to see you" $LOG_PATH) != 0 ]] && \
       [[ $(grep -c "operating system" $LOG_PATH) != 0 ]]; then
        status=true
    fi

    if [ $status == false ]; then
        echo "Response check failed, please check the logs in artifacts!"
        exit 1
    else
        echo "Response check succeed!"
    fi
}

function docker_stop() {
    local container_name=$1
    cid=$(docker ps -aq --filter "name=$container_name")
    if [[ ! -z "$cid" ]]; then docker stop $cid && docker rm $cid; fi
}

function main() {
    test_env_setup
    rename
    docker_stop $TGI_CONTAINER_NAME && docker_stop $LANGCHAIN_CONTAINER_NAME && sleep 5s

    launch_tgi_gaudi_service
    launch_langchain_service

    run_tests
    check_response

    docker_stop $TGI_CONTAINER_NAME && docker_stop $LANGCHAIN_CONTAINER_NAME && sleep 5s
    echo y | docker system prune
}

main
