#!/bin/bash
# Copyright (C) 2024 Intel Corporation
# SPDX-License-Identifier: Apache-2.0

SCRIPT_DIR_SETVALUES=$(cd "$(dirname "${BASH_SOURCE[0]}")" &>/dev/null && pwd)
source "${SCRIPT_DIR_SETVALUES}/utils.sh" # Assuming utils.sh is in the same directory
# LOG_FILE="set_values.log" # Optional: specific log file

REPO_DIR=$(realpath "$SCRIPT_DIR_SETVALUES/../")

# Default values
DEVICE="xeon" # Mandatory, e.g., xeon, gaudi
DEPLOY_MODE="docker" # Default deployment mode
REGISTRY="" # Renamed from REPOSITORY for consistency with other scripts' params
TAG="latest"
EMBED_MODEL=""
RERANK_MODEL_ID=""
LLM_MODEL_ID=""
HUGGINGFACEHUB_API_TOKEN=""
HTTP_PROXY=""
HTTPS_PROXY=""
NO_PROXY_BASE="cluster.local,localhost,127.0.0.1,chatqna-xeon-ui-server,chatqna-xeon-backend-server,dataprep-service,mosec-embedding-service,embedding,retriever,reranking,mosec-reranking-service,vllm-service" # Added localhost, 127.0.0.1
NO_PROXY="$NO_PROXY_BASE"
MOUNT_DIR=""
# Removed ip_address from here, will be determined in update_docker_config if needed or use localhost/service_name

# Function to display usage information
usage() {
    echo "Usage: $0 -d <DEVICE> [OPTIONS]"
    echo "  -d <DEVICE>                   (Required) Target device/platform (e.g., xeon, gaudi)."
    echo "  -m <DEPLOY_MODE>              Deployment Mode (e.g., k8s, docker, default: docker)."
    echo "  -r <REGISTRY>                 Container registry/prefix (e.g., myregistry.com/myorg)."
    echo "  -t <TAG>                      Image tag (default: latest)."
    echo "  -u <MOUNT_DIR>                Data mount directory for Docker volumes (default: ./data)."
    echo "  -e <EMBED_MODEL>              Embedding model name/path."
    echo "  -a <RERANK_MODEL_ID>          Reranking model ID."
    echo "  -l <LLM_MODEL_ID>             LLM model ID."
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
        r) REGISTRY="$OPTARG" ;; # Changed from REPOSITORY
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
log INFO "  EMBED_MODEL: ${EMBED_MODEL:-Not set, service default will apply}"
log INFO "  RERANK_MODEL_ID: ${RERANK_MODEL_ID:-Not set, service default will apply}"
log INFO "  LLM_MODEL_ID: ${LLM_MODEL_ID:-Not set, service default will apply}"
log INFO "  HUGGINGFACEHUB_API_TOKEN: ${HUGGINGFACEHUB_API_TOKEN:+(set, not shown for security)}"
log INFO "  HTTP_PROXY: ${HTTP_PROXY:-Not set}"
log INFO "  HTTPS_PROXY: ${HTTPS_PROXY:-Not set}"
log INFO "  NO_PROXY: $NO_PROXY"

update_yaml_image() {
    local file_path="$1"
    local image_base_name="$2" # e.g., "opea/aisolution/chatqna"
    local new_registry="$3"
    local new_tag="$4"

    # Construct the original image pattern carefully. Allows for an optional existing registry.
    # Example: image: opea/aisolution/chatqna:latest
    # Example: image: my.old.registry/opea/aisolution/chatqna:some-tag
    # This sed tries to replace the registry and tag for a known image base name.

    local new_image_prefix=""
    if [ -n "$new_registry" ]; then
        new_image_prefix="${new_registry}/"
    fi

    # sed -i "s|image: \(.*\/\)*${image_base_name}:.*|image: ${new_image_prefix}${image_base_name}:${new_tag}|g" "$file_path"
    # A simpler approach if `opea/aisolution` is a fixed part that might be *prefixed* or *replaced* by REGISTRY
    # If REGISTRY is a full prefix like "my.registry/myorg", and images are "opea/aisolution/component"
    # The new image would be "my.registry/myorg/opea/aisolution/component:new_tag"
    # Or if REGISTRY is "my.registry/myorg" and it *replaces* "opea", then "my.registry/myorg/aisolution/component:new_tag"

    # Assuming REGISTRY replaces "opea/aisolution" part or prefixes it.
    # Let's assume images are like `opea/aisolution/image-name` and `REGISTRY` is `new-registry/new-org`
    # then final image is `new-registry/new-org/image-name:TAG`
    # This is complex to do reliably with sed for all YAML structures.
    # A common pattern is that the default image is 'opea/aisolution/some-service:latest'
    # and we want to change it to '$REGISTRY/some-service:$TAG' if REGISTRY is 'myhub.com/myteam'
    # OR to '$REGISTRY/opea/aisolution/some-service:$TAG' if REGISTRY is just 'myhub.com'

    # Let's simplify: if REGISTRY is set, it replaces the part before the specific service name.
    # If original is "image: opea/aisolution/chatqna:latest"
    # If REGISTRY="my.repo", TAG="v2", then "image: my.repo/chatqna:v2" (assuming image_base_name includes "opea/aisolution")
    # This needs a clear convention on what REGISTRY means and what image_base_name is.

    # The find command below is more general but still relies on a common original prefix.
    # `find . -name '*.yaml' -type f -exec sed -i -E -e "s|image: *[^ /]+/aisolution/([^:]+):.+|image: ${REGISTRY}/\1:${TAG}|g" {} \;`
    # This is too specific.
    # The original `sed -i -e "/image: /s#opea/aisolution#${REGISTRY}#g" -e "/image: /s#latest#${TAG}#g" {} \;`
    # assumes REGISTRY replaces "opea/aisolution". This is a strong assumption.
    # A safer way for tags:
    # sed -i -E "s|(image: .*:)[^:]+$|\1${new_tag}|g" "$file_path"
    # And for registry, if REGISTRY is a full prefix for the image name (e.g., image_name is "chatqna", registry is "myorg"):
    # sed -i -E "s|image: *([^/]+)/([^:]+):|image: ${new_registry}/\2:|g" "$file_path"
    # This is very tricky. The existing find command in `update_k8s_config` is probably the most practical if assumptions hold.
    log WARN "YAML image update logic is complex and highly dependent on current YAML structure and REGISTRY definition. Review carefully."
}


