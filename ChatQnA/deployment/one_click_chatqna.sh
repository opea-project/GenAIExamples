#!/bin/bash
# Copyright (C) 2024 Intel Corporation
# SPDX-License-Identifier: Apache-2.0

# set -e # Removed set -e to allow user to decide to skip parts, script will handle errors
# set -o pipefail # Removed for same reason

# Script's own directory
SCRIPT_DIR_ONECLICK=$(cd "$(dirname "${BASH_SOURCE[0]}")" &>/dev/null && pwd)
source "${SCRIPT_DIR_ONECLICK}/utils.sh" # Assuming utils.sh is in the same directory
# LOG_FILE="one_click_chatqna.log" # Optional: specific log file
default_host_ip=$(hostname -I | awk '{print $1}' 2>/dev/null)

# --- Default values ---
DEFAULT_DEVICE="xeon"
DEFAULT_TAG="latest"
REGISTRY=""
DEFAULT_REGISTRY=""
DEFAULT_DEPLOY_MODE="docker"
DEFAULT_CHECK_ENV_MODE="online" # For check_env.sh

# --- Pre-requisite checks ---
if ! command_exists docker; then
    log ERROR "Docker is not installed. Please install Docker first."
    exit 1
fi
# Kubectl check only if k8s mode is chosen later
# Git check if update_images needs it for cloning (it does)

# --- Interactive Parameter Input ---
section_header "ChatQnA One-Click Interactive Setup"
log INFO "This script will guide you through deploying ChatQnA."
log INFO "Press Enter to use default values shown in [brackets]."

DEFAULT_HUG_TOKEN=$(get_huggingface_token)

if [ -n "$DEFAULT_HUG_TOKEN" ]; then
    read -p "Found default Hugging Face Token. Use it? [Y/n]: " use_default
    case "$use_default" in
        [nN]|[nN][oO])
            HUG_TOKEN=""
            ;;
        *)
            HUG_TOKEN="$DEFAULT_HUG_TOKEN"
            ;;
    esac
fi

while [ -z "$HUG_TOKEN" ]; do
    read -p "Enter Hugging Face Token (mandatory for model downloads): " HUG_TOKEN
    if [ -z "$HUG_TOKEN" ]; then
        log WARN "Hugging Face Token cannot be empty if models need to be downloaded."
    fi
done

log INFO "Using Hugging Face Token: ${HUG_TOKEN:0:4}...${HUG_TOKEN: -4}"
if [ ! -f $HOME/.cache/huggingface/token ]; then
    log INFO 'Save Hugging Face Token into $HF_HOME/token'
    echo $HUG_TOKEN > $HOME/.cache/huggingface/token
fi

# Core Deployment Parameters
log INFO "--- Core Deployment Settings ---"
read -p "Enter DEVICE type (e.g., xeon, gaudi) [default: $DEFAULT_DEVICE]: " input_device
DEVICE="${input_device:-$DEFAULT_DEVICE}"
while [[ "$DEVICE" != "xeon" && "$DEVICE" != "gaudi" ]]; do
    log WARN "Invalid DEVICE. Must be 'xeon' or 'gaudi'."
    read -p "Enter DEVICE type (e.g., xeon, gaudi) [default: $DEFAULT_DEVICE]: " input_device
    DEVICE="${input_device:-$DEFAULT_DEVICE}"
done


read -p "Enter Image TAG [default: $DEFAULT_TAG]: " input_tag
TAG="${input_tag:-$DEFAULT_TAG}"

read -p "Enter Container REGISTRY (e.g., myregistry.com/myorg, leave blank for Docker Hub or local build defaults) [default: $DEFAULT_REGISTRY]: " input_registry
REGISTRY="${input_registry:-$DEFAULT_REGISTRY}"

read -p "Enter DEPLOY_MODE (docker/k8s) [default: $DEFAULT_DEPLOY_MODE]: " input_deploy_mode
DEPLOY_MODE="${input_deploy_mode:-$DEFAULT_DEPLOY_MODE}"
while [[ "$DEPLOY_MODE" != "docker" && "$DEPLOY_MODE" != "k8s" ]]; do
    log WARN "Invalid DEPLOY_MODE. Must be 'docker' or 'k8s'."
    read -p "Enter DEPLOY_MODE (docker/k8s) [default: $DEFAULT_DEPLOY_MODE]: " input_deploy_mode
    DEPLOY_MODE="${input_deploy_mode:-$DEFAULT_DEPLOY_MODE}"
done
echo

