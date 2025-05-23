#!/bin/bash
# Copyright (C) 2024 Intel Corporation
# SPDX-License-Identifier: Apache-2.0

SCRIPT_DIR_SETVALUES=$(cd "$(dirname "${BASH_SOURCE[0]}")" &>/dev/null && pwd)
source "${SCRIPT_DIR_SETVALUES}/utils.sh" # Assuming utils.sh is in the same directory
# LOG_FILE="set_values.log" # Optional: specific log file

CHATQNA_DIR=$(realpath "$SCRIPT_DIR_SETVALUES/../")

# Default values
DEVICE="xeon" # Mandatory, e.g., xeon, gaudi
DEPLOY_MODE="docker" # Default deployment mode
REGISTRY="" # Renamed from REPOSITORY for consistency with other scripts' params
TAG="latest"
EMBED_MODEL="" # User input for embedding model
RERANK_MODEL_ID="" # User input for rerank model
LLM_MODEL_ID="" # User input for LLM model
HUGGINGFACEHUB_API_TOKEN=""
HTTP_PROXY=""
HTTPS_PROXY=""
# Updated NO_PROXY_BASE to include static entries from the new set_env.sh
# The dynamic $JAEGER_IP part from new set_env.sh will be appended by that script itself
NO_PROXY_BASE="cluster.local,localhost,127.0.0.1,chatqna-xeon-ui-server,chatqna-xeon-backend-server,dataprep-redis-service,tei-embedding-service,retriever,tei-reranking-service,tgi-service,vllm-service,jaeger,prometheus,grafana,node-exporter"
NO_PROXY="$NO_PROXY_BASE"
MOUNT_DIR=""

# Function to display usage information
usage() {
    echo "Usage: $0 -d <DEVICE> [OPTIONS]"
    echo "  -d <DEVICE>                   (Required) Target device/platform (e.g., xeon, gaudi)."
    echo "  -m <DEPLOY_MODE>              Deployment Mode (e.g., k8s, docker, default: docker)."
    echo "  -r <REGISTRY>                 Container registry/prefix (e.g., myregistry.com/myorg)."
    echo "  -t <TAG>                      Image tag (default: latest)."
    echo "  -u <MOUNT_DIR>                Data mount directory for Docker volumes (default: ./data)."
    echo "  -e <EMBED_MODEL>              Embedding model ID (e.g., BAAI/bge-base-en-v1.5)."
    echo "  -a <RERANK_MODEL_ID>          Reranking model ID (e.g., BAAI/bge-reranker-base)."
    echo "  -l <LLM_MODEL_ID>             LLM model ID (e.g., meta-llama/Meta-Llama-3-8B-Instruct)."
    echo "  -g <HUGGINGFACEHUB_API_TOKEN> HuggingFaceHub API token."
    echo "  -p <HTTP_PROXY>               HTTP proxy URL."
    echo "  -s <HTTPS_PROXY>              HTTPS proxy URL."
    echo "  -n <NO_PROXY_VALUES>          Comma-separated values to add to NO_PROXY (in addition to defaults)."
    echo "  -h                            Display this help message."
    exit 1
}

if [ $# -eq 0 ]; then
    log ERROR "No parameters passed. Use -h for help."
    usage # usage already exits
fi

# Parse command-line arguments
while getopts "d:m:r:t:e:a:l:g:p:s:n:u:h" opt; do
    case $opt in
        d) DEVICE="$OPTARG" ;;
        m) DEPLOY_MODE="$OPTARG" ;;
        r) REGISTRY="$OPTARG" ;;
        t) TAG="$OPTARG" ;;
        e) EMBED_MODEL="$OPTARG" ;;
        a) RERANK_MODEL_ID="$OPTARG" ;;
        l) LLM_MODEL_ID="$OPTARG" ;;
        g) HUGGINGFACEHUB_API_TOKEN="$OPTARG" ;;
        p) HTTP_PROXY="$OPTARG" ;;
        s) HTTPS_PROXY="$OPTARG" ;;
        n) NO_PROXY_EXTRA="$OPTARG" ;;
        u) MOUNT_DIR="$OPTARG" ;;
        h) usage ;;
        *) usage ;;
    esac
done

# Validate required DEVICE parameter
if [ -z "$DEVICE" ]; then
    log ERROR "-d <DEVICE> is a required parameter."
    usage