function update_k8s_config() {
    local k8s_manifests_base_path="${REPO_DIR}/deployment/kubernetes"
    local device_manifest_dir="${k8s_manifests_base_path}/${DEVICE}"
    local configmap_file_pattern="${device_manifest_dir}/chatQnA_config_map.yaml" # Assuming this naming

    # Try to find a configmap, could be named differently
    local configmap_file
    configmap_file=$(find "$device_manifest_dir" -name "*config*.yaml" -type f -print -quit)


    if [ ! -f "$configmap_file" ]; then
        log WARN "K8s ConfigMap file not found in '$device_manifest_dir' (searched for *config*.yaml). Skipping K8s model/token config updates."
    else
        log INFO "Updating K8s ConfigMap: $configmap_file"
        # Use yq if available for robust YAML editing, otherwise sed
        local use_yq=false
        if command_exists yq; then use_yq=true; fi

        if [ -n "$EMBED_MODEL" ]; then
          log INFO "  Updating EMBED_MODEL to: $EMBED_MODEL"
          if $use_yq; then yq e ".data.EMBED_MODEL = \"$EMBED_MODEL\"" -i "$configmap_file"; else \
          sed -i "s|^\([[:space:]]*EMBED_MODEL:\).*|\1 \"$EMBED_MODEL\"|" "$configmap_file"; fi
        fi
        if [ -n "$RERANK_MODEL_ID" ]; then
          log INFO "  Updating RERANK_MODEL_ID to: $RERANK_MODEL_ID"
          if $use_yq; then yq e ".data.RERANK_MODEL_ID = \"$RERANK_MODEL_ID\"" -i "$configmap_file"; else \
          sed -i "s|^\([[:space:]]*RERANK_MODEL_ID:\).*|\1 \"$RERANK_MODEL_ID\"|" "$configmap_file"; fi
        fi
        if [ -n "$LLM_MODEL_ID" ]; then
          log INFO "  Updating LLM_MODEL_ID to: $LLM_MODEL_ID"
          if $use_yq; then yq e ".data.LLM_MODEL_ID = \"$LLM_MODEL_ID\"" -i "$configmap_file"; else \
          sed -i "s|^\([[:space:]]*LLM_MODEL_ID:\).*|\1 \"$LLM_MODEL_ID\"|" "$configmap_file"; fi
        fi
        if [ -n "$HUGGINGFACEHUB_API_TOKEN" ]; then
          log INFO "  Updating HUGGINGFACEHUB_API_TOKEN..."
          if $use_yq; then
            yq e ".data.HUGGINGFACEHUB_API_TOKEN = \"$HUGGINGFACEHUB_API_TOKEN\"" -i "$configmap_file"
            yq e ".data.HF_TOKEN = \"$HUGGINGFACEHUB_API_TOKEN\"" -i "$configmap_file" # If HF_TOKEN is also used
          else
            sed -i "s|^\([[:space:]]*HUGGINGFACEHUB_API_TOKEN:\).*|\1 \"$HUGGINGFACEHUB_API_TOKEN\"|" "$configmap_file"
            sed -i "s|^\([[:space:]]*HF_TOKEN:\).*|\1 \"$HUGGINGFACEHUB_API_TOKEN\"|" "$configmap_file"
          fi
        fi
        # Add proxy settings to ConfigMap if they are defined in it
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

            # This find and sed command is quite aggressive. It assumes all images under "opea/aisolution/"
            # should be replaced by "REGISTRY/" and tag updated.
            # Example: image: opea/aisolution/foo:latest -> image: my.reg/foo:newtag
            # This will break if images are not from "opea/aisolution" or if REGISTRY is not just a prefix.
            # Consider making this more targeted or using kustomize/helm for image overrides.
            find "$device_manifest_dir" -name '*.yaml' -type f -print0 | while IFS= read -r -d $'\0' file; do
                log INFO "  Processing $file for image updates..."
                if [ -n "$REGISTRY" ]; then
                    # This sed replaces 'opea/aisolution' with the new registry.
                    # It assumes 'opea/aisolution' is a common prefix for images that need changing.
                    # e.g. image: opea/aisolution/my-service:some-tag -> image: ${REGISTRY}/my-service:some-tag
                    sed -i -E "s|image: *([A-Za-z0-9.-]+/)*opea/aisolution/([^:]+):(.*)|image: ${REGISTRY}/\2:\3|g" "$file"
                fi
                if [ -n "$TAG" ]; then
                    # This sed changes the tag of any image line.
                    # e.g. image: something/another:latest -> image: something/another:${TAG}
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
    local target_compose_dir="${REPO_DIR}/deployment/docker_compose/${DEVICE}"
    local set_env_script_path="${target_compose_dir}/set_env.sh" # Original script

    # Prefer .env file if it exists, otherwise modify set_env.sh
    # For Docker, it's usually better to set these in a .env file read by docker-compose
    # or directly in the docker-compose.yaml environment sections.
    # Modifying set_env.sh directly is also an option if that's the established workflow.

    # For this review, I'll stick to exporting, assuming set_env.sh will pick them up if sourced by compose,
    # or that compose file directly uses these exported vars.
    # The original script just exported them, which means they need to be available when `docker compose` runs.
    # This script (`set_values.sh`) is typically sourced or its output is eval'd by the caller.
    # If this script is run standalone, exports won't persist for a later `docker compose` call.
    # The original `install_chatqna.sh` sources `set_env.sh` from the compose dir.
    # The original `one_click_chatqna.sh` calls this `set_values.sh` then `install_chatqna.sh`.
    # The crucial part is that `docker_compose/${DEVICE}/set_env.sh` should correctly use these.

    # Let's assume `docker_compose/${DEVICE}/set_env.sh` is the primary place to set these for Docker.
    # We will modify that script.
    if [ ! -f "$set_env_script_path" ]; then
        log WARN "Docker set_env.sh script not found at '$set_env_script_path'. Skipping Docker config updates."
        return
    fi
    log INFO "Updating Docker environment script: $set_env_script_path"

    update_line_in_file() {
        local file="$1"
        local key="$2"
        local value="$3"
        # If key exists, update it. If not, append it.
        # Ensure value is quoted if it contains spaces or special chars, though for env vars it's usually fine.
        if grep -q "export ${key}=" "$file"; then
            sed -i "s|^export ${key}=.*|export ${key}=${value}|" "$file"
        else
            echo "export ${key}=${value}" >> "$file"
        fi
    }

    # It's better if set_env.sh sources another file that we can cleanly overwrite,
    # or if set_env.sh is designed to use defaults if overrides aren't present.
    # For now, directly editing set_env.sh based on parameters.
    if [ -n "$REGISTRY" ]; then update_line_in_file "$set_env_script_path" "REGISTRY" "$REGISTRY"; fi # Assuming set_env.sh uses REPOSITORY/REGISTRY
    if [ -n "$TAG" ]; then update_line_in_file "$set_env_script_path" "IMAGE_TAG" "$TAG"; fi

    if [ -n "$HTTP_PROXY" ]; then update_line_in_file "$set_env_script_path" "HTTP_PROXY" "$HTTP_PROXY"; fi
    if [ -n "$HTTPS_PROXY" ]; then update_line_in_file "$set_env_script_path" "HTTPS_PROXY" "$HTTPS_PROXY"; fi
    if [ -n "$NO_PROXY" ]; then update_line_in_file "$set_env_script_path" "NO_PROXY" "\"$NO_PROXY\""; fi # Quote if it has commas
    [ -n "$MOUNT_DIR" ] && update_line_in_file "$set_env_script_path" "MOUNT_DIR" "$MOUNT_DIR"

    [ -n "$EMBED_MODEL" ] && export MOSEC_EMBEDDING_MODEL_ID=$EMBED_MODEL
    [ -n "$RERANK_MODEL_ID" ] && export MOSEC_RERANKING_MODEL_ID=$RERANK_MODEL_ID
    [ -n "$LLM_MODEL_ID" ] && export LLM_MODEL_ID=$LLM_MODEL_ID
    [ -n "$HUGGINGFACEHUB_API_TOKEN" ] && export HUGGINGFACEHUB_API_TOKEN=$HUGGINGFACEHUB_API_TOKEN

    log INFO "Docker configurations prepared/updated in $set_env_script_path."
    # The original script EXPORTED variables. This means the calling shell (e.g. one_click_chatqna)
    # would need to `source` this script for those exports to be effective for subsequent `docker compose` calls.
    # Alternatively, `docker compose` can use an `.env` file.
    # If `install_chatqna.sh` sources the `docker_compose/$DEVICE/set_env.sh`, then modifying that file is correct.
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