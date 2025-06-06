#!/bin/bash
# Copyright (C) 2024 Intel Corporation
# SPDX-License-Identifier: Apache-2.0

set -e
set -o pipefail

SCRIPT_DIR_UPDATE=$(cd "$(dirname "${BASH_SOURCE[0]}")" &>/dev/null && pwd)
source "${SCRIPT_DIR_UPDATE}/utils.sh" # Provides log, section_header, command_exists

repo_path=$(realpath "${SCRIPT_DIR_UPDATE}/../")

# --- Configuration ---
BUILD_CONTEXT_REL_PATH="deployment/docker_image_build"
BUILD_CONTEXT_PATH="${repo_path}/${BUILD_CONTEXT_REL_PATH}"
COMPOSE_FILE="${BUILD_CONTEXT_PATH}/build.yaml" # Updated Compose file name

LOG_DIR="${repo_path}/logs"
mkdir -p "$LOG_DIR"
BUILD_LOG_FILE="${LOG_DIR}/docker_compose_build_$(date +%Y%m%d_%H%M%S).log"

# Registry and Tagging Defaults
REGISTRY_NAME="" # Set via --registry or --setup-registry
TAG="latest"

# Dependency Repository Defaults
DEFAULT_REPO_TAG_BRANCH="main"
OPEA_REPO_BRANCH="${DEFAULT_REPO_TAG_BRANCH}"
CORE_REPO_BRANCH="${DEFAULT_REPO_TAG_BRANCH}"
CORE_REPO_URL="https://github.com/intel-innersource/frameworks.ai.enterprise-solutions-core"
VLLM_FORK_REPO_URL="https://github.com/HabanaAI/vllm-fork.git"
VLLM_FORK_REPO_TAG="v0.6.6.post1+Gaudi-1.20.0"
VLLM_REPO_URL="https://github.com/vllm-project/vllm.git"
# VLLM version for main repo is determined dynamically later by checking out latest tag (or hardcoded in function)

export WORKSPACE=$repo_path # Used by compose files

declare -A components
components=(
    ["chatqna"]="chatqna opea/chatqna"
    ["chatqna-ui"]="chatqna-ui opea/chatqna-ui"
    ["chatqna-conversation-ui"]="chatqna-conversation-ui opea/chatqna-conversation-ui"
    ["embedding"]="embedding opea/embedding"
    ["retriever"]="retriever opea/retriever"
    ["reranking"]="reranking opea/reranking"
    ["llm-textgen"]="llm-textgen opea/llm-textgen"
    ["llm-faqgen"]="llm-faqgen opea/llm-faqgen"
    ["dataprep"]="dataprep opea/dataprep"
    ["guardrails"]="guardrails opea/guardrails"
    ["vllm-rocm"]="vllm-rocm opea/vllm-rocm"
    ["vllm"]="vllm opea/vllm" # For CPU vLLM
    ["vllm-gaudi"]="vllm-gaudi opea/vllm-gaudi"
    ["nginx"]="nginx opea/nginx"
)

DEFAULT_COMPONENTS_LIST=()
declare -a yaml_service_names

components_to_build_list=() # User specified components

# Proxies for Docker build
DOCKER_BUILD_PROXY_ARGS_ARRAY=()
[ -n "$http_proxy" ] && DOCKER_BUILD_PROXY_ARGS_ARRAY+=(--build-arg "http_proxy=$http_proxy")
[ -n "$https_proxy" ] && DOCKER_BUILD_PROXY_ARGS_ARRAY+=(--build-arg "https_proxy=$https_proxy")
[ -n "$no_proxy" ] && DOCKER_BUILD_PROXY_ARGS_ARRAY+=(--build-arg "no_proxy=$no_proxy")

# --- Functions ---