# Proxy Parameters (Optional)
log INFO "--- Proxy Settings (optional, press Enter to skip or use system defaults) ---"
SYSTEM_HTTP_PROXY="${http_proxy:-${HTTP_PROXY:-}}"
SYSTEM_HTTPS_PROXY="${https_proxy:-${HTTPS_PROXY:-}}"
SYSTEM_NO_PROXY="${no_proxy:-${NO_PROXY:-}},$default_host_ip"

prompt_http_proxy="Enter HTTP_PROXY"
[[ -n "$SYSTEM_HTTP_PROXY" ]] && prompt_http_proxy+=" [current/system: $SYSTEM_HTTP_PROXY]"
read -p "$prompt_http_proxy: " input_http_proxy
FINAL_HTTP_PROXY="${input_http_proxy:-$SYSTEM_HTTP_PROXY}"

prompt_https_proxy="Enter HTTPS_PROXY"
[[ -n "$SYSTEM_HTTPS_PROXY" ]] && prompt_https_proxy+=" [current/system: $SYSTEM_HTTPS_PROXY]"
read -p "$prompt_https_proxy: " input_https_proxy
FINAL_HTTPS_PROXY="${input_https_proxy:-$SYSTEM_HTTPS_PROXY}"

prompt_no_proxy="Enter NO_PROXY (comma-separated)"
[[ -n "$SYSTEM_NO_PROXY" ]] && prompt_no_proxy+=" [current/system: $SYSTEM_NO_PROXY]"
read -p "$prompt_no_proxy: " input_no_proxy
FINAL_NO_PROXY="${input_no_proxy:-$SYSTEM_NO_PROXY}"
echo

# Model Configuration Parameters (Optional)
log INFO "--- Model Configuration (optional, press Enter to use defaults from sub-scripts) ---"
read -p "Enter Embedding Model ID (e.g., BAAI/bge-base-en-v1.5): " EMBED_MODEL
read -p "Enter Reranking Model ID (e.g., BAAI/bge-reranker-base): " RERANK_MODEL_ID
read -p "Enter LLM Model ID (e.g., meta-llama/Meta-Llama-3-8B-Instruct): " LLM_MODEL_ID
read -p "Enter Data Mount Directory [default: ./data]: " MOUNT_DIR
echo

section_header "Configuration Summary"
log INFO "  Hugging Face Token: [REDACTED FOR SECURITY]"
log INFO "  Device:             $DEVICE"
log INFO "  Image Tag:          $TAG"
log INFO "  Registry:           ${REGISTRY:-Not set / Use sub-script default}"
log INFO "  Deploy Mode:        $DEPLOY_MODE"
log INFO "  HTTP Proxy:         ${FINAL_HTTP_PROXY:-Not set}"
log INFO "  HTTPS Proxy:        ${FINAL_HTTPS_PROXY:-Not set}"
log INFO "  No Proxy:           ${FINAL_NO_PROXY:-Not set}"
log INFO "  Embedding Model:    ${EMBED_MODEL:-Not set / Use sub-script default}"
log INFO "  Reranking Model ID: ${RERANK_MODEL_ID:-Not set / Use sub-script default}"
log INFO "  LLM Model ID:       ${LLM_MODEL_ID:-Not set / Use sub-script default}"
log INFO "  Mount Directory:     ${MOUNT_DIR:-./data}"
echo

read -p "Proceed with these settings? (Y/n): " confirm_settings
confirm_settings_lower=$(echo "${confirm_settings:-Y}" | tr '[:upper:]' '[:lower:]')
if [[ "$confirm_settings_lower" != "y" && "$confirm_settings_lower" != "yes" ]]; then
    log INFO "Aborted by user."
    exit 1
fi
echo

# --- Execution Steps ---

# 1. Check environment
section_header "Step 1: Checking Environment (check_env.sh)"
read -p "Run environment check? (Y/n) [Default: Y]: " run_check_env
run_check_env_lower=$(echo "$run_check_env" | tr '[:upper:]' '[:lower:]')
if [[ "$run_check_env_lower" == "y" || "$run_check_env_lower" == "yes" || -z "$run_check_env" ]]; then
    if [ -f "${SCRIPT_DIR_ONECLICK}/check_env.sh" ]; then
        log INFO "Running check_env.sh --device $DEVICE --mode $DEFAULT_CHECK_ENV_MODE ..."
        if ! bash "${SCRIPT_DIR_ONECLICK}/check_env.sh" --device "$DEVICE" --mode "$DEFAULT_CHECK_ENV_MODE"; then
            log ERROR "Environment check failed. Please resolve issues or skip this step if you are sure."
            read -p "Continue despite environment check failure? (y/N): " continue_anyway
            if [[ "$(echo "$continue_anyway" | tr '[:upper:]' '[:lower:]')" != "y" ]]; then
                exit 1
            fi
        else
            log OK "Environment check passed."
        fi
    else
        log WARN "check_env.sh not found. Skipping environment check."
    fi