fi
if [[ "$DEVICE" != "xeon" && "$DEVICE" != "gaudi" ]]; then
    log ERROR "DEVICE must be either 'xeon' or 'gaudi'. Received: '$DEVICE'"
    usage
fi
if [[ "$DEPLOY_MODE" != "k8s" && "$DEPLOY_MODE" != "docker" ]]; then
    log ERROR "DEPLOY_MODE must be either 'k8s' or 'docker'. Received: '$DEPLOY_MODE'"
    usage
fi

# Append extra NO_PROXY values if provided
if [ -n "$NO_PROXY_EXTRA" ]; then
    NO_PROXY="$NO_PROXY_BASE,$NO_PROXY_EXTRA"
fi

section_header "Applying Configuration Values"
log INFO "Effective configuration values:"
log INFO "  DEVICE: $DEVICE"
log INFO "  DEPLOY_MODE: $DEPLOY_MODE"
log INFO "  REGISTRY: ${REGISTRY:-Not set, defaults will apply in target files}"
log INFO "  TAG: $TAG"
log INFO "  MOUNT_DIR: ${MOUNT_DIR:-Not set, default to ./data}"
log INFO "  EMBED_MODEL (target EMBEDDING_MODEL_ID): ${EMBED_MODEL:-Not set, service default will apply}"
log INFO "  RERANK_MODEL_ID: ${RERANK_MODEL_ID:-Not set, service default will apply}"
log INFO "  LLM_MODEL_ID: ${LLM_MODEL_ID:-Not set, service default will apply}"
log INFO "  HUGGINGFACEHUB_API_TOKEN: ${HUGGINGFACEHUB_API_TOKEN:+(set, not shown for security)}"
log INFO "  HTTP_PROXY: ${HTTP_PROXY:-Not set}"
log INFO "  HTTPS_PROXY: ${HTTPS_PROXY:-Not set}"
log INFO "  NO_PROXY: $NO_PROXY"

update_yaml_image() {
    local file_path="$1"
    local image_base_name="$2" 
    local new_registry="$3"
    local new_tag="$4"
    local new_image_prefix=""
    if [ -n "$new_registry" ]; then
        new_image_prefix="${new_registry}/"
    fi
    log WARN "YAML image update logic is complex and highly dependent on current YAML structure and REGISTRY definition. Review carefully."
}