usage() {
    echo -e "Usage: $0 [OPTIONS] [COMPONENTS_TO_BUILD...]"
    echo -e "Builds OPEA microservice images using Docker Compose."
    echo -e "Handles Git dependencies efficiently (updates existing repos, clones new ones)."
    echo -e ""
    echo -e "Options:"
    echo -e "  --build:            Build specified components (or defaults if none specified)."
    echo -e "  --push:             Push built images to the registry."
    echo -e "  --setup-registry:   Setup a local Docker registry (localhost:5000)."
    echo -e "  --registry <URL>:   Target Docker registry (e.g., mydockerhub/myproject, docker.io/myuser)."
    echo -e "  --tag <TAG>:        Image tag (default: $TAG)."
    echo -e "  --core-repo <URL>:  Git URL for core components (default: $CORE_REPO_URL)."
    echo -e "  --core-branch <B>:  Branch/tag for core components repo (default: $DEFAULT_REPO_TAG_BRANCH)."
    echo -e "  --opea-branch <B>:  Branch/tag for GenAIComps repo (default: $DEFAULT_REPO_TAG_BRANCH)."
    echo -e "  --no-cache:         Add --no-cache flag to docker compose build."
    echo -e "  --help:             Display this help message."
    echo -e ""
    echo -e "Available components (derived from compose file if found, otherwise from script's map):"
    local available_comp_args=("${!components[@]}")
    echo -e "  ${available_comp_args[*]}"
    echo -e ""
    echo -e "Example: Build specific components and push to a custom registry:"
    echo -e "  $0 --build --push --registry my-registry.com/myorg --tag v1.0 embedding"
    exit 0
}