else
    log INFO "Skipping environment check as per user choice."
fi
echo

# 2. Build/Push Images (update_images.sh)
section_header "Step 2: Building and Pushing Images (update_images.sh)"
read -p "Build images with update_images.sh? (y/N) [Default: N]: " run_update_images
run_update_images_lower=$(echo "$run_update_images" | tr '[:upper:]' '[:lower:]')

if [[ "$run_update_images_lower" == "y" || "$run_update_images_lower" == "yes" ]]; then
    if [ ! -f "${SCRIPT_DIR_ONECLICK}/update_images.sh" ]; then
        log ERROR "update_images.sh not found."
        exit 1
    fi

    update_images_args=("--tag" "$TAG" "--build") # 默认包含 build

    # 询问是否需要 push
    read -p "Push images to registry? (y/N) [Default: N]: " push_images
    push_images_lower=$(echo "$push_images" | tr '[:upper:]' '[:lower:]')
    if [[ "$push_images_lower" == "y" || "$push_images_lower" == "yes" ]]; then
        update_images_args+=("--push")
        # 检查 registry 是否设置
        if [ -z "$REGISTRY" ]; then
            read -p "Setup local registry (localhost:5000)? (y/N) [Default: N]: " setup_local_reg
            setup_local_reg_lower=$(echo "$setup_local_reg" | tr '[:upper:]' '[:lower:]')
            if [[ "$setup_local_reg_lower" == "y" ]]; then
                update_images_args+=("--setup-registry")
                REGISTRY="localhost:5000"
            else
                log ERROR "Push requires registry. Use --registry to specify or --setup-registry for local."
                exit 1
            fi
        fi
    fi

    # 处理 registry 参数
    if [ -n "$REGISTRY" ]; then
        update_images_args+=("--registry" "$REGISTRY")
        log INFO "Please ensure you are logged in to registry: $REGISTRY"
    fi

    # 代理设置
    export http_proxy="${FINAL_HTTP_PROXY}"
    export https_proxy="${FINAL_HTTPS_PROXY}"
    export no_proxy="${FINAL_NO_PROXY}"

    log INFO "Running update_images.sh ${update_images_args[*]} ..."
    if ! bash "${SCRIPT_DIR_ONECLICK}/update_images.sh" "${update_images_args[@]}"; then
        log ERROR "Image build/push failed."
        unset http_proxy https_proxy no_proxy
        exit 1
    fi
    unset http_proxy https_proxy no_proxy
else
    log INFO "Skipping image update."
fi
echo


# 3. Set Helm/Manifest Values (set_values.sh)
# This step is important for both K8s and Docker (to prepare compose env files)
section_header "Step 3: Configuring Service Parameters (set_values.sh)"
if [ ! -f "${SCRIPT_DIR_ONECLICK}/set_values.sh" ]; then
    log ERROR "set_values.sh not found. Cannot configure deployment parameters."
    # Decide if this is fatal or skippable
    read -p "Continue without running set_values.sh? (y/N): " skip_set_values
    if [[ "$(echo "$skip_set_values" | tr '[:upper:]' '[:lower:]')" != "y" ]]; then
        exit 1
    fi
