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
            if [[ "$device_name" == "gaudi" ]]; then
                echo "audioqna audioqna-ui whisper-gaudi speecht5-gaudi vllm-gaudi"
            else
                echo "audioqna audioqna-ui whisper speecht5 vllm"
            fi
            ;;
        "FaqGen")
            if [[ "$device_name" == "gaudi" ]]; then
                echo "chatqna chatqna-ui llm-faqgen dataprep retriever nginx vllm-gaudi"
            else
                echo "chatqna chatqna-ui llm-faqgen dataprep retriever nginx vllm"
            fi
            ;;
        "CodeTrans")
            if [[ "$device_name" == "gaudi" ]]; then
                echo "codetrans codetrans-ui llm-textgen vllm-gaudi nginx"
            else
                echo "codetrans codetrans-ui llm-textgen vllm nginx"
            fi
            ;;
        "VisualQnA")
            if [[ "$device_name" == "gaudi" ]]; then
                echo "visualqna visualqna-ui lvm nginx vllm-gaudi"
            else
                echo "visualqna visualqna-ui lvm nginx vllm"
            fi
            ;;
        "AgentQnA")
            if [[ "$device_name" == "gaudi" ]]; then
                echo "agent agent-ui vllm-gaudi"
            else
                echo "agent agent-ui"
            fi
            ;;
        *)
            # Default to empty, which means docker-compose will process all services
            echo ""
            ;;
    esac
}

# --- Example-Specific Build Configurations ---
# Defines the configurations for cloning prerequisite repositories.
# A generic build function will use these settings.

VLLM_FORK_VER=v0.8.5.post1+Gaudi-1.21.3

# Config for examples using vLLM v0.8.3
declare -A VLLM_8_3_CONFIG=(
    [clone_vllm]=true
    [vllm_version]="v0.8.3"
    [clone_vllm_fork]=true
    [vllm_fork_version]="${VLLM_FORK_VER}"
)

# Config for examples using vLLM v0.9.0.1
declare -A VLLM_9_0_1_CONFIG=(
    [clone_vllm]=true
    [vllm_version]="v0.9.0.1"
    [clone_vllm_fork]=true
    [vllm_fork_version]="${VLLM_FORK_VER}"
)

# Config for AgentQnA, which only needs vllm-fork
declare -A AGENT_CONFIG=(
    [clone_vllm]=false
    [clone_vllm_fork]=true
    [vllm_fork_version]="${VLLM_FORK_VER}"
)

# --- Generic Build Function ---
# This single function handles the build process for any example,
# using the configurations defined above.
execute_build() {
    local example_name=$1
    local example_path=$2
    local service_list=$3
    # Use nameref to access the associative array by its name
    declare -n config=$4

    local build_dir="${example_path}/docker_image_build"
    log "INFO" "Executing generic build for ${example_name}..."
    cd "$build_dir"

    log "INFO" "Cloning required repositories for ${example_name}..."
    # Always clone GenAIComps
    if [ ! -d "GenAIComps" ]; then
        git clone --depth 1 https://github.com/opea-project/GenAIComps.git
    else
        log "INFO" "GenAIComps directory already exists, skipping clone."
    fi

    # Conditionally clone vllm based on config
    if [[ ${config[clone_vllm]:-false} == true ]]; then
        if [ ! -d "vllm" ]; then
            git clone https://github.com/vllm-project/vllm.git
            cd vllm
            log "INFO" "Checking out vLLM tag ${config[vllm_version]}"
            git checkout "${config[vllm_version]}" &> /dev/null
            cd ..
        else
            log "INFO" "vllm directory already exists, skipping clone."
        fi
    fi

    # Conditionally clone vllm-fork based on config
    if [[ ${config[clone_vllm_fork]:-false} == true ]]; then
        if [ ! -d "vllm-fork" ]; then
            git clone https://github.com/HabanaAI/vllm-fork.git && cd vllm-fork
            log "INFO" "Checking out vllm-fork tag ${config[vllm_fork_version]}"
            git checkout "${config[vllm_fork_version]}" &> /dev/null
            cd ..
        else
            log "INFO" "vllm-fork directory already exists, skipping clone."
        fi
    fi

    log "INFO" "Building base image: comps-base (build-time only)"
    pushd GenAIComps
    docker build --no-cache -t "${REGISTRY}/comps-base:${TAG}" \
        --build-arg https_proxy="$https_proxy" \
        --build-arg http_proxy="$http_proxy" \
        -f Dockerfile .
    popd

    log "INFO" "Starting build for specified ${example_name} services..."
    docker compose -f build.yaml build ${service_list} --no-cache
    cd - > /dev/null
}


# --- Build Dispatcher ---
# This function selects the correct configuration and calls the generic build function.
dispatch_build() {
    local example_name=$1
    local example_path=$2
    local device_name=$3
    local config_name # This will hold the name of the config array

    section_header "Building Docker Images for ${example_name} on ${device_name}"

    export REGISTRY
    export TAG
    export http_proxy=${http_proxy:-}
    export https_proxy=${https_proxy:-}
    export no_proxy=${no_proxy:-}

    local service_list=$(get_service_list "$example_name" "$device_name")

    case "$example_name" in
        "DocSum"|"ChatQnA"|"CodeTrans"|"FaqGen"|"VisualQnA")
            config_name="VLLM_8_3_CONFIG"
            ;;
        "CodeGen"|"AudioQnA")
            config_name="VLLM_9_0_1_CONFIG"
            ;;
        "AgentQnA")
            config_name="AGENT_CONFIG"
            ;;
        *)
            error_exit "No build configuration defined for example '${example_name}'. Please add it to the script."
            ;;
    esac

    execute_build "$example_name" "$example_path" "$service_list" "$config_name"

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

# Resolves the filesystem path for a specified GenAI example
#
# Args:
#   $1 (string): The example name (e.g. "ChatQnA")
#
# Returns:
#   The absolute path to the example directory
#
# Errors:
#   Exits with error if the directory doesn't exist
get_example_path() {
    local example_name=$1
    local example_path="n/a"

    case "$example_name" in
        "FaqGen")
            # FaqGen was merged to ChatQnA since OPEA v1.3.
            # It reuses ChatQnA's code structure.
            example_path="${PROJECT_ROOT}/ChatQnA"
            ;;
        *)
            # Standard case - example name matches directory name
            example_path="${PROJECT_ROOT}/${example_name}"
            ;;
    esac

    if [ ! -d "${example_path}" ]; then
        error_exit "Example directory not found for ${example_name}: '$example_path'."
    fi

    echo "${example_path}"
}

# --- Main Script Logic ---

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
EXAMPLE_PATH=$(get_example_path "$EXAMPLE")

log "INFO" "Project Root: ${PROJECT_ROOT}"
log "INFO" "Selected Example: ${EXAMPLE} (Path: ${EXAMPLE_PATH})"
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
