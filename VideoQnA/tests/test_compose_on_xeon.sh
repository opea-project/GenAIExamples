#!/bin/bash
# Copyright (C) 2024 Intel Corporation
# SPDX-License-Identifier: Apache-2.0

set -x
IMAGE_REPO=${IMAGE_REPO:-"opea"}
IMAGE_TAG=${IMAGE_TAG:-"latest"}
echo "REGISTRY=IMAGE_REPO=${IMAGE_REPO}"
echo "TAG=IMAGE_TAG=${IMAGE_TAG}"
export REGISTRY=${IMAGE_REPO}
export TAG=${IMAGE_TAG}

WORKPATH=$(dirname "$PWD")
LOG_PATH="$WORKPATH/tests"
ip_address=$(hostname -I | awk '{print $1}')

function build_docker_images() {
    cd $WORKPATH/docker_image_build
    git clone https://github.com/opea-project/GenAIComps.git && cd GenAIComps && git checkout "${opea_branch:-"main"}" && cd ../

    echo "Build all the images with --no-cache, check docker_image_build.log for details..."
    docker compose -f build.yaml build --no-cache > ${LOG_PATH}/docker_image_build.log

    docker pull intellabs/vdms:v2.8.0
    docker images && sleep 1s
}


function start_services() {
    cd $WORKPATH/docker_compose/intel/cpu/xeon/

    source set_env.sh
    docker volume create video-llama-model
    docker compose up vdms-vector-db dataprep -d
    sleep 30s

    # Insert some sample data to the DB
    HTTP_STATUS=$(curl -s -o /dev/null -w "%{http_code}" -X POST http://${ip_address}:6007/v1/dataprep \
    -H "Content-Type: multipart/form-data" \
    -F "files=@./data/op_1_0320241830.mp4")

    if [ "$HTTP_STATUS" -eq 200 ]; then
        echo "Inserted some data at the beginning."
    else
        echo "Inserted failed at the beginning. Received status was $HTTP_STATUS"
        docker logs dataprep-vdms-server >> ${LOG_PATH}/dataprep.log
        exit 1
    fi
    # Bring all the others
    docker compose up -d > ${LOG_PATH}/start_services_with_compose.log
    sleep 1m

    # List of containers running uvicorn
    list=("dataprep-vdms-server" "embedding-multimodal-server" "retriever-vdms-server" "reranking-videoragqna-server" "video-llama-lvm-server" "lvm-video-llama" "videoragqna-xeon-backend-server")

    # Define the maximum time limit in seconds
    TIME_LIMIT=5400
    start_time=$(date +%s)

    check_condition() {
        local item=$1

        if docker logs $item 2>&1 | grep -q "Uvicorn running on"; then
            return 0
        else
            return 1
        fi
    }

    # Main loop
    while [[ ${#list[@]} -gt 0 ]]; do
        # Get the current time
        current_time=$(date +%s)
        elapsed_time=$((current_time - start_time))

        # Exit if time exceeds the limit
        if (( elapsed_time >= TIME_LIMIT )); then
            echo "Time limit exceeded."
            break
        fi

        # Iterate through the list
        for i in "${!list[@]}"; do
            item=${list[i]}
            if check_condition "$item"; then
                echo "Condition met for $item, removing from list."
                unset list[i]
            else
                echo "Condition not met for $item, keeping in list."
            fi
        done

        # Clean up the list to remove empty elements
        list=("${list[@]}")

        # Check if the list is empty
        if [[ ${#list[@]} -eq 0 ]]; then
            echo "List is empty. Exiting."
            break
        fi
        sleep 5m
    done

    if docker logs videoragqna-xeon-ui-server 2>&1 | grep -q "Streamlit app"; then
        return 0
    else
        return 1
    fi

}

function validate_services() {
    local URL="$1"
    local EXPECTED_RESULT="$2"
    local SERVICE_NAME="$3"
    local DOCKER_NAME="$4"
    local INPUT_DATA="$5"

    local HTTP_STATUS=$(curl -s -o /dev/null -w "%{http_code}" -X POST -d "$INPUT_DATA" -H 'Content-Type: application/json' "$URL")
    if [ "$HTTP_STATUS" -eq 200 ]; then
        echo "[ $SERVICE_NAME ] HTTP status is 200. Checking content..."

        local CONTENT=$(curl -s -X POST -d "$INPUT_DATA" -H 'Content-Type: application/json' "$URL" | tee ${LOG_PATH}/${SERVICE_NAME}.log)

        if echo "$CONTENT" | grep -q "$EXPECTED_RESULT"; then
            echo "[ $SERVICE_NAME ] Content is as expected."
        else
            echo "[ $SERVICE_NAME ] Content does not match the expected result: $CONTENT"
            docker logs ${DOCKER_NAME} >> ${LOG_PATH}/${SERVICE_NAME}.log
            exit 1
        fi
    else
        echo "[ $SERVICE_NAME ] HTTP status is not 200. Received status was $HTTP_STATUS"
        docker logs ${DOCKER_NAME} >> ${LOG_PATH}/${SERVICE_NAME}.log
        exit 1
    fi
    sleep 1s
}

function validate_microservices() {
    # Check if the microservices are running correctly.
    cd $WORKPATH/docker_compose/intel/cpu/xeon//data

    # dataprep microservice
    HTTP_STATUS=$(curl -s -o /dev/null -w "%{http_code}" -X POST http://${ip_address}:6007/v1/dataprep \
    -H "Content-Type: multipart/form-data" \
    -F "files=@./op_1_0320241830.mp4")

    if [ "$HTTP_STATUS" -eq 200 ]; then
        echo "Dataprep microservice is running correctly."
    else
        echo "Dataprep microservice is not running correctly. Received status was $HTTP_STATUS"
        docker logs dataprep-vdms-server >> ${LOG_PATH}/dataprep.log
        exit 1
    fi

    # Embedding Microservice
    validate_services \
        "${ip_address}:6000/v1/embeddings" \
        "Sample text" \
        "embedding" \
        "embedding-multimodal-server" \
        '{"text":"Sample text"}'

    # Retriever Microservice
    export your_embedding=$(python -c "import random; embedding = [random.uniform(-1, 1) for _ in range(512)]; print(embedding)")
    validate_services \
        "${ip_address}:7000/v1/retrieval" \
        "retrieved_docs" \
        "retriever" \
        "retriever-vdms-server" \
        "{\"text\":\"test\",\"embedding\":${your_embedding}}"

    # Reranking Microservice
    validate_services \
        "${ip_address}:8000/v1/reranking" \
        "video_url" \
        "reranking" \
        "reranking-videoragqna-server" \
        '{
            "retrieved_docs": [{"doc": [{"text": "retrieved text"}]}],
            "initial_query": "query",
            "top_n": 1,
            "metadata": [
                {"other_key": "value", "video":"top_video_name", "timestamp":"20"}
            ]
        }'

    # LVM Microservice
    validate_services \
        "${ip_address}:9000/v1/lvm" \
        "silence" \
        "lvm" \
        "lvm-video-llama" \
        '{"video_url":"https://github.com/DAMO-NLP-SG/Video-LLaMA/raw/main/examples/silence_girl.mp4","chunk_start": 0,"chunk_duration": 7,"prompt":"What is the person doing?","max_new_tokens": 50}'

    sleep 1s
}

function validate_megaservice() {
    validate_services \
    "${ip_address}:8888/v1/videoragqna" \
    "man" \
    "videoragqna-xeon-backend-server" \
    "videoragqna-xeon-backend-server" \
    '{"messages":"What is the man doing?","stream":"True"}'
}

function validate_frontend() {
    HTTP_STATUS=$(curl -s -o /dev/null -w "%{http_code}" -X GET http://${ip_address}:5173/_stcore/health)

    if [ "$HTTP_STATUS" -eq 200 ]; then
        echo "Frontend is running correctly."
        local CONTENT=$(curl -s -X GET http://${ip_address}:5173/_stcore/health)
        if echo "$CONTENT" | grep -q "ok"; then
            echo "Frontend Content is as expected."
        else
            echo "Frontend Content does not match the expected result: $CONTENT"
            docker logs videoragqna-xeon-ui-server >> ${LOG_PATH}/ui.log
            exit 1
        fi
    else
        echo "Frontend is not running correctly. Received status was $HTTP_STATUS"
        docker logs videoragqna-xeon-ui-server >> ${LOG_PATH}/ui.log
        exit 1
    fi
}

function stop_docker() {
    cd $WORKPATH/docker_compose/intel/cpu/xeon/
    docker compose stop && docker compose rm -f
    docker volume rm video-llama-model
}

function main() {

    stop_docker

    if [[ "$IMAGE_REPO" == "opea" ]]; then build_docker_images; fi
    start_services

    validate_microservices
    validate_megaservice
    validate_frontend

    stop_docker
    echo y | docker system prune

}

main
