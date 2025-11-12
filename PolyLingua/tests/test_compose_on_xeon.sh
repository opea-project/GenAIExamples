#!/bin/bash
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

# Get the directory where this script is located
SCRIPT_DIR=$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)
# PolyLingua root is one level up from tests directory
WORKPATH=$(dirname "$SCRIPT_DIR")
LOG_PATH="$WORKPATH/tests"
ip_address=$(hostname -I | awk '{print $1}')

echo "Script directory: $SCRIPT_DIR"
echo "Working directory: $WORKPATH"

function build_docker_images() {
    opea_branch=${opea_branch:-"main"}
    cd $WORKPATH/docker_image_build

    # Clone GenAIComps
    git clone --depth 1 --branch ${opea_branch} https://github.com/opea-project/GenAIComps.git
    pushd GenAIComps
    echo "GenAIComps test commit is $(git rev-parse HEAD)"
    docker build --no-cache -t ${REGISTRY}/comps-base:${TAG} --build-arg https_proxy=$https_proxy --build-arg http_proxy=$http_proxy -f Dockerfile .
    popd && sleep 1s

    # Build all images using build.yaml
    echo "Building PolyLingua images with --no-cache, check docker_image_build.log for details..."
    service_list="polylingua polylingua-ui llm-textgen"
    docker compose -f build.yaml build ${service_list} --no-cache > ${LOG_PATH}/docker_image_build.log 2>&1

    echo "Image build completed"
    docker images | grep -E "polylingua|llm-textgen"
    sleep 1s
}

function start_services() {
    cd $WORKPATH/docker_compose/intel/cpu/xeon/
    export host_ip=${ip_address}
    export no_proxy="localhost,127.0.0.1,$ip_address"

    # Load environment variables
    if [ ! -f .env ]; then
        echo "Creating .env file..."
        export HF_TOKEN=${HF_TOKEN}
        export LLM_MODEL_ID="swiss-ai/Apertus-8B-Instruct-2509"
        export VLLM_ENDPOINT="http://${host_ip}:8028"
        export LLM_SERVICE_HOST_IP=${host_ip}
        export LLM_SERVICE_PORT=9000
        export MEGA_SERVICE_HOST_IP=${host_ip}
        export MEGA_SERVICE_PORT=8888
        export BACKEND_SERVICE_ENDPOINT="http://${host_ip}:8888"
        export BACKEND_SERVICE_NAME="polylingua"
        export BACKEND_SERVICE_IP=${host_ip}
        export BACKEND_SERVICE_PORT=8888
        export FRONTEND_SERVICE_IP=${host_ip}
        export FRONTEND_SERVICE_PORT=5173
        export NGINX_PORT=80

        cat > .env <<EOF
HF_TOKEN=${HF_TOKEN}
LLM_MODEL_ID=${LLM_MODEL_ID}
MODEL_CACHE=${MODEL_CACHE}
host_ip=${host_ip}
VLLM_ENDPOINT=${VLLM_ENDPOINT}
LLM_SERVICE_HOST_IP=${LLM_SERVICE_HOST_IP}
LLM_SERVICE_PORT=${LLM_SERVICE_PORT}
MEGA_SERVICE_HOST_IP=${MEGA_SERVICE_HOST_IP}
MEGA_SERVICE_PORT=${MEGA_SERVICE_PORT}
BACKEND_SERVICE_ENDPOINT=${BACKEND_SERVICE_ENDPOINT}
BACKEND_SERVICE_NAME=${BACKEND_SERVICE_NAME}
BACKEND_SERVICE_IP=${BACKEND_SERVICE_IP}
BACKEND_SERVICE_PORT=${BACKEND_SERVICE_PORT}
FRONTEND_SERVICE_IP=${FRONTEND_SERVICE_IP}
FRONTEND_SERVICE_PORT=${FRONTEND_SERVICE_PORT}
NGINX_PORT=${NGINX_PORT}
REGISTRY=${REGISTRY}
TAG=${TAG}
EOF
    fi

    # Start Docker Containers
    echo "Starting services with docker compose..."
    docker compose -f compose.yaml up -d > ${LOG_PATH}/start_services_with_compose.log 2>&1

    # Wait for vLLM service to be ready
    echo "Waiting for vLLM service to initialize (this may take several minutes)..."
    n=0
    until [[ "$n" -ge 100 ]]; do
        docker logs vllm-service > ${LOG_PATH}/vllm_service_start.log 2>&1
        if grep -E "Uvicorn running|Application startup complete" ${LOG_PATH}/vllm_service_start.log; then
            echo "vLLM service is ready!"
            break
        fi
        if grep -q "error" ${LOG_PATH}/vllm_service_start.log; then
            echo "Error detected in vLLM service startup"
            cat ${LOG_PATH}/vllm_service_start.log
            exit 1
        fi
        sleep 10s
        n=$((n+1))
    done

    if [[ "$n" -ge 100 ]]; then
        echo "Timeout waiting for vLLM service"
        docker logs vllm-service
        exit 1
    fi

    echo "Waiting additional 10s for all services to stabilize..."
    sleep 10s
}