function update_k8s_config() {
    local k8s_manifests_base_path="${CHATQNA_DIR}/deployment/kubernetes"
    local device_manifest_dir="${k8s_manifests_base_path}/${DEVICE}"
    local configmap_file
    configmap_file=$(find "$device_manifest_dir" -name "*config*.yaml" -type f -print -quit)

    if [ ! -f "$configmap_file" ]; then
        log WARN "K8s ConfigMap file not found in '$device_manifest_dir' (searched for *config*.yaml). Skipping K8s model/token config updates."
    else
        log INFO "Updating K8s ConfigMap: $configmap_file"
        local use_yq=false
        if command_exists yq; then use_yq=true; fi

        if [ -n "$EMBED_MODEL" ]; then # User param -e <EMBED_MODEL>
          log INFO "  Updating EMBEDDING_MODEL_ID to: $EMBED_MODEL" # K8s ConfigMap key
          if $use_yq; then yq e ".data.EMBEDDING_MODEL_ID = \"$EMBED_MODEL\"" -i "$configmap_file"; else \
          sed -i "s|^\([[:space:]]*EMBEDDING_MODEL_ID:\).*|\1 \"$EMBED_MODEL\"|" "$configmap_file"; fi
        fi
        if [ -n "$RERANK_MODEL_ID" ]; then # User param -a <RERANK_MODEL_ID>
          log INFO "  Updating RERANK_MODEL_ID to: $RERANK_MODEL_ID" # K8s ConfigMap key
          if $use_yq; then yq e ".data.RERANK_MODEL_ID = \"$RERANK_MODEL_ID\"" -i "$configmap_file"; else \
          sed -i "s|^\([[:space:]]*RERANK_MODEL_ID:\).*|\1 \"$RERANK_MODEL_ID\"|" "$configmap_file"; fi
        fi
        if [ -n "$LLM_MODEL_ID" ]; then # User param -l <LLM_MODEL_ID>
          log INFO "  Updating LLM_MODEL_ID to: $LLM_MODEL_ID" # K8s ConfigMap key
          if $use_yq; then yq e ".data.LLM_MODEL_ID = \"$LLM_MODEL_ID\"" -i "$configmap_file"; else \
          sed -i "s|^\([[:space:]]*LLM_MODEL_ID:\).*|\1 \"$LLM_MODEL_ID\"|" "$configmap_file"; fi
        fi
        if [ -n "$HUGGINGFACEHUB_API_TOKEN" ]; then
          log INFO "  Updating HUGGINGFACEHUB_API_TOKEN and HF_TOKEN..."
          if $use_yq; then
            yq e ".data.HUGGINGFACEHUB_API_TOKEN = \"$HUGGINGFACEHUB_API_TOKEN\"" -i "$configmap_file"
            yq e ".data.HF_TOKEN = \"$HUGGINGFACEHUB_API_TOKEN\"" -i "$configmap_file"
          else
            sed -i "s|^\([[:space:]]*HUGGINGFACEHUB_API_TOKEN:\).*|\1 \"$HUGGINGFACEHUB_API_TOKEN\"|" "$configmap_file"
            sed -i "s|^\([[:space:]]*HF_TOKEN:\).*|\1 \"$HUGGINGFACEHUB_API_TOKEN\"|" "$configmap_file"
          fi
        fi
        if [ -n "$HTTP_PROXY" ]; then
            log INFO "  Updating HTTP_PROXY..."
            if $use_yq; then yq e ".data.HTTP_PROXY = \"$HTTP_PROXY\"" -i "$configmap_file"; else \
            sed -i "s|^\([[:space:]]*HTTP_PROXY:\).*|\1 \"$HTTP_PROXY\"|" "$configmap_file"; fi
        fi
        if [ -n "$HTTPS_PROXY" ]; then
            log INFO "  Updating HTTPS_PROXY..."
            if $use_yq; then yq e ".data.HTTPS_PROXY = \"$HTTPS_PROXY\"" -i "$configmap_file"; else \
            sed -i "s|^\([[:space:]]*HTTPS_PROXY:\).*|\1 \"$HTTPS_PROXY\"|" "$configmap_file"; fi
        fi
        if [ -n "$NO_PROXY" ]; then
            log INFO "  Updating NO_PROXY..."
            if $use_yq; then yq e ".data.NO_PROXY = \"$NO_PROXY\"" -i "$configmap_file"; else \
            sed -i "s|^\([[:space:]]*NO_PROXY:\).*|\1 \"$NO_PROXY\"|" "$configmap_file"; fi
        fi
    fi

    if [ -d "$device_manifest_dir" ]; then
        if [ -n "$REGISTRY" ] || [ -n "$TAG" ]; then
            log INFO "Updating images in K8s manifests under $device_manifest_dir:"
            [ -n "$REGISTRY" ] && log INFO "  Setting registry part to: $REGISTRY"
            [ -n "$TAG" ] && log INFO "  Setting tag to: $TAG"
            find "$device_manifest_dir" -name '*.yaml' -type f -print0 | while IFS= read -r -d $'\0' file; do
                log INFO "  Processing $file for image updates..."
                if [ -n "$REGISTRY" ]; then
                    sed -i -E "s|image: *([A-Za-z0-9.-]+/)*opea/aisolution/([^:]+):(.*)|image: ${REGISTRY}/\2:\3|g" "$file"
                fi
                if [ -n "$TAG" ]; then
                    sed -i -E "s|(image: *[^:]+:)[^:]+$|\1${TAG}|g" "$file"
                fi
            done
        fi
    else
        log WARN "K8s manifest directory for device '$DEVICE' ($device_manifest_dir) not found. Skipping image updates in K8s YAMLs."
    fi
}

