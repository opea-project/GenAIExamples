#!/bin/bash
# Copyright (C) 2024 Intel Corporation
# SPDX-License-Identifier: Apache-2.0

# Exit immediately if a command exits with a non-zero status.
set -e

# --- Script Setup ---
SCRIPT_DIR=$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" &> /dev/null && pwd)
source "${SCRIPT_DIR}/utils.sh"
PROJECT_ROOT=$(cd "${SCRIPT_DIR}/../.." && pwd)
LOG_FILE="${PROJECT_ROOT}/deploy.log"

# --- Configuration ---
EXAMPLE="ChatQnA"
DEVICE="xeon"
REGISTRY="opea"
TAG="latest"
BUILD_ACTION=false
PUSH_ACTION=false
SETUP_REGISTRY_ACTION=false

error_exit() {
    log "ERROR" "$1"
    exit 1
}

usage() {
    echo
    echo "Usage: $0 [OPTIONS]"
    echo
    echo "This script builds and pushes all Docker images for a specified GenAIExample."
    echo
    echo "Options:"
    echo "  -h, --help:                 Show this help message."
    echo "  --example <NAME>:           Specify the example to process (e.g., ChatQnA, CodeTrans, DocSum)."
    echo "                              (default: ${EXAMPLE})"
    echo "  --device <DEVICE>:          Specify the target device (e.g., xeon, gaudi)."
    echo "                              (default: ${DEVICE})"
    echo "  --build:                    Build all images for the specified example."
    echo "  --push:                     Push all built images for the specified example to the registry."
    echo "  --setup-registry:           Set up a local Docker registry (localhost:5000) for this run."
    echo "  --registry <URL>:           Specify the target Docker registry URL (e.g., docker.io/myuser)."
    echo "                              (default: ${REGISTRY})"
    echo "  --tag <TAG>:                Specify the image tag. (default: ${TAG})"
    echo
    echo "Example:"
    echo "  # Build all images for DocSum on Gaudi"
    echo "  bash one_click_deploy/common/update_images.sh --example DocSum --device gaudi --build"
    echo
}

# ==================================================================================
# ==                  EXAMPLE-SPECIFIC CONFIGURATION & FUNCTIONS                ==
# ==================================================================================

# Returns the list of services to be processed for a given example and device.
# If empty, all services in the compose file will be processed.
get_service_list() {
    local example_name=$1
    local device_name=$2
    case "$example_name" in
        "DocSum")
            if [[ "$device_name" == "gaudi" ]]; then
                echo "docsum docsum-gradio-ui whisper llm-docsum vllm-gaudi"
            else
                echo "docsum docsum-gradio-ui whisper llm-docsum vllm"
            fi
            ;;
        "ChatQnA")
            echo "chatqna chatqna-ui dataprep retriever vllm nginx"
            ;;
        "CodeGen")
            if [[ "$device_name" == "gaudi" ]]; then
                echo "codegen codegen-gradio-ui dataprep embedding retriever llm-textgen vllm-gaudi"
            else
                echo "codegen codegen-gradio-ui dataprep embedding retriever llm-textgen vllm"
            fi
            ;;
        "AudioQnA")
            echo "audioqna audioqna-ui whisper speecht5 vllm whisper-gaudi speecht5-gaudi vllm-gaudi"
            ;;
        *)
            # Default to empty, which means docker-compose will process all services
            echo ""
            ;;
    esac
}

# Build function for DocSum - includes custom pre-build steps
build_docsum() {
    local example_path=$1
    local service_list=$2
    local build_dir="${example_path}/docker_image_build"
    log "INFO" "Executing custom build function for DocSum..."
    cd "$build_dir"

    log "INFO" "Cloning required repositories for DocSum..."
    if [ ! -d "GenAIComps" ]; then
        git clone --depth 1 https://github.com/opea-project/GenAIComps.git
    else
        log "INFO" "GenAIComps directory already exists, skipping clone."
    fi
    if [ ! -d "vllm" ]; then
        git clone https://github.com/vllm-project/vllm.git
        cd vllm
        local vllm_ver="v0.8.3" # As per original script
        log "INFO" "Checking out vLLM tag ${vllm_ver}"
        git checkout ${vllm_ver} &> /dev/null
        cd ..
    else
        log "INFO" "vllm directory already exists, skipping clone."
    fi
    if [ ! -d "vllm-fork" ]; then
        git clone https://github.com/HabanaAI/vllm-fork.git && cd vllm-fork
        VLLM_FORK_VER=v0.6.6.post1+Gaudi-1.20.0
        git checkout ${VLLM_FORK_VER} &> /dev/null
        cd ..
    else
        log "INFO" "vllm-fork directory already exists, skipping clone."
    fi

    log "INFO" "Building base image: comps-base (build-time only)"
    pushd GenAIComps
    docker build --no-cache -t ${REGISTRY}/comps-base:${TAG} --build-arg https_proxy=$https_proxy --build-arg http_proxy=$http_proxy -f Dockerfile .
    popd

    log "INFO" "Starting build for specified DocSum services..."
    docker compose -f build.yaml build ${service_list} --no-cache
    cd - > /dev/null
}