populate_default_components_from_compose() {
    yaml_service_names=()
    local parsed_successfully=false

    if [ ! -f "$COMPOSE_FILE" ]; then
        log WARN "Compose file '$COMPOSE_FILE' not found. Cannot dynamically determine default components."
    else
        log INFO "Deriving default components from $COMPOSE_FILE..."
        if command_exists yq; then
            log INFO "Attempting to parse $COMPOSE_FILE with yq."
            mapfile -t yaml_service_names < <(yq eval '.services | keys | .[]' "$COMPOSE_FILE" 2>/dev/null)
            if [ $? -eq 0 ] && [ ${#yaml_service_names[@]} -gt 0 ]; then
                parsed_successfully=true
            else
                yaml_service_names=()
                log WARN "yq (v4+ syntax) failed or returned no services. Trying alternative yq syntax."
                mapfile -t yaml_service_names < <(yq -r '.services | keys | .[]' "$COMPOSE_FILE" 2>/dev/null)
                if [ $? -eq 0 ] && [ ${#yaml_service_names[@]} -gt 0 ]; then
                    parsed_successfully=true
                fi
            fi
        fi

        if ! $parsed_successfully; then
            if ! command_exists yq; log INFO "yq command not found."; else log INFO "All yq parsing attempts failed."; fi
            log INFO "Using sed to parse $COMPOSE_FILE (less robust)."
            mapfile -t yaml_service_names < <(sed -n '/^services:/,/^[^ ]/ { /^[ ]*$/d; /^services:/d; /^[ ]{2}\S[^:]*:/ { s/^[ ]{2}\([^:]*\):.*/\1/; p } }' "$COMPOSE_FILE")
            if [ ${#yaml_service_names[@]} -gt 0 ]; then
                parsed_successfully=true
            fi
        fi
    fi

    if ! $parsed_successfully || [ ${#yaml_service_names[@]} -eq 0 ]; then
        if [ -f "$COMPOSE_FILE" ]; then
             log WARN "Failed to parse services from '$COMPOSE_FILE', or it has no services defined."
        fi
        log WARN "Falling back to all known components in the script's 'components' map."
        DEFAULT_COMPONENTS_LIST=("${!components[@]}")
        if [ ${#DEFAULT_COMPONENTS_LIST[@]} -eq 0 ]; then
             log ERROR "The 'components' map in the script is also empty. Cannot proceed."
             exit 1
        fi
        yaml_service_names=()
        return
    fi

    local temp_default_list=()
    for service_name_from_yaml in "${yaml_service_names[@]}"; do
        local found_arg_name=""
        for comp_arg_key in "${!components[@]}"; do
            local component_details="${components[$comp_arg_key]}"
            local compose_service_name_in_map="${component_details%% *}"
            if [[ "$compose_service_name_in_map" == "$service_name_from_yaml" ]]; then
                found_arg_name="$comp_arg_key"
                break
            fi
        done
        if [[ -n "$found_arg_name" ]]; then
            temp_default_list+=("$found_arg_name")
        else
            log INFO "Service '$service_name_from_yaml' from $COMPOSE_FILE has no mapping in 'components' array. It won't be a default arg."
        fi
    done
    DEFAULT_COMPONENTS_LIST=("${temp_default_list[@]}")
    log INFO "Default components derived from compose file: ${DEFAULT_COMPONENTS_LIST[*]}"
    if [ ${#DEFAULT_COMPONENTS_LIST[@]} -eq 0 ]; then
         log WARN "No services from $COMPOSE_FILE could be mapped to known component arguments. Default list is empty."
    fi
}

setup_local_registry_func() {
    local local_reg_name_const="local-docker-registry"
    local local_reg_port_const=5000
    local local_reg_image_const="registry:2"

    if $do_setup_registry_flag && [ -z "$REGISTRY_NAME" ]; then
        REGISTRY_NAME="localhost:${local_reg_port_const}"
        log INFO "Using local registry: $REGISTRY_NAME"
    fi

    if ! $do_setup_registry_flag; then return 0; fi

    log INFO "Setting up local registry '$local_reg_name_const'..."
    if docker ps --format '{{.Names}}' | grep -qx "^${local_reg_name_const}$" > /dev/null; then
        log INFO "Local registry '$local_reg_name_const' already running."
        return 0
    fi
    if docker ps -aq -f name="^${local_reg_name_const}$" > /dev/null; then
        log INFO "Starting existing stopped local registry '$local_reg_name_const'..."
        if docker start "$local_reg_name_const"; then log OK "Started existing local registry."; return 0; fi
        log WARN "Failed to start existing registry. Removing and recreating."
        docker rm -f "$local_reg_name_const" &>/dev/null
    fi
    log INFO "Creating new local registry container '$local_reg_name_const' on port $local_reg_port_const..."
    if docker run -d -p "${local_reg_port_const}:${local_reg_port_const}" --restart always --name "$local_reg_name_const" "$local_reg_image_const"; then
        log OK "Local registry '$local_reg_name_const' started."
    else
        log ERROR "Failed to start new local registry container '$local_reg_name_const'."
        if [[ "$REGISTRY_NAME" == "localhost:${local_reg_port_const}" ]]; then log WARN "Pushing to $REGISTRY_NAME might fail."; fi
        return 1
    fi
}

clone_or_update_repo() {
    local repo_url="$1"
    local target_path="$2"
    local branch_or_tag="$3"
    local git_clone_base_flags="--config advice.detachedHead=false"

    log INFO "Syncing repository $repo_url ($branch_or_tag) in $target_path"
    if [ ! -d "$target_path/.git" ] || [[ "$(git -C "$target_path" config --get remote.origin.url)" != "$repo_url" ]]; then
        log INFO "Cloning $repo_url..."
        rm -rf "$target_path"
        if [[ "$repo_url" == "$VLLM_REPO_URL" ]]; then # Special handling for main vLLM repo for specific tag checkout
            git clone $git_clone_base_flags --no-single-branch "$repo_url" "$target_path" || { log ERROR "Clone failed."; return 1; }
            checkout_vllm_tag "$target_path" || return 1
        else
            git clone $git_clone_base_flags --depth 1 --branch "$branch_or_tag" "$repo_url" "$target_path" || { log ERROR "Clone failed."; return 1; }
        fi
    else
        log INFO "Updating existing repo $target_path..."
        ( # Subshell for safer cd and operations
            cd "$target_path" || return 1
            git reset --hard HEAD || return 1
            git clean -fd || return 1
            git fetch --all --prune --tags || return 1
            if [[ "$repo_url" == "$VLLM_REPO_URL" ]]; then
                checkout_vllm_tag "." || return 1 # Pass current dir
            else
                git checkout "$branch_or_tag" --force || return 1
                # If it's a branch (not a tag), pull updates
                if ! git rev-parse --verify --quiet "refs/tags/$branch_or_tag" >/dev/null; then
                    log INFO "Pulling branch updates for $branch_or_tag..."
                    git pull --rebase || git pull || return 1
                fi
            fi
        ) || { log WARN "Update failed for $target_path. Re-cloning might be needed if issues persist."; return 1; }
    fi
    log OK "Repository $repo_url synced successfully."
}

checkout_vllm_tag() {
    local target_path="$1" # Expected to be the path to the vLLM repo
    git -C "$target_path" fetch --tags > /dev/null 2>&1
    # local latest_tag=$(git -C "$target_path" describe --tags "$(git -C "$target_path" rev-list --tags --max-count=1)")
    local latest_tag="v0.8.5" # Keeping this as per original script, can be parameterized if needed
    if [ -z "$latest_tag" ]; then
        log ERROR "No vLLM tags found in $target_path!"
        return 1
    fi
    log INFO "Checking out vLLM tag: $latest_tag in $target_path"
    git -C "$target_path" checkout "$latest_tag" --force || { log ERROR "Failed to checkout vLLM tag $latest_tag"; return 1; }
}

tag_and_push_func() {
    if [[ "$do_push_flag" == "false" ]]; then return 0; fi

    local target_registry_url="$1"
    local base_image_name="$2" # e.g., "chatqna" or "opea/chatqna"
    local image_tag_to_push="$3"

    if [ -z "$target_registry_url" ] && [[ "$base_image_name" != */* ]]; then
        log WARN "No registry URL specified (--registry) and base image name '$base_image_name' is simple."
        log WARN "If pushing to Docker Hub, use --registry <your_dockerhub_username>. Skipping push for ${base_image_name}:${image_tag_to_push}."
        return 1
    fi

    local local_full_image_name="${base_image_name}:${image_tag_to_push}"
    local remote_full_image_name
    if [ -n "$target_registry_url" ]; then
        remote_full_image_name="${target_registry_url}/${base_image_name}:${image_tag_to_push}"
    else
        remote_full_image_name="${base_image_name}:${image_tag_to_push}"
    fi

    if ! docker image inspect "${local_full_image_name}" > /dev/null 2>&1; then
        log WARN "Local image ${local_full_image_name} not found. Cannot tag or push. Build/Aliasing might have failed."
        return 1
    fi

    log INFO "Tagging $local_full_image_name -> $remote_full_image_name"
    if ! docker tag "${local_full_image_name}" "${remote_full_image_name}"; then
        log ERROR "Failed to tag ${local_full_image_name} for remote push to ${remote_full_image_name}."
        return 1
    fi

    log INFO "Pushing ${remote_full_image_name}..."
    if ! docker push "${remote_full_image_name}"; then
        log ERROR "Failed to push ${remote_full_image_name}."
        docker rmi "${remote_full_image_name}" > /dev/null 2>&1 # Attempt to clean up local tag
        return 1
    fi
    log OK "Successfully pushed ${remote_full_image_name}."
    return 0
}

build_images_with_compose() {
    local -a services_to_build_array=("$@")

    if [[ "$do_build_flag" == "false" ]]; then log INFO "Skipping image build."; return 0; fi
    if [ ${#services_to_build_array[@]} -eq 0 ]; then log WARN "No valid services for build. Skipping."; return 0; fi

    section_header "Syncing Dependencies into Build Context"
    log INFO "Build context path: ${BUILD_CONTEXT_PATH}"
    mkdir -p "${BUILD_CONTEXT_PATH}"
    if ! command_exists git; then log ERROR "'git' command not found."; return 1; fi

    ( \
        clone_or_update_repo "https://github.com/opea-project/GenAIComps.git" "${BUILD_CONTEXT_PATH}/GenAIComps" "$OPEA_REPO_BRANCH" && \
        clone_or_update_repo "$CORE_REPO_URL" "${BUILD_CONTEXT_PATH}/aisolution-core" "$CORE_REPO_BRANCH" && \
        clone_or_update_repo "$VLLM_REPO_URL" "${BUILD_CONTEXT_PATH}/vllm" "main" && \
        clone_or_update_repo "$VLLM_FORK_REPO_URL" "${BUILD_CONTEXT_PATH}/vllm-fork" "$VLLM_FORK_REPO_TAG" \
    ) || { log ERROR "Dependency syncing failed. Aborting build."; return 1; }
    log OK "Dependencies synced successfully."

    section_header "Checking Dockerfile Modifications (if needed)"
    if [[ "${OPEA_REPO_BRANCH}" != "main" ]]; then
        log INFO "Modifying Dockerfiles for GenAIComps branch: ${OPEA_REPO_BRANCH}"
        local OLD_STRING_GENAI="RUN git clone --depth 1 https://github.com/opea-project/GenAIComps.git"
        local NEW_STRING_GENAI="RUN git clone --depth 1 --branch ${OPEA_REPO_BRANCH} https://github.com/opea-project/GenAIComps.git"
        find "${BUILD_CONTEXT_PATH}" -type f \( -name "Dockerfile" -o -name "Dockerfile.*" \) -print0 | while IFS= read -r -d $'\0' file; do
            if grep -qF "$OLD_STRING_GENAI" "$file"; then
                log INFO "  Updating GenAIComps clone in: $file"
                sed -i.bak "s|$OLD_STRING_GENAI|$NEW_STRING_GENAI|g" "$file" && rm "${file}.bak"
            fi
        done
    fi
    local CORE_REPO_DEFAULT_MAIN_URL_IN_DOCKERFILES="https://github.com/intel-innersource/frameworks.ai.enterprise-solutions-core" # Default assumed in Dockerfiles
    if [[ "${CORE_REPO_BRANCH}" != "main" ]] || [[ "${CORE_REPO_URL}" != "${CORE_REPO_DEFAULT_MAIN_URL_IN_DOCKERFILES}" ]]; then
        log INFO "Modifying Dockerfiles for Core repo URL: ${CORE_REPO_URL}, branch: ${CORE_REPO_BRANCH}"
        # Be careful with this string, ensure it matches exactly what's in Dockerfiles
        local OLD_STRING_CORE="RUN git clone ${CORE_REPO_DEFAULT_MAIN_URL_IN_DOCKERFILES}"
        local NEW_STRING_CORE="RUN git clone --depth 1 --branch ${CORE_REPO_BRANCH} ${CORE_REPO_URL}"
        find "${BUILD_CONTEXT_PATH}" -type f \( -name "Dockerfile" -o -name "Dockerfile.*" \) -print0 | while IFS= read -r -d $'\0' file; do
             if grep -qF "$OLD_STRING_CORE" "$file"; then
                 log INFO "  Updating Core repo clone in: $file"
                 sed -i.bak "s|$OLD_STRING_CORE|$NEW_STRING_CORE|g" "$file" && rm "${file}.bak"
            fi
        done
    fi
    log OK "Dockerfile modification checks complete."

    section_header "Building Images with Docker Compose"
    log INFO "Using Compose file: ${COMPOSE_FILE}"
    log INFO "Building services: ${services_to_build_array[*]}"
    log INFO "Log file: ${BUILD_LOG_FILE}"
    if [ ! -f "$COMPOSE_FILE" ]; then log ERROR "Compose file not found: $COMPOSE_FILE"; return 1; fi

    local -a cmd_array
    cmd_array=(docker compose -f "${COMPOSE_FILE}" build)
    if [ ${#DOCKER_BUILD_PROXY_ARGS_ARRAY[@]} -gt 0 ]; then
        cmd_array+=("${DOCKER_BUILD_PROXY_ARGS_ARRAY[@]}")
    fi
    if $do_no_cache_flag; then cmd_array+=(--no-cache); fi
    cmd_array+=("${services_to_build_array[@]}")

    log INFO "Executing build command:"
    local display_cmd=""
    for arg in "${cmd_array[@]}"; do display_cmd+="'$arg' "; done
    log INFO "$display_cmd"

    export REGISTRY="${REGISTRY_NAME}"
    export TAG="${TAG}" # Ensure TAG is exported for compose file's ${TAG:-latest}

    local build_status=0
    { "${cmd_array[@]}" 2>&1 || build_status=$?; } | tee -a "${BUILD_LOG_FILE}"
    if [ $build_status -ne 0 ]; then
        log ERROR "Docker Compose build failed (status $build_status). See log: ${BUILD_LOG_FILE}"
        return 1
    fi
    log OK "Docker Compose build completed."

    section_header "Applying Local Aliases for Push Consistency"
    local tag_success_count=0
    local tag_fail_count=0

    for component_arg_name in "${components_to_build_list[@]}"; do
        local service_name_from_map base_image_name_from_map
        read -r service_name_from_map base_image_name_from_map <<< "${components[$component_arg_name]}"

        local service_was_built=false
        for srv_in_build in "${services_to_build_array[@]}"; do
            if [[ "$srv_in_build" == "$service_name_from_map" ]]; then service_was_built=true; break; fi
        done
        if ! $service_was_built; then continue; fi

        local built_image_by_compose
        # REGISTRY is the env var passed to compose, TAG is also env var.
        if [ -n "$REGISTRY" ]; then
            built_image_by_compose="${REGISTRY}/${service_name_from_map}:${TAG}"
        else
            # Default from build.yaml's image field pattern ${REGISTRY:-opea}/...
            built_image_by_compose="opea/${service_name_from_map}:${TAG}"
        fi

        local target_local_alias_base_name_for_push
        # REGISTRY_NAME is the script's global var for push operation target
        if [ -n "$REGISTRY_NAME" ]; then
            target_local_alias_base_name_for_push="$service_name_from_map"
        else
            target_local_alias_base_name_for_push="$base_image_name_from_map" # e.g. "opea/chatqna"
        fi
        local final_local_alias_for_push="${target_local_alias_base_name_for_push}:${TAG}"

        if docker image inspect "$built_image_by_compose" > /dev/null 2>&1; then
            if [[ "$built_image_by_compose" != "$final_local_alias_for_push" ]]; then
                log INFO "Aliasing ${built_image_by_compose} -> ${final_local_alias_for_push}"
                if docker tag "$built_image_by_compose" "$final_local_alias_for_push"; then
                    ((tag_success_count++))
                else
                    log WARN "Failed to alias ${built_image_by_compose} to ${final_local_alias_for_push}"
                    ((tag_fail_count++))
                fi
            else
                log INFO "Image ${final_local_alias_for_push} already exists as expected."
                ((tag_success_count++))
            fi
        else
            log WARN "Image '${built_image_by_compose}' (for service '${service_name_from_map}') not found after build. Skipping alias."
            ((tag_fail_count++))
        fi
    done

    log OK "Local aliasing complete. Success: $tag_success_count, Failed/Skipped: $tag_fail_count."
    if [ $tag_fail_count -gt 0 ]; then
        log WARN "Some images may not have the expected local alias for push."
    fi
    return 0
}

# --- Argument Parsing ---
do_build_flag=false
do_push_flag=false
do_setup_registry_flag=false
do_no_cache_flag=false

while [ $# -gt 0 ]; do
    case "$1" in
        --build) do_build_flag=true ;;
        --push) do_push_flag=true ;;
        --setup-registry) do_setup_registry_flag=true ;;
        --registry) REGISTRY_NAME="$2"; shift ;;
        --tag) TAG="$2"; shift ;;
        --core-repo) CORE_REPO_URL="$2"; shift ;;
        --core-branch) CORE_REPO_BRANCH="$2"; shift ;;
        --opea-branch) OPEA_REPO_BRANCH="$2"; shift ;;
        --no-cache) do_no_cache_flag=true ;;
        --help) usage ;;
        -*) log ERROR "Unknown option: $1"; usage ;;
        *) components_to_build_list+=("$1") ;;
    esac
    shift
done

if $do_setup_registry_flag && [ -n "$REGISTRY_NAME" ]; then
    log WARN "Both --setup-registry and --registry specified, using --registry value: $REGISTRY_NAME"
fi

# --- Main Logic ---
section_header "Image Update Script Started"
log INFO "Repo Path: $repo_path, Build Context Root: $BUILD_CONTEXT_PATH, Compose File: $COMPOSE_FILE"
log INFO "Config - Build: $do_build_flag, Push: $do_push_flag, Setup Registry: $do_setup_registry_flag, Tag: $TAG"
log INFO "Config - Registry: ${REGISTRY_NAME:-'Default (opea/ prefix or as in compose)'}, No Cache: $do_no_cache_flag"
log INFO "Config - Core Repo: $CORE_REPO_URL ($CORE_REPO_BRANCH)"
log INFO "Config - GenAIComps Repo: ($OPEA_REPO_BRANCH)" # OPEA_REPO_URL is hardcoded in clone_or_update_repo
log INFO "Config - vLLM Fork: $VLLM_FORK_REPO_URL ($VLLM_FORK_REPO_TAG)"

populate_default_components_from_compose

if ! setup_local_registry_func; then
    if $do_push_flag && $do_setup_registry_flag && [[ "$REGISTRY_NAME" == "localhost:"* ]] ; then
      log ERROR "Local registry setup failed, and it was requested for push. Aborting."
      exit 1
    fi
    log WARN "Failed to set up local registry. Continuing..."
fi

if [ ${#components_to_build_list[@]} -eq 0 ]; then
    if [ ${#DEFAULT_COMPONENTS_LIST[@]} -eq 0 ]; then
        log ERROR "No specific components listed for build, and could not determine default components."
        usage
        exit 1
    fi
    log INFO "Using default components: ${DEFAULT_COMPONENTS_LIST[*]}"
    components_to_build_list=("${DEFAULT_COMPONENTS_LIST[@]}")
else
    log INFO "Processing specified components: ${components_to_build_list[*]}"
fi

services_to_process_for_compose=()
valid_component_args_for_push=()
for comp_arg in "${components_to_build_list[@]}"; do
    if [[ -n "${components[$comp_arg]}" ]]; then
        read -r service_name _ <<< "${components[$comp_arg]}"
        services_to_process_for_compose+=("$service_name")
        valid_component_args_for_push+=("$comp_arg")
    else
        log WARN "Unknown component argument '$comp_arg'. Skipping."
        local is_direct_service=false
        local service_names_to_check_hint=()
        if [ ${#yaml_service_names[@]} -gt 0 ]; then
            service_names_to_check_hint=("${yaml_service_names[@]}")
        else
            for comp_key_for_hint in "${!components[@]}"; do
                service_names_to_check_hint+=("$(echo "${components[$comp_key_for_hint]}" | awk '{print $1}')")
            done
        fi
        for yaml_service_name_check in "${service_names_to_check_hint[@]}"; do
            if [[ "$comp_arg" == "$yaml_service_name_check" ]]; then is_direct_service=true; break; fi
        done
        if $is_direct_service; then
             log WARN "Hint: '$comp_arg' is a service name from $COMPOSE_FILE. Ensure it's mapped in the 'components' script map."
        fi
    fi
done

if [ ${#services_to_process_for_compose[@]} -eq 0 ]; then
    log WARN "No valid components selected for processing. Exiting."
    exit 0
fi
log INFO "Mapped to Docker Compose services for build: ${services_to_process_for_compose[*]}"

if $do_build_flag; then
    if ! build_images_with_compose "${services_to_process_for_compose[@]}"; then
        log ERROR "Image building process failed."
        exit 1
    fi
else
    log INFO "Skipping build phase (--build not specified)."
fi

if $do_push_flag; then
    section_header "Pushing Images"
    if [ -z "$REGISTRY_NAME" ]; then
        log WARN "Target registry not specified via --registry. Push might be ambiguous or fail for non-namespaced images."
        log WARN "If pushing to Docker Hub for an organization (e.g. 'opea'), use --registry docker.io/opea or ensure image names in compose are fully qualified for Docker Hub user."
    fi
    log INFO "Attempting to push to registry: '${REGISTRY_NAME:-"Default (e.g., Docker Hub, image name must be namespaced or use default 'opea/' prefix)"}' with tag: $TAG"

    push_failed_count=0
    for component_arg_name in "${valid_component_args_for_push[@]}"; do
        read -r service_name_from_map base_image_name_from_components_map <<< "${components[$component_arg_name]}"
        base_name_for_push_call=""
        if [ -n "$REGISTRY_NAME" ]; then
            base_name_for_push_call="$service_name_from_map"
        else
            base_name_for_push_call="$base_image_name_from_components_map"
        fi

        log INFO "--- Pushing component: $component_arg_name (image base for push: ${base_name_for_push_call}:${TAG}) ---"
        if ! tag_and_push_func "$REGISTRY_NAME" "$base_name_for_push_call" "$TAG"; then
            log WARN "Failed or skipped push for component: $component_arg_name"
            ((push_failed_count++))
        fi
    done

    if [ $push_failed_count -gt 0 ]; then
        log ERROR "$push_failed_count image(s) failed to push."
    else
        log OK "All requested images pushed successfully (or skipped as per config)."
    fi
else
    log INFO "Skipping push phase (--push not specified)."
fi

section_header "Image Update Script Finished Successfully"
exit 0