else
    set_values_args=()
    set_values_args+=("-d" "$DEVICE")
    set_values_args+=("-m" "$DEPLOY_MODE")
    set_values_args+=("-g" "$HUG_TOKEN")
    set_values_args+=("-t" "$TAG")

    if [ -n "$REGISTRY" ]; then set_values_args+=("-r" "$REGISTRY"); fi
    if [ -n "$FINAL_HTTP_PROXY" ]; then set_values_args+=("-p" "$FINAL_HTTP_PROXY"); fi
    if [ -n "$FINAL_HTTPS_PROXY" ]; then set_values_args+=("-s" "$FINAL_HTTPS_PROXY"); fi # -s for set_values.sh
    if [ -n "$FINAL_NO_PROXY" ]; then set_values_args+=("-n" "$FINAL_NO_PROXY"); fi # -n for set_values.sh additions
    if [ -n "$EMBED_MODEL" ]; then set_values_args+=("-e" "$EMBED_MODEL"); fi
    if [ -n "$RERANK_MODEL_ID" ]; then set_values_args+=("-a" "$RERANK_MODEL_ID"); fi # -a for set_values.sh
    if [ -n "$LLM_MODEL_ID" ]; then set_values_args+=("-l" "$LLM_MODEL_ID"); fi
    if [ -n "$MOUNT_DIR" ]; then set_values_args+=("-u" "$MOUNT_DIR"); fi


    log INFO "Running set_values.sh ${set_values_args[*]} ..."
    if ! bash "${SCRIPT_DIR_ONECLICK}/set_values.sh" "${set_values_args[@]}"; then
        log ERROR "set_values.sh failed. Parameter configuration aborted."
        exit 1 # This is usually critical
    else
        log OK "Parameter configuration (set_values.sh) finished successfully."
    fi
fi
echo

# 4. Install ChatQnA (install_chatqna.sh)
section_header "Step 4: Installing ChatQnA (install_chatqna.sh)"
if [ "$DEPLOY_MODE" == "k8s" ]; then
    if ! command_exists kubectl; then
        log ERROR "kubectl is not installed, but DEPLOY_MODE is k8s. Please install kubectl."
        exit 1
    fi
fi

if [ ! -f "${SCRIPT_DIR_ONECLICK}/install_chatqna.sh" ]; then
    log ERROR "install_chatqna.sh not found. Cannot proceed with deployment."
    exit 1
fi

install_args=()
install_args+=("--device" "$DEVICE")
install_args+=("--deploy-mode" "$DEPLOY_MODE")
install_args+=("--hf-token" "$HUG_TOKEN")
install_args+=("--tag" "$TAG")
install_args+=("--deploy") # Explicitly tell install_chatqna.sh to deploy

if [ -n "$REGISTRY" ]; then install_args+=("--registry" "$REGISTRY"); fi
if [ -n "$FINAL_HTTP_PROXY" ]; then install_args+=("--http-proxy" "$FINAL_HTTP_PROXY"); fi
if [ -n "$FINAL_HTTPS_PROXY" ]; then install_args+=("--https-proxy" "$FINAL_HTTPS_PROXY"); fi
if [ -n "$FINAL_NO_PROXY" ]; then install_args+=("--no-proxy" "$FINAL_NO_PROXY"); fi
if [ -n "$EMBED_MODEL" ]; then install_args+=("--embed-model" "$EMBED_MODEL"); fi
if [ -n "$RERANK_MODEL_ID" ]; then install_args+=("--rerank-model" "$RERANK_MODEL_ID"); fi
if [ -n "$LLM_MODEL_ID" ]; then install_args+=("--llm-model" "$LLM_MODEL_ID"); fi
if [ -n "$MOUNT_DIR" ]; then install_args+=("--mount-dir" "$MOUNT_DIR"); fi

log INFO "Running install_chatqna.sh ${install_args[*]} ..."
# The install_chatqna.sh script will also run a test at the end of its deploy action.
if ! bash "${SCRIPT_DIR_ONECLICK}/install_chatqna.sh" "${install_args[@]}"; then
    log ERROR "install_chatqna.sh failed. Deployment process aborted."
    exit 1
else
    log OK "ChatQnA installation and initial test (from install_chatqna.sh) process finished successfully."
fi
echo

section_header "One-Click Setup Completed"
log OK "All selected steps executed. Please check logs for details."
if [ "$DEPLOY_MODE" == "docker" ]; then
    log INFO "For Docker deployment, you can check running containers using: docker ps"
    log INFO "To view logs for a service: docker logs <container_name_or_id>"
    log INFO "To stop services: Navigate to deployment/docker_compose/$DEVICE/ and run: docker compose down"
elif [ "$DEPLOY_MODE" == "k8s" ]; then
    log INFO "For Kubernetes deployment, check pods status: kubectl get pods -n chatqna" # Assuming 'chatqna' namespace
    log INFO "To view logs for a pod: kubectl logs <pod_name> -n chatqna"
    log INFO "To delete the deployment: ./install_chatqna.sh --device $DEVICE --deploy-mode k8s --clear-deployment"
fi
local_ip_for_ui=$(hostname -I | awk '{print $1}' || echo "localhost")
log INFO "ChatQnA UI is accessible at: ${COLOR_OK}http://${local_ip_for_ui}${COLOR_RESET}"
