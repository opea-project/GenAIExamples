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

function validate_frontend() {
    echo "Validating frontend ..."

    HTTP_STATUS=$(curl -s -o /dev/null -w "%{http_code}" -X GET ${FRONTEND_ENDPOINT})

    if [ "$HTTP_STATUS" -eq 200 ]; then
        echo "Frontend is running correctly."
        local CONTENT=$(curl -s -X GET ${FRONTEND_ENDPOINT})
        if echo "$CONTENT" | grep -q "ok"; then
            echo "Frontend Content is as expected."
        else
            echo "Frontend Content does not match the expected result: $CONTENT"
            docker logs videoqna-xeon-ui-server >> ${LOG_PATH}/ui.log
            exit 1
        fi
    else
        echo "Frontend is not running correctly. Received status was $HTTP_STATUS"
        docker logs videoqna-xeon-ui-server >> ${LOG_PATH}/ui.log
        exit 1
    fi

    echo "==== frontend validated ===="
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

    echo "::group::validate_frontend"
    validate_frontend
    echo "::endgroup::"

    echo "::group::stop_docker"
    stop_docker
    echo "::endgroup::"

    docker system prune -f

}

main
