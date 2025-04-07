
# Copyright (C) 2024 Intel Corporation
# SPDX-License-Identifier: Apache-2.0

set -xe
IMAGE_REPO=${IMAGE_REPO:-"opea"}
IMAGE_TAG=${IMAGE_TAG:-"latest"}
echo "REGISTRY=IMAGE_REPO=${IMAGE_REPO}"
echo "TAG=IMAGE_TAG=${IMAGE_TAG}"
export REGISTRY=${IMAGE_REPO}
export TAG=${IMAGE_TAG}
export MODEL_CACHE=${model_cache:-"./data"}

WORKPATH=$(dirname "$PWD")
LOG_PATH="$WORKPATH/tests"
ip_address=$(hostname -I | awk '{print $1}')

function build_docker_images() {
    opea_branch=${opea_branch:-"main"}
    # If the opea_branch isn't main, replace the git clone branch in Dockerfile.
    if [[ "${opea_branch}" != "main" ]]; then
        cd $WORKPATH
        OLD_STRING="RUN git clone --depth 1 https://github.com/opea-project/GenAIComps.git"
        NEW_STRING="RUN git clone --depth 1 --branch ${opea_branch} https://github.com/opea-project/GenAIComps.git"
        find . -type f -name "Dockerfile*" | while read -r file; do
            echo "Processing file: $file"
            sed -i "s|$OLD_STRING|$NEW_STRING|g" "$file"
        done
    fi

    cd $WORKPATH/docker_image_build
    git clone --depth 1 --branch ${opea_branch} https://github.com/opea-project/GenAIComps.git

    git clone https://github.com/HabanaAI/vllm-fork.git && cd vllm-fork
    VLLM_VER=v0.6.6.post1+Gaudi-1.20.0
    echo "Check out vLLM tag ${VLLM_VER}"
    git checkout ${VLLM_VER} &> /dev/null && cd ../

    echo "Build all the images with --no-cache, check docker_image_build.log for details..."
    service_list="codegen codegen-ui llm-textgen vllm-gaudi"
    docker compose -f build.yaml build ${service_list} --no-cache > ${LOG_PATH}/docker_image_build.log

    docker images && sleep 1s
}

function start_services() {
    local compose_profile="$1"
    local llm_container_name="$2"

    cd $WORKPATH/docker_compose/intel/hpu/gaudi
    export http_proxy=${http_proxy}
    export https_proxy=${https_proxy}
    export LLM_MODEL_ID="Qwen/Qwen2.5-Coder-7B-Instruct"
    export LLM_ENDPOINT="http://${ip_address}:8028"
    export HUGGINGFACEHUB_API_TOKEN=${HUGGINGFACEHUB_API_TOKEN}
    export MEGA_SERVICE_HOST_IP=${ip_address}
    export LLM_SERVICE_HOST_IP=${ip_address}
    export BACKEND_SERVICE_ENDPOINT="http://${ip_address}:7778/v1/codegen"
    export NUM_CARDS=1
    export host_ip=${ip_address}

    sed -i "s/backend_address/$ip_address/g" $WORKPATH/ui/svelte/.env

    # Start Docker Containers
    docker compose --profile ${compose_profile} up -d | tee ${LOG_PATH}/start_services_with_compose.log

    n=0
    until [[ "$n" -ge 100 ]]; do
        docker logs ${llm_container_name} > ${LOG_PATH}/llm_service_start.log 2>&1
        if grep -E "Connected|complete" ${LOG_PATH}/llm_service_start.log; then
            break
        fi
        sleep 5s
        n=$((n+1))
    done
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
    sleep 5s
}

function validate_microservices() {
    local llm_container_name="$1"

    # tgi for llm service
    validate_services \
        "${ip_address}:8028/v1/chat/completions" \
        "completion_tokens" \
        "llm-service" \
        "${llm_container_name}" \
        '{"model": "Qwen/Qwen2.5-Coder-7B-Instruct", "messages": [{"role": "user", "content": "def print_hello_world():"}], "max_tokens": 256}'

    # llm microservice
    validate_services \
        "${ip_address}:9000/v1/chat/completions" \
        "data: " \
        "llm" \
        "llm-textgen-gaudi-server" \
        '{"query":"def print_hello_world():"}'

}

function validate_megaservice() {
    # Curl the Mega Service
    validate_services \
        "${ip_address}:7778/v1/codegen" \
        "print" \
        "mega-codegen" \
        "codegen-gaudi-backend-server" \
        '{"messages": "def print_hello_world():"}'

}

function validate_frontend() {
    cd $WORKPATH/ui/svelte
    local conda_env_name="OPEA_e2e"
    export PATH=${HOME}/miniforge3/bin/:$PATH
    if conda info --envs | grep -q "$conda_env_name"; then
        echo "$conda_env_name exist!"
    else
        conda create -n ${conda_env_name} python=3.12 -y
    fi
    source activate ${conda_env_name}

    sed -i "s/localhost/$ip_address/g" playwright.config.ts

    conda install -c conda-forge nodejs=22.6.0 -y
    npm install && npm ci && npx playwright install --with-deps
    node -v && npm -v && pip list

    exit_status=0
    npx playwright test || exit_status=$?

    if [ $exit_status -ne 0 ]; then
        echo "[TEST INFO]: ---------frontend test failed---------"
        exit $exit_status
    else
        echo "[TEST INFO]: ---------frontend test passed---------"
    fi
}

function stop_docker() {
    local docker_profile="$1"

    cd $WORKPATH/docker_compose/intel/hpu/gaudi
    docker compose --profile ${docker_profile} down
}

function main() {
    # all docker docker compose profiles for XEON Platform
    docker_compose_profiles=("codegen-gaudi-vllm" "codegen-gaudi-tgi")
    docker_llm_container_names=("vllm-gaudi-server" "tgi-gaudi-server")

    # get number of profiels and container
    len_profiles=${#docker_compose_profiles[@]}
    len_containers=${#docker_llm_container_names[@]}

    # number of profiels and docker container names must be matched
    if [ ${len_profiles} -ne ${len_containers} ]; then
        echo "Error: number of profiles ${len_profiles} and container names ${len_containers} mismatched"
        exit 1
    fi

    # stop_docker, stop all profiles
    for ((i = 0; i < len_profiles; i++)); do
        stop_docker "${docker_compose_profiles[${i}]}"
    done

    # build docker images
    if [[ "$IMAGE_REPO" == "opea" ]]; then build_docker_images; fi

    # loop all profiles
    for ((i = 0; i < len_profiles; i++)); do
        echo "Process [${i}]: ${docker_compose_profiles[$i]}, ${docker_llm_container_names[${i}]}"
        start_services "${docker_compose_profiles[${i}]}" "${docker_llm_container_names[${i}]}"
        docker ps -a

        validate_microservices "${docker_llm_container_names[${i}]}"
        validate_megaservice
        validate_frontend

        stop_docker "${docker_compose_profiles[${i}]}"
        sleep 5s
    done

    echo y | docker system prune
}

main