function validate_services() {
    local URL="$1"
    local EXPECTED_RESULT="$2"
    local SERVICE_NAME="$3"
    local DOCKER_NAME="$4"
    local INPUT_DATA="$5"
    local CONTENT_TYPE="${6:-application/json}"

    echo "Testing $SERVICE_NAME at $URL"

    if [[ "$CONTENT_TYPE" == "multipart/form-data" ]]; then
        # Handle file upload
        local HTTP_STATUS=$(eval curl -s -o /dev/null -w "%{http_code}" -X POST $INPUT_DATA "$URL")

        if [ "$HTTP_STATUS" -eq 200 ]; then
            echo "[ $SERVICE_NAME ] HTTP status is 200. Checking content..."
            local CONTENT=$(eval curl -s -X POST $INPUT_DATA "$URL" | tee ${LOG_PATH}/${SERVICE_NAME}.log)

            if echo "$CONTENT" | grep -q "$EXPECTED_RESULT"; then
                echo "[ $SERVICE_NAME ] ✓ Content is as expected."
            else
                echo "[ $SERVICE_NAME ] ✗ Content does not match expected result"
                echo "Expected: $EXPECTED_RESULT"
                echo "Got: $CONTENT"
                docker logs ${DOCKER_NAME} >> ${LOG_PATH}/${SERVICE_NAME}.log
                exit 1
            fi
        else
            echo "[ $SERVICE_NAME ] ✗ HTTP status is $HTTP_STATUS (expected 200)"
            docker logs ${DOCKER_NAME} >> ${LOG_PATH}/${SERVICE_NAME}.log
            exit 1
        fi
    else
        # Handle JSON request
        local HTTP_STATUS=$(curl -s -o /dev/null -w "%{http_code}" -X POST -d "$INPUT_DATA" -H "Content-Type: $CONTENT_TYPE" "$URL")

        if [ "$HTTP_STATUS" -eq 200 ]; then
            echo "[ $SERVICE_NAME ] HTTP status is 200. Checking content..."

            local CONTENT=$(curl -s -X POST -d "$INPUT_DATA" -H "Content-Type: $CONTENT_TYPE" "$URL" | tee ${LOG_PATH}/${SERVICE_NAME}.log)

            if echo "$CONTENT" | grep -q "$EXPECTED_RESULT"; then
                echo "[ $SERVICE_NAME ] ✓ Content is as expected."
            else
                echo "[ $SERVICE_NAME ] ✗ Content does not match expected result"
                echo "Expected: $EXPECTED_RESULT"
                echo "Got: $CONTENT"
                docker logs ${DOCKER_NAME} >> ${LOG_PATH}/${SERVICE_NAME}.log
                exit 1
            fi
        else
            echo "[ $SERVICE_NAME ] ✗ HTTP status is $HTTP_STATUS (expected 200)"
            docker logs ${DOCKER_NAME} >> ${LOG_PATH}/${SERVICE_NAME}.log
            exit 1
        fi
    fi

    sleep 2s
}

function validate_microservices() {
    echo "======================================"
    echo "Validating Microservices"
    echo "======================================"

    # Test vLLM service health
    echo "Testing vLLM service health..."
    curl -s http://${ip_address}:8028/health || {
        echo "vLLM health check failed"
        exit 1
    }
    echo "✓ vLLM service health check passed"

    # Test vLLM service chat completions
    validate_services \
        "http://${ip_address}:8028/v1/chat/completions" \
        "content" \
        "vllm" \
        "vllm-service" \
        '{"model": "swiss-ai/Apertus-8B-Instruct-2509", "messages": [{"role": "user", "content": "Translate Hello to Spanish"}], "max_tokens": 32}'

    # Test LLM microservice
    validate_services \
        "http://${ip_address}:9000/v1/chat/completions" \
        "data: " \
        "llm" \
        "llm-textgen-server" \
        '{"query":"Translate Hello to Spanish", "max_tokens": 32}'
}