# Build function for ChatQnA - standard build
build_chatqna() {
    local example_path=$1
    local service_list=$2
    local build_dir="${example_path}/docker_image_build"
    log "INFO" "Executing standard build function for ChatQnA..."
    cd "$build_dir"
    log "INFO" "Starting build for ChatQnA services..."
    docker compose -f build.yaml build ${service_list} --no-cache
    cd - > /dev/null
}

# Build function for CodeTrans - standard build
build_codetrans() {
    local example_path=$1
    local service_list=$2
    local build_dir="${example_path}/docker_image_build"
    log "INFO" "Executing standard build function for CodeTrans..."
    cd "$build_dir"
    log "INFO" "Starting build for CodeTrans services..."
    docker compose -f build.yaml build ${service_list} --no-cache
    cd - > /dev/null
}

# Build function for CodeGen - standard build
build_codegen() {
    local example_path=$1
    local service_list=$2
    local build_dir="${example_path}/docker_image_build"
    log "INFO" "Executing custom build function for CodeGen..."
    cd "$build_dir"

    log "INFO" "Cloning required repositories for CodeGen..."
    if [ ! -d "GenAIComps" ]; then
        git clone --depth 1 https://github.com/opea-project/GenAIComps.git
    else
        log "INFO" "GenAIComps directory already exists, skipping clone."
    fi
    if [ ! -d "vllm" ]; then
        git clone https://github.com/vllm-project/vllm.git
        cd vllm
        local vllm_ver="v0.8.3" # As per original script
        log "INFO" "Checking out vLLM tag ${vllm_ver}"
        git checkout ${vllm_ver} &> /dev/null
        cd ..
    else
        log "INFO" "vllm directory already exists, skipping clone."
    fi
    if [ ! -d "vllm-fork" ]; then
        git clone https://github.com/HabanaAI/vllm-fork.git && cd vllm-fork
        VLLM_FORK_VER=v0.6.6.post1+Gaudi-1.20.0
        git checkout ${VLLM_FORK_VER} &> /dev/null
        cd ..
    else
        log "INFO" "vllm-fork directory already exists, skipping clone."
    fi

    log "INFO" "Building base image: comps-base (build-time only)"
    pushd GenAIComps
    docker build --no-cache -t ${REGISTRY}/comps-base:${TAG} --build-arg https_proxy=$https_proxy --build-arg http_proxy=$http_proxy -f Dockerfile .
    popd

    log "INFO" "Starting build for specified DocSum services..."
    docker compose -f build.yaml build ${service_list} --no-cache
    cd - > /dev/null
}

# Build function for AudioQnA - standard build
build_audioqna() {
    local example_path=$1
    local service_list=$2
    local build_dir="${example_path}/docker_image_build"
    log "INFO" "Executing custom build function for AudioQnA..."
    cd "$build_dir"

    log "INFO" "Cloning required repositories for AudioQnA..."
    if [ ! -d "GenAIComps" ]; then
        git clone --depth 1 https://github.com/opea-project/GenAIComps.git
    else
        log "INFO" "GenAIComps directory already exists, skipping clone."
    fi
    if [ ! -d "vllm" ]; then
        git clone https://github.com/vllm-project/vllm.git
        cd vllm
        local vllm_ver="v0.8.3" # As per original script
        log "INFO" "Checking out vLLM tag ${vllm_ver}"
        git checkout ${vllm_ver} &> /dev/null && cd ../
    else
        log "INFO" "vllm directory already exists, skipping clone."
    fi
    if [ ! -d "vllm-fork" ]; then
        git clone https://github.com/HabanaAI/vllm-fork.git && cd vllm-fork
        VLLM_FORK_VER=v0.6.6.post1+Gaudi-1.20.0
        git checkout ${VLLM_FORK_VER} &> /dev/null && cd ../
    else
        log "INFO" "vllm-fork directory already exists, skipping clone."
    fi

    log "INFO" "Building base image: comps-base (build-time only)"
    pushd GenAIComps
    docker build --no-cache -t ${REGISTRY}/comps-base:${TAG} --build-arg https_proxy=$https_proxy --build-arg http_proxy=$http_proxy -f Dockerfile .
    popd

    log "INFO" "Starting build for specified DocSum services..."
    docker compose -f build.yaml build ${service_list} --no-cache
    cd - > /dev/null
}