function update_docker_config() {
    log INFO "Preparing Docker environment variables for device: $DEVICE"
    if [ "$DEVICE" = "gaudi" ]; then
        local target_compose_dir="${CHATQNA_DIR}/docker_compose/intel/hpu/${DEVICE}"
    elif [ "$DEVICE" = "xeon" ]; then
        local target_compose_dir="${CHATQNA_DIR}/docker_compose/intel/cpu/${DEVICE}"
    fi
    local set_env_script_path="${target_compose_dir}/set_env.sh"

    if [ ! -f "$set_env_script_path" ]; then
        log WARN "Docker set_env.sh script not found at '$set_env_script_path'. Skipping Docker config updates."
        return
    fi
    log INFO "Updating Docker environment script: $set_env_script_path"

    update_line_in_file() {
        local file="$1"
        local key="$2"
        local value="$3"
        # Ensure value is quoted for sed replacement, especially if it contains special characters like / or ,
        # For export lines, the value itself might need internal quotes if it contains spaces, handled by caller.
        local escaped_value=$(sed 's/[&/\]/\\&/g' <<< "$value")
        if grep -q "export ${key}=" "$file"; then
            sed -i "s|^export ${key}=.*|export ${key}=${escaped_value}|" "$file"
        else
            echo "export ${key}=${value}" >> "$file" # Value here should be as it's meant to be in the script
        fi
    }

    if [ -n "$REGISTRY" ]; then update_line_in_file "$set_env_script_path" "REGISTRY" "$REGISTRY"; fi
    if [ -n "$TAG" ]; then update_line_in_file "$set_env_script_path" "IMAGE_TAG" "$TAG"; fi # Assuming new set_env or compose uses IMAGE_TAG

    if [ -n "$HTTP_PROXY" ]; then update_line_in_file "$set_env_script_path" "HTTP_PROXY" "\"$HTTP_PROXY\""; fi
    if [ -n "$HTTPS_PROXY" ]; then update_line_in_file "$set_env_script_path" "HTTPS_PROXY" "\"$HTTPS_PROXY\""; fi
    # NO_PROXY is updated. The target set_env.sh appends dynamic parts like $JAEGER_IP to this.
    if [ -n "$NO_PROXY" ]; then update_line_in_file "$set_env_script_path" "no_proxy" "\"$NO_PROXY\""; fi # Target script uses lowercase 'no_proxy'
    if [ -n "$MOUNT_DIR" ]; then update_line_in_file "$set_env_script_path" "MOUNT_DIR" "$MOUNT_DIR"; fi # If set_env.sh uses it

    # Update model IDs based on new variable names in the target set_env.sh
    # User param -e EMBED_MODEL is for EMBEDDING_MODEL_ID
    if [ -n "$EMBED_MODEL" ]; then update_line_in_file "$set_env_script_path" "EMBEDDING_MODEL_ID" "\"$EMBED_MODEL\""; fi
    # User param -a RERANK_MODEL_ID is for RERANK_MODEL_ID
    if [ -n "$RERANK_MODEL_ID" ]; then update_line_in_file "$set_env_script_path" "RERANK_MODEL_ID" "\"$RERANK_MODEL_ID\""; fi
    # User param -l LLM_MODEL_ID is for LLM_MODEL_ID
    if [ -n "$LLM_MODEL_ID" ]; then update_line_in_file "$set_env_script_path" "LLM_MODEL_ID" "\"$LLM_MODEL_ID\""; fi

    # Update HUGGINGFACEHUB_API_TOKEN and HF_TOKEN
    if [ -n "$HUGGINGFACEHUB_API_TOKEN" ]; then
        update_line_in_file "$set_env_script_path" "HUGGINGFACEHUB_API_TOKEN" "\"$HUGGINGFACEHUB_API_TOKEN\""
        update_line_in_file "$set_env_script_path" "HF_TOKEN" "\"$HUGGINGFACEHUB_API_TOKEN\"" # New set_env.sh also uses HF_TOKEN
    fi
    # Variables like LOGFLAG, INDEX_NAME etc. from new set_env.sh could be added here if parameterization is needed

    log INFO "Docker configurations prepared/updated in $set_env_script_path."
}


# Main logic based on DEPLOY_MODE
if [ "$DEPLOY_MODE" = "k8s" ]; then
    update_k8s_config
elif [ "$DEPLOY_MODE" = "docker" ]; then
    update_docker_config
else
    log ERROR "Unsupported DEPLOY_MODE '$DEPLOY_MODE'. This check should have been caught earlier."
    exit 1
fi

log OK "Configuration update process completed for DEVICE '$DEVICE' in DEPLOY_MODE '$DEPLOY_MODE'."