#!/bin/bash
# Copyright (C) 2024 Intel Corporation
# SPDX-License-Identifier: Apache-2.0

set -x

WORKPATH=$(dirname "$PWD")
LOG_PATH="$WORKPATH/tests"
ip_address=$(hostname -I | awk '{print $1}')


function start_service() {
    cd $WORKPATH/comps/vectorstores/langchain/milvus
    rm -rf volumes/

    docker compose up -d

    sleep 60s
}

function validate_vectorstore() {
    PORT="19530"
    COLLECTION_NAME="test_col"

    # test create collection
    echo "[ test create ] creating collection.."
    create_response=$(curl -X POST "http://$ip_address:$PORT/v1/vector/collections/create"  -H "accept: application/json" -H "Content-Type: application/json" -d "{ \"collectionName\": \"$COLLECTION_NAME\", \"dbName\": \"default\", \"dimension\": 2, \"metricType\": \"L2\", \"primaryField\": \"id\", \"vectorField\": \"vector\"}")
    echo $create_response >> ${LOG_PATH}/milvus_create_col.log
    if [[ $(echo $create_response | grep '{"code":200') ]]; then
        echo "[ test create ] create collection succeed"
    else
        echo "[ test create ] create collection failed"
        docker logs milvus-standalone
        exit 1
    fi

    # test insert data
    echo "[ test insert ] inserting data.."
    insert_response=$(curl -X POST "http://$ip_address:$PORT/v1/vector/insert" -H "accept: application/json" -H "Content-Type: application/json" -d "{ \"collectionName\": \"$COLLECTION_NAME\", \"data\": [{\"vector\":[1,2]}] }")
    echo $insert_response >> ${LOG_PATH}/milvus_insert_data.log
    if [[ $(echo $insert_response | grep '{"code":200,"data":{"insertCount":1') ]]; then
        echo "[ test insert ] insert data succeed"
    else
        echo "[ test insert ] insert data failed"
        docker logs milvus-standalone
        exit 1
    fi

    # test search data
    echo "[ test search ] searching data.."
    search_response=$(curl -X POST "http://$ip_address:$PORT/v1/vector/search" -H "accept: application/json" -H "Content-Type: application/json" -d "{ \"collectionName\": \"$COLLECTION_NAME\", \"vector\":[1,2] }")
    echo $search_response>> ${LOG_PATH}/milvus_search_data.log
    if [[ $(echo $search_response | grep '{"code":200,"data":') ]]; then
        echo "[ test search ] search data succeed"
    else
        echo "[ test search ] search data failed"
        docker logs milvus-standalone
        exit 1
    fi
}

function stop_docker() {
    cid=$(docker ps -aq --filter "name=milvus-*")
    if [[ ! -z "$cid" ]]; then docker stop $cid && docker rm $cid && sleep 1s; fi
}

function main() {

    stop_docker

    start_service

    validate_vectorstore

    stop_docker
    echo y | docker system prune

}

main