# --- Build Dispatcher ---
# This function calls the correct build function based on the example name.
dispatch_build() {
    local example_name=$1
    local example_path=$2
    local device_name=$3

    section_header "Building Docker Images for ${example_name} on ${device_name}"

    export REGISTRY
    export TAG
    export http_proxy=${http_proxy:-}
    export https_proxy=${https_proxy:-}
    export no_proxy=${no_proxy:-}

    local service_list=$(get_service_list "$example_name" "$device_name")

    case "$example_name" in
        "DocSum")
            build_docsum "$example_path" "$service_list"
            ;;
        "ChatQnA")
            build_chatqna "$example_path" "$service_list"
            ;;
        "CodeTrans")
            build_codetrans "$example_path" "$service_list"
            ;;
        "CodeGen")
            build_codegen "$example_path" "$service_list"
            ;;
        "AudioQnA")
            build_audioqna "$example_path" "$service_list"
            ;;
        *)
            error_exit "No specific build function defined for example '${example_name}'. Please add it to the script."
            ;;
    esac

    log "OK" "Build process for ${example_name} completed successfully."
}

setup_local_registry() {
    section_header "Setting Up Local Registry"
    if [ ! "$(docker ps -q -f name=local-registry)" ]; then
        if [ "$(docker ps -aq -f status=exited -f name=local-registry)" ]; then
            log "INFO" "Restarting existing local-registry container."
            docker start local-registry
        else
            log "INFO" "Creating new local-registry container."
            docker run -d -p 5000:5000 --restart=always --name local-registry registry:2
        fi
    else
        log "INFO" "Local registry is already running."
    fi
    REGISTRY="localhost:5000"
    log "OK" "Registry set to: ${REGISTRY}"
}

push_images() {
    local example_name=$1
    local example_path=$2
    local device_name=$3
    section_header "Pushing Docker Images for ${example_name}"

    cd "${example_path}/docker_image_build"

    log "INFO" "Target Registry: ${REGISTRY}, Tag: ${TAG}"

    export REGISTRY
    export TAG

    local service_list=$(get_service_list "$example_name" "$device_name")

    if [ -z "$service_list" ]; then
        log "INFO" "Pushing all services defined in build.yaml for ${example_name}..."
    else
        log "INFO" "Pushing specified services for ${example_name}: ${service_list}"
    fi

    docker compose -f build.yaml push ${service_list}

    log "OK" "Push completed successfully."
    cd - > /dev/null
}


while [[ $# -gt 0 ]]; do
    case "$1" in
        -h|--help)
            usage
            exit 0
            ;;
        --example)
            EXAMPLE="$2"
            shift 2
            ;;
        --device)
            DEVICE="$2"
            shift 2
            ;;
        --build)
            BUILD_ACTION=true
            shift
            ;;
        --push)
            PUSH_ACTION=true
            shift
            ;;
        --setup-registry)
            SETUP_REGISTRY_ACTION=true
            shift
            ;;
        --registry)
            REGISTRY="$2"
            shift 2
            ;;
        --tag)
            TAG="$2"
            shift 2
            ;;
        *)
            error_exit "Unknown option: $1"
            ;;
    esac
done

if [ "$BUILD_ACTION" = true ] && [ -z "$REGISTRY" ] && [ "$SETUP_REGISTRY_ACTION" = false ]; then
    log "INFO" "No registry specified for build. Defaulting to 'opea' as the registry prefix for local build."
    REGISTRY="opea"
fi

section_header "Image Management Script Started"
EXAMPLE_PATH="${PROJECT_ROOT}/${EXAMPLE}"
if [ ! -d "$EXAMPLE_PATH" ]; then
    error_exit "Example directory not found: '$EXAMPLE_PATH'."
fi

log "INFO" "Project Root: ${PROJECT_ROOT}"
log "INFO" "Selected Example: ${EXAMPLE}"
log "INFO" "Target Device: ${DEVICE}"
log "INFO" "Image Registry: ${REGISTRY:-'Not set'}"
log "INFO" "Image Tag: ${TAG}"

if [ "$SETUP_REGISTRY_ACTION" = true ]; then
    setup_local_registry
fi

if [ "$BUILD_ACTION" = true ]; then
    dispatch_build "$EXAMPLE" "$EXAMPLE_PATH" "$DEVICE"
fi

if [ "$PUSH_ACTION" = true ]; then
    if [ "$REGISTRY" == "opea" ] && [ "$SETUP_REGISTRY_ACTION" = false ]; then
        log "INFO" "Warning: Pushing to default 'opea' registry. Use --registry to specify user/org, e.g., --registry docker.io/opea."
    fi
    push_images "$EXAMPLE" "$EXAMPLE_PATH" "$DEVICE"
fi

if [ "$BUILD_ACTION" = false ] && [ "$PUSH_ACTION" = false ] && [ "$SETUP_REGISTRY_ACTION" = false ]; then
    log "INFO" "No action specified (--build, --push, --setup-registry). Nothing to do."
    usage
fi

log "OK" "Script finished successfully."
