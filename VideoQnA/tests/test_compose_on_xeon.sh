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
export host_ip=${ip_address}


function build_docker_images() {
    opea_branch=${opea_branch:-"main"}
    cd $WORKPATH/docker_image_build
    git clone --depth 1 --branch ${opea_branch} https://github.com/opea-project/GenAIComps.git
    pushd GenAIComps
    echo "GenAIComps test commit is $(git rev-parse HEAD)"
    docker build --no-cache -t ${REGISTRY}/comps-base:${TAG} --build-arg https_proxy=$https_proxy --build-arg http_proxy=$http_proxy -f Dockerfile .
    popd && sleep 1s

    # Create .cache directory for cache volume to connect (avoids permission denied error)
    OLD_STRING="mkdir -p /home/user "
    NEW_STRING="mkdir -p /home/user/.cache "
    sed -i "s|$OLD_STRING|$NEW_STRING|g" "GenAIComps/comps/dataprep/src/Dockerfile"
    sed -i "s|$OLD_STRING|$NEW_STRING|g" "GenAIComps/comps/retrievers/src/Dockerfile"
    sed -i "s|$OLD_STRING|$NEW_STRING|g" "GenAIComps/comps/third_parties/clip/src/Dockerfile"

    echo "Build all the images with --no-cache, check docker_image_build.log for details..."
    docker compose -f build.yaml build --no-cache > ${LOG_PATH}/docker_image_build.log 2>&1

    docker images && sleep 1s
}

function start_services() {
    echo "Starting services..."
    cd $WORKPATH/docker_compose/intel/cpu/xeon/
    source ./set_env.sh
    export no_proxy="localhost,127.0.0.1,$ip_address"
    docker volume create video-llama-model
    docker volume create videoqna-cache
    docker compose up vdms-vector-db dataprep -d
    sleep 30s

    # Insert some sample data to the DB
    HTTP_STATUS=$(curl -s -o /dev/null -w "%{http_code}" -X POST ${DATAPREP_INGEST_SERVICE_ENDPOINT} \
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
    list=("dataprep-vdms-server" "clip-embedding-server" "retriever-vdms-server" "reranking-tei-server" "lvm-video-llama" "videoqna-xeon-backend-server")

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
                echo "Condition met for $item, removing from list." >> ${LOG_PATH}/list_check.log
                unset "list[i]"
            else
                echo "Condition not met for $item, keeping in list." >> ${LOG_PATH}/list_check.log
            fi
        done

        # Clean up the list to remove empty elements
        list=("${list[@]}")

        # Check if the list is empty
        if [[ ${#list[@]} -eq 0 ]]; then
            echo "List is empty. Exiting."
            break
        fi
        sleep 2m
    done

    if docker logs videoqna-xeon-ui-server 2>&1 | grep -q "Streamlit app"; then
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

    HTTP_RESPONSE=$(curl -s -w "HTTPSTATUS:%{http_code}" -X POST -d "$INPUT_DATA" -H 'Content-Type: application/json' "$URL")
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
    if [[ "${RESPONSE_BODY}" != *"${EXPECTED_RESULT}"* ]]; then
        echo "[ $SERVICE_NAME ] Content does not match the expected result: $RESPONSE_BODY"
        exit 1
    else
        echo "[ $SERVICE_NAME ] Content is as expected."
    fi
    sleep 1s
}

function validate_microservices() {
    # Check if the microservices are running correctly.
    cd $WORKPATH/docker_compose/intel/cpu/xeon/data

    # dataprep microservice
    echo "Validating Dataprep microservice ..."
    HTTP_STATUS=$(curl -s -o /dev/null -w "%{http_code}" -X POST "${DATAPREP_INGEST_SERVICE_ENDPOINT}" \
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
        ${EMBEDDING_ENDPOINT} \
        '"embedding":[' \
        "embedding" \
        "clip-embedding-server" \
        '{"input":"What is the man doing?"}'

    # Retriever Microservice
    export your_embedding=$(python3 -c "import random; embedding = [random.uniform(-1, 1) for _ in range(512)]; print(embedding)")
    validate_services \
        ${RETRIEVER_ENDPOINT} \
        "retrieved_docs" \
        "retriever" \
        "retriever-vdms-server" \
        "{\"text\":\"What is the man doing?\",\"embedding\":${your_embedding},\"search_type\":\"mmr\", \"k\":4}"

    # Reranking Microservice
    validate_services \
        ${RERANKING_ENDPOINT} \
        "video_url" \
        "reranking" \
        "reranking-tei-server" \
        '{
            "retrieved_docs": [{"doc": [{"text": "retrieved text"}]}],
            "initial_query": "query",
            "top_n": 1,
            "metadata": [
                {"other_key": "value", "video":"top_video_name", "timestamp":"20"}
            ]
        }'

    # Video Llama LVM Backend Service
    result=$(http_proxy="" curl -X POST \
        "${LVM_VIDEO_ENDPOINT}?video_url=https%3A%2F%2Fgithub.com%2FDAMO-NLP-SG%2FVideo-LLaMA%2Fraw%2Fmain%2Fexamples%2Fsilence_girl.mp4&start=0.0&duration=9&prompt=What%20is%20the%20person%20doing%3F&max_new_tokens=150" \
        -H "accept: */*" -d '')

    if [[ $result == *"silence"* ]]; then
        echo "LVM microservice is running correctly."
    else
        echo "LVM microservice is not running correctly. Received status was $HTTP_STATUS"
        docker logs lvm-video-llama >> ${LOG_PATH}/lvm-video-llama.log
        exit 1
    fi

    # LVM Microservice
    validate_services \
        "http://${host_ip}:${LVM_PORT}/v1/lvm" \
        "silence" \
        "lvm" \
        "lvm" \
        '{"video_url":"https://github.com/DAMO-NLP-SG/Video-LLaMA/raw/main/examples/silence_girl.mp4","chunk_start": 0,"chunk_duration": 7,"prompt":"What is the man doing?","max_new_tokens": 50}'

    echo "==== microservices validated ===="
    sleep 1s
}

function validate_megaservice() {
    echo "Validating videoqna-xeon-backend-server ..."

    validate_services \
    ${BACKEND_SERVICE_ENDPOINT} \
    "man" \
    "videoqna-xeon-backend-server" \
    "videoqna-xeon-backend-server" \
    '{"messages":"What is the man doing?","stream":"True"}'

    echo "==== megaservice validated ===="
}

function stop_docker() {
    echo "Stopping docker..."
    cd $WORKPATH/docker_compose/intel/cpu/xeon/
    docker compose stop && docker compose rm -f
    docker volume rm video-llama-model
    docker volume rm videoqna-cache
    echo "Docker stopped."
}

function main() {

    echo "::group::stop_docker"
    stop_docker
    echo "::endgroup::"

    echo "::group::build_docker_images"
    if [[ "$IMAGE_REPO" == "opea" ]]; then build_docker_images; fi
    echo "::endgroup::"

    echo "::group::start_services"
    start_services
    echo "::endgroup::"

    echo "::group::validate_microservices"
    validate_microservices
    echo "::endgroup::"

    echo "::group::validate_megaservice"
    validate_megaservice
    echo "::endgroup::"

    echo "::group::stop_docker"
    stop_docker
    echo "::endgroup::"

    docker system prune -f

}

main