function validate_megaservice() {
    echo "======================================"
    echo "Validating Megaservice"
    echo "======================================"

    # Test 1: Basic text translation (English to Spanish)
    echo "Test 1: Basic English to Spanish translation..."
    validate_services \
        "http://${ip_address}:8888/v1/translation" \
        "choices" \
        "mega-polylingua-basic" \
        "polylingua-xeon-backend-server" \
        '{"language_from": "English", "language_to": "Spanish", "source_language": "Hello, how are you today?"}'

    # Test 2: Language auto-detection
    echo "Test 2: Auto-detection test..."
    validate_services \
        "http://${ip_address}:8888/v1/translation" \
        "choices" \
        "mega-polylingua-auto" \
        "polylingua-xeon-backend-server" \
        '{"language_from": "auto", "language_to": "French", "source_language": "Hello world"}'

    # Test 3: Different language pair (English to German)
    echo "Test 3: English to German translation..."
    validate_services \
        "http://${ip_address}:8888/v1/translation" \
        "choices" \
        "mega-polylingua-german" \
        "polylingua-xeon-backend-server" \
        '{"language_from": "English", "language_to": "German", "source_language": "Good morning"}'
}

function validate_file_translation() {
    echo "======================================"
    echo "Validating File Upload Translation"
    echo "======================================"

    # Create test file
    cd $WORKPATH/tests
    mkdir -p test_data
    echo "Hello, this is a test document for translation. It contains multiple sentences. We want to test if file upload works correctly." > test_data/sample.txt

    # Test file upload translation
    echo "Testing file upload translation..."
    validate_services \
        "http://${ip_address}:8888/v1/translation" \
        "choices" \
        "file-translation" \
        "polylingua-xeon-backend-server" \
        '-F "file=@test_data/sample.txt" -F "language_from=English" -F "language_to=Spanish"' \
        "multipart/form-data"
}

function validate_nginx() {
    echo "======================================"
    echo "Validating Nginx Proxy"
    echo "======================================"

    # Test translation via nginx
    validate_services \
        "http://${ip_address}:80/v1/translation" \
        "choices" \
        "nginx-proxy" \
        "polylingua-nginx-server" \
        '{"language_from": "English", "language_to": "Italian", "source_language": "Thank you very much"}'
}

function validate_ui() {
    echo "======================================"
    echo "Validating UI Service"
    echo "======================================"

    # Check if UI is accessible
    local HTTP_STATUS=$(curl -s -o /dev/null -w "%{http_code}" http://${ip_address}:5173)

    if [ "$HTTP_STATUS" -eq 200 ]; then
        echo "[ UI ] ✓ UI service is accessible"
    else
        echo "[ UI ] ✗ UI service returned HTTP status $HTTP_STATUS"
        docker logs polylingua-ui-server
        exit 1
    fi
}

function stop_docker() {
    cd $WORKPATH/docker_compose/intel/cpu/xeon/
    echo "Stopping services..."
    docker compose -f compose.yaml down
    echo "Services stopped"
}

function main() {
    echo "======================================"
    echo "PolyLingua E2E Test Suite"
    echo "======================================"
    echo "Platform: Intel Xeon (CPU)"
    echo "LLM Backend: vLLM"
    echo "IP Address: ${ip_address}"
    echo "======================================"

    echo "::group::stop_docker"
    stop_docker
    echo "::endgroup::"

    echo "::group::build_docker_images"
    if [[ "$IMAGE_REPO" == "opea" ]]; then
        build_docker_images
    else
        echo "Skipping image build (using IMAGE_REPO=${IMAGE_REPO})"
    fi
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

    echo "::group::validate_file_translation"
    validate_file_translation
    echo "::endgroup::"

    echo "::group::validate_nginx"
    validate_nginx
    echo "::endgroup::"

    echo "::group::validate_ui"
    validate_ui
    echo "::endgroup::"

    echo "::group::stop_docker"
    stop_docker
    echo "::endgroup::"

    docker system prune -f

    echo "======================================"
    echo "✓ All tests passed successfully!"
    echo "======================================"
}

main
