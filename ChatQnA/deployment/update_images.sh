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
COMPOSE_FILE="${BUILD_CONTEXT_PATH}/docker_build_compose.yaml"

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
#CORE_REPO_URL="https://gitee.com/intel-china/aisolution-core"
CORE_REPO_URL="https://github.com/intel-innersource/frameworks.ai.enterprise-solutions-core"
VLLM_FORK_REPO_URL="https://github.com/HabanaAI/vllm-fork.git"
VLLM_FORK_REPO_TAG="v0.6.6.post1+Gaudi-1.20.0"
VLLM_REPO_URL="https://github.com/vllm-project/vllm.git"
# VLLM version is determined dynamically later by checking out latest tag

export WORKSPACE=$repo_path # Used by compose files

declare -A components
components=(
    ["chatqna"]="chatqna opea/aisolution/chatqna"
    # ["ui-usvc"]="chatqna-ui opea/aisolution/chatqna-ui" # Assuming chatqna-ui maps to a compose service, add to YAML if needed
    ["embedding-mosec"]="embedding-mosec opea/aisolution/embedding-mosec"
    ["embedding-mosec-endpoint"]="embedding-mosec-endpoint opea/aisolution/embedding-mosec-endpoint"
    ["dataprep"]="dataprep opea/aisolution/dataprep"
    ["retriever"]="retriever opea/aisolution/retriever"
    ["reranking-mosec"]="reranking-mosec opea/aisolution/reranking-mosec"
    ["reranking-mosec-endpoint"]="reranking-mosec-endpoint opea/aisolution/reranking-mosec-endpoint"
    ["nginx"]="nginx opea/aisolution/nginx"
    ["vllm-gaudi"]="vllm-gaudi opea/vllm-gaudi"
    ["vllm-cpu"]="vllm opea/vllm"

)
# DEFAULT_COMPONENTS_LIST will be populated dynamically from COMPOSE_FILE
DEFAULT_COMPONENTS_LIST=()
# yaml_service_names will be populated by populate_default_components_from_compose
# and used in the main script body for hints.
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
    echo -e "  --registry <URL>:   Target Docker registry (e.g., mydockerhub/myproject, docker.io)."
    echo -e "  --tag <TAG>:        Image tag (default: $TAG)."
    echo -e "  --core-repo <URL>:  Git URL for core components (default: $CORE_REPO_URL)."
    echo -e "  --core-branch <B>:  Branch/tag for core components repo (default: $DEFAULT_REPO_TAG_BRANCH)."
    echo -e "  --opea-branch <B>:  Branch/tag for GenAIComps repo (default: $DEFAULT_REPO_TAG_BRANCH)."
    echo -e "  --no-cache:         Add --no-cache flag to docker compose build."
    echo -e "  --help:             Display this help message."
    echo -e ""
    echo -e "Available components (derived from compose file if found, otherwise from script's map):"
    # Dynamically list available components from the 'components' map keys
    local available_comp_args=("${!components[@]}")
    echo -e "  ${available_comp_args[*]}"
    echo -e ""
    echo -e "Example: Build specific components and push to a custom registry:"
    echo -e "  $0 --build --push --registry my-registry.com/myorg --tag v1.0 embedding-mosec-usvc"
    exit 0
}

populate_default_components_from_compose() {
    # This function populates the global 'yaml_service_names' array and 'DEFAULT_COMPONENTS_LIST'
    yaml_service_names=() # Clear global array for fresh population
    local parsed_successfully=false

    if [ ! -f "$COMPOSE_FILE" ]; then
        log WARN "Compose file '$COMPOSE_FILE' not found. Cannot dynamically determine default components."
        # Fallback logic will be handled after this block
    else
        log INFO "Deriving default components from $COMPOSE_FILE..."
        if command_exists yq; then
            log INFO "Attempting to parse $COMPOSE_FILE with yq."
            # Try yq (mikefarah/yq v4+) syntax
            mapfile -t yaml_service_names < <(yq eval '.services | keys | .[]' "$COMPOSE_FILE" 2>/dev/null)
            if [ $? -eq 0 ] && [ ${#yaml_service_names[@]} -gt 0 ]; then
                log INFO "Successfully parsed service names using yq (v4+ syntax)."
                parsed_successfully=true
            else
                # Clear if previous attempt failed or returned empty
                yaml_service_names=()
                log WARN "yq (v4+ syntax) failed or returned no services. Trying alternative yq syntax (Python yq or older mikefarah/yq)."
                # Try Python yq syntax (kislyuk/yq)
                mapfile -t yaml_service_names < <(yq -r '.services | keys | .[]' "$COMPOSE_FILE" 2>/dev/null)
                if [ $? -eq 0 ] && [ ${#yaml_service_names[@]} -gt 0 ]; then
                    log INFO "Successfully parsed service names using yq (Python yq or older mikefarah/yq syntax)."
                    parsed_successfully=true
                else
                    yaml_service_names=() # Clear again
                    log WARN "Alternative yq syntax also failed or returned no services. Will try sed fallback."
                fi
            fi
        fi

        # Fallback to sed if yq is not available or all yq attempts failed
        if ! $parsed_successfully; then
            if ! command_exists yq; then
                log INFO "yq command not found. Using sed to parse $COMPOSE_FILE (less robust)."
            else
                log INFO "All yq parsing attempts failed. Using sed to parse $COMPOSE_FILE (less robust)."
            fi
            # This sed command extracts service names indented by 2 spaces under a 'services:' block.
            mapfile -t yaml_service_names < <(sed -n '/^services:/,/^[^ ]/ { /^[ ]*$/d; /^services:/d; /^[ ]{2}\S[^:]*:/ { s/^[ ]{2}\([^:]*\):.*/\1/; p } }' "$COMPOSE_FILE")
            if [ ${#yaml_service_names[@]} -gt 0 ]; then
                log INFO "Successfully parsed service names using sed."
                parsed_successfully=true
            fi
        fi
    fi # End of if [ -f "$COMPOSE_FILE" ]

    if ! $parsed_successfully || [ ${#yaml_service_names[@]} -eq 0 ]; then
        if [ -f "$COMPOSE_FILE" ]; then # Only log this specific warning if the file existed but parsing failed
             log WARN "Failed to parse services from '$COMPOSE_FILE' using all methods, or the file has no services defined under a 'services:' key."
        fi
        log WARN "Falling back to all known components in the script's 'components' map as potential defaults."
        DEFAULT_COMPONENTS_LIST=("${!components[@]}")
        if [ ${#DEFAULT_COMPONENTS_LIST[@]} -eq 0 ]; then
             log ERROR "The 'components' map in the script is also empty. Cannot proceed."
             exit 1 # Exiting here because no components can be determined.
        fi
        yaml_service_names=() # Ensure it's empty if we are using fallback for DEFAULT_COMPONENTS_LIST
        return
    fi

    # Populate DEFAULT_COMPONENTS_LIST based on successfully parsed yaml_service_names
    local temp_default_list=()
    for service_name_from_yaml in "${yaml_service_names[@]}"; do
        local found_arg_name=""
        for comp_arg_key in "${!components[@]}"; do
            local component_details="${components[$comp_arg_key]}"
            local compose_service_name_in_map="${component_details%% *}" # Get first word

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
    if [ ${#DEFAULT_COMPONENTS_LIST[@]} -eq 0 ] && [ ${#yaml_service_names[@]} -gt 0 ]; then # If YAML had services but none mapped
        log WARN "Services were found in $COMPOSE_FILE (${yaml_service_names[*]}), but none could be mapped to known component arguments for the default list."
    elif [ ${#DEFAULT_COMPONENTS_LIST[@]} -eq 0 ]; then # If YAML had no services or they didn't map
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
    
    if docker ps  --format '{{.Names}}' | grep -qx "^${local_reg_name_const}$" > /dev/null; then
        log INFO "Local registry '$local_reg_name_const' already running."
        return 0
    fi

    if docker ps -aq -f name="^${local_reg_name_const}$" > /dev/null; then
        log INFO "Starting existing stopped local registry '$local_reg_name_const'..."
        if docker start "$local_reg_name_const"; then
            log OK "Started existing local registry '$local_reg_name_const'."
            return 0
        else
            log WARN "Failed to start existing registry container. Removing and recreating."
            docker rm -f "$local_reg_name_const" &>/dev/null || log WARN "Failed to remove existing container '$local_reg_name_const'."
        fi
    fi

    log INFO "Creating new local registry container '$local_reg_name_const' on port $local_reg_port_const..."
    if docker run -d -p "${local_reg_port_const}:${local_reg_port_const}" --restart always --name "$local_reg_name_const" "$local_reg_image_const"; then
        log OK "Local registry '$local_reg_name_const' started successfully."
        return 0
    else
        log ERROR "Failed to start new local registry container '$local_reg_name_const'."
        if [[ "$REGISTRY_NAME" == "localhost:${local_reg_port_const}" ]]; then
             log WARN "Pushing to $REGISTRY_NAME might fail."
        fi
        return 1
    fi
}


clone_or_update_repo() {
    local repo_url="$1"
    local target_path="$2"
    local branch_or_tag="$3"
    local git_clone_base_flags="--config advice.detachedHead=false"

    log INFO "Syncing repository $repo_url ($branch_or_tag) in $target_path"

    if should_clone_repo "$repo_url" "$target_path"; then
        safe_clone_repo "$repo_url" "$target_path" "$branch_or_tag" "$git_clone_base_flags"
    else
        update_existing_repo "$repo_url" "$target_path" "$branch_or_tag" || {
            log WARN "Update failed. Re-cloning..."
            safe_clone_repo "$repo_url" "$target_path" "$branch_or_tag" "$git_clone_base_flags"
        }
    fi
}

should_clone_repo() {
    local repo_url="$1"
    local target_path="$2"

    if [ ! -d "$target_path" ] || [ ! -d "$target_path/.git" ]; then
        return 0
    fi

    local current_url
    if ! current_url=$(git -C "$target_path" config --get remote.origin.url); then
        return 0
    fi

    if [[ "$current_url" != "$repo_url" ]]; then
        log WARN "Remote URL mismatch. Forcing re-clone."
        return 0
    fi

    return 1
}

update_existing_repo() {
    local repo_url="$1"
    local target_path="$2" 
    local branch_or_tag="$3"

    git -C "$target_path" reset --hard HEAD || return 1
    git -C "$target_path" clean -fd || return 1
    git -C "$target_path" fetch --all --prune --tags || return 1

    if [[ "$repo_url" == "$VLLM_REPO_URL" ]]; then
        checkout_vllm_tag "$target_path"
    else
        checkout_normal_repo "$target_path" "$branch_or_tag"
    fi
}

checkout_vllm_tag() {
    local target_path="$1"
    
    git -C "$target_path" fetch --tags > /dev/null 2>&1
    # local latest_tag=$(git -C "$target_path" describe --tags "$(git -C "$target_path" rev-list --tags --max-count=1)")
    local latest_tag="v0.8.5"
    if [ -z "$latest_tag" ]; then
        log ERROR "No vLLM tags found!"
        return 1
    fi

    log INFO "Checking out vLLM tag: $latest_tag"
    git -C "$target_path" checkout "$latest_tag" --force
}

checkout_normal_repo() {
    local target_path="$1"
    local branch_or_tag="$2"

    git -C "$target_path" checkout "$branch_or_tag" --force || return 1

    if ! is_git_tag "$target_path" "$branch_or_tag"; then
        log INFO "Pulling branch updates..."
        git -C "$target_path" pull --rebase || git -C "$target_path" pull
    fi
}

safe_clone_repo() {
    local repo_url="$1"
    local target_path="$2"
    local branch_or_tag="$3"
    local base_flags="$4"

    rm -rf "$target_path"

    if [[ "$repo_url" == "$VLLM_REPO_URL" ]]; then
        git clone $base_flags --no-single-branch "$repo_url" "$target_path"
        checkout_vllm_tag "$target_path"
    else
        git clone $base_flags --depth 1 --branch "$branch_or_tag" "$repo_url" "$target_path"
    fi
}

is_git_tag() {
    local target_path="$1"
    local ref="$2"
    git -C "$target_path" rev-parse --verify --quiet "refs/tags/$ref" >/dev/null
}


tag_and_push_func() {
    if [[ "$do_push_flag" == "false" ]]; then return 0; fi

    local target_registry_url="$1"
    # base_image_name is now the name segment that appears AFTER the registry in the final remote name
    # e.g., "chatqna" or "opea/aisolution/chatqna"
    local base_image_name="$2"
    local image_tag_to_push="$3"

    if [ -z "$target_registry_url" ] && [[ "$base_image_name" != */* ]]; then
        # If no registry specified AND base_image_name is simple (e.g. "chatqna", not "myuser/chatqna")
        # then we assume it's for official Docker Hub image, which is not what we usually do here.
        # Or, if user wants to push to their Docker Hub, they should specify --registry <username>
        log WARN "No registry URL specified (--registry) and base image name '$base_image_name' is simple."
        log WARN "If pushing to Docker Hub, please use --registry <your_dockerhub_username>."
        log WARN "Skipping push for ${base_image_name}:${image_tag_to_push}."
        return 1
    fi

    # This is the name of the image that should exist locally, prepared by the aliasing step in build_images_with_compose
    # e.g., "chatqna:latest" or "opea/aisolution/chatqna:latest"
    local local_full_image_name="${base_image_name}:${image_tag_to_push}"

    # Construct the remote image name
    local remote_full_image_name
    if [ -n "$target_registry_url" ]; then
        remote_full_image_name="${target_registry_url}/${base_image_name}:${image_tag_to_push}"
    else
        # No target_registry_url, means base_image_name should be the full name (e.g. user/repo)
        remote_full_image_name="${base_image_name}:${image_tag_to_push}"
    fi


    if ! docker image inspect "${local_full_image_name}" > /dev/null 2>&1; then
        log WARN "Local image ${local_full_image_name} not found. Cannot tag for remote or push. Build/Aliasing might have failed."
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
        docker rmi "${remote_full_image_name}" > /dev/null 2>&1 || log WARN "Could not remove local tag ${remote_full_image_name} after failed push."
        return 1
    else
        log OK "Successfully pushed ${remote_full_image_name}."
        # Optional: docker rmi "${remote_full_image_name}" > /dev/null 2>&1 # Clean up the remote-named local tag
    fi
    return 0
}

build_images_with_compose() {
    local -a services_to_build_array # Use local array for services
    services_to_build_array=("$@") # Capture all arguments into the array

    if [[ "$do_build_flag" == "false" ]]; then
        log INFO "Skipping image build (--build not specified)."
        return 0
    fi
    if [ ${#services_to_build_array[@]} -eq 0 ]; then
        log WARN "No valid services specified for build. Skipping."
        return 0
    fi

    # --- 1. Sync Dependencies ---
    section_header "Syncing Dependencies into Build Context"
    log INFO "Build context path: ${BUILD_CONTEXT_PATH}"
    mkdir -p "${BUILD_CONTEXT_PATH}"
    if ! command_exists git; then log ERROR "'git' command not found."; return 1; fi

    # Chain dependency syncing. If one fails, subsequent ones are skipped.
    ( \
        clone_or_update_repo "https://github.com/opea-project/GenAIComps.git" "${BUILD_CONTEXT_PATH}/GenAIComps" "$OPEA_REPO_BRANCH" && \
        clone_or_update_repo "$CORE_REPO_URL" "${BUILD_CONTEXT_PATH}/aisolution-core" "$CORE_REPO_BRANCH" && \
        clone_or_update_repo "$VLLM_REPO_URL" "${BUILD_CONTEXT_PATH}/vllm" "main" && \
        clone_or_update_repo "$VLLM_FORK_REPO_URL" "${BUILD_CONTEXT_PATH}/vllm-fork" "$VLLM_FORK_REPO_TAG" \
    ) || { log ERROR "Dependency syncing failed. Aborting build."; return 1; }
    log OK "Dependencies synced successfully into build context."

    # --- 2. Modify Dockerfiles (Optional - consider build args instead) ---
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
    #local CORE_REPO_DEFAULT_MAIN_URL="https://gitee.com/intel-china/aisolution-core" # Default assumed in Dockerfiles
    local CORE_REPO_DEFAULT_MAIN_URL="https://github.com/intel-innersource/frameworks.ai.enterprise-solutions-core"
    if [[ "${CORE_REPO_BRANCH}" != "main" ]] || [[ "${CORE_REPO_URL}" != "${CORE_REPO_DEFAULT_MAIN_URL}" ]]; then
        log INFO "Modifying Dockerfiles for Core repo URL: ${CORE_REPO_URL}, branch: ${CORE_REPO_BRANCH}"
        local OLD_STRING_CORE="RUN git clone ${CORE_REPO_DEFAULT_MAIN_URL}" # Might be fragile if Dockerfile changes
        local NEW_STRING_CORE="RUN git clone --depth 1 --branch ${CORE_REPO_BRANCH} ${CORE_REPO_URL}"
        find "${BUILD_CONTEXT_PATH}" -type f \( -name "Dockerfile" -o -name "Dockerfile.*" \) -print0 | while IFS= read -r -d $'\0' file; do
             if grep -qF "$OLD_STRING_CORE" "$file"; then
                 log INFO "  Updating Core repo clone in: $file"
                 sed -i.bak "s|$OLD_STRING_CORE|$NEW_STRING_CORE|g" "$file" && rm "${file}.bak"
            fi
        done
    fi
    log OK "Dockerfile modification checks complete."

    # --- 3. Docker Compose Build ---
    section_header "Building Images with Docker Compose"
    log INFO "Using Compose file: ${COMPOSE_FILE}"
    log INFO "Building services: ${services_to_build_array[*]}"
    log INFO "Log file: ${BUILD_LOG_FILE}"

    if [ ! -f "$COMPOSE_FILE" ]; then log ERROR "Compose file not found: $COMPOSE_FILE"; return 1; fi

    local -a cmd_array
    cmd_array=(docker compose -f "${COMPOSE_FILE}" build)
    # Add proxy build args if any
    if [ ${#DOCKER_BUILD_PROXY_ARGS_ARRAY[@]} -gt 0 ]; then
        cmd_array+=("${DOCKER_BUILD_PROXY_ARGS_ARRAY[@]}")
    fi
    if $do_no_cache_flag; then cmd_array+=(--no-cache); fi
    cmd_array+=("${services_to_build_array[@]}") # Add services to build

    log INFO "Executing build command:"
    # Log the command carefully, handling potential spaces in args by quoting for display
    local display_cmd=""
    for arg in "${cmd_array[@]}"; do display_cmd+="'$arg' "; done
    log INFO "$display_cmd"

    # Export variables for compose file substitution, if they are used like ${VAR} in compose
    export REGISTRY="${REGISTRY_NAME}" # For image: ${REGISTRY:-opea/aisolution}/...
    export IMAGE_TAG="${TAG}"          # For image: ...:${IMAGE_TAG:-latest}

    # Execute the command
    # Tee output to log file and also capture exit status
    local build_status=0
    { "${cmd_array[@]}" 2>&1 || build_status=$?; } | tee -a "${BUILD_LOG_FILE}"
    # Check the captured exit status
    if [ $build_status -ne 0 ]; then
        log ERROR "Docker Compose build failed with status $build_status. See log: ${BUILD_LOG_FILE}"
        return 1
    else
        log OK "Docker Compose build completed successfully."
    fi


    # --- 4. Tag Built Images (to prepare for push logic) ---
    # This step ensures that a local image exists with the name that tag_and_push_func will expect.
    section_header "Applying Local Aliases for Push Consistency"
    local tag_success_count=0
    local tag_fail_count=0

    for component_arg_name in "${components_to_build_list[@]}"; do
        local service_name_from_map base_image_name_from_map
        read -r service_name_from_map base_image_name_from_map <<< "${components[$component_arg_name]}"

        local service_was_built=false
        for srv_in_build in "${services_to_build_array[@]}"; do
            if [[ "$srv_in_build" == "$service_name_from_map" ]]; then
                service_was_built=true
                break
            fi
        done

        if ! $service_was_built; then
            continue
        fi

        # Determine the image name as built by Docker Compose
        local built_image_by_compose
        if [ -n "$REGISTRY" ]; then # Use exported REGISTRY var which was used for 'docker compose build'
            built_image_by_compose="${REGISTRY}/${service_name_from_map}:${TAG}"
        else
            built_image_by_compose="opea/aisolution/${service_name_from_map}:${TAG}"
        fi

        # Determine the target local alias name that tag_and_push_func will expect.
        # This depends on how tag_and_push_func will be called (which depends on global REGISTRY_NAME for push).
        local target_local_alias_base_name_for_push
        if [ -n "$REGISTRY_NAME" ]; then # REGISTRY_NAME here is the global one for the upcoming push operation
            target_local_alias_base_name_for_push="$service_name_from_map" # e.g., "chatqna"
        else
            target_local_alias_base_name_for_push="$base_image_name_from_map" # e.g., "opea/aisolution/chatqna"
        fi
        local final_local_alias_for_push="${target_local_alias_base_name_for_push}:${TAG}"


        if docker image inspect "$built_image_by_compose" > /dev/null 2>&1; then
            if [[ "$built_image_by_compose" != "$final_local_alias_for_push" ]]; then
                log INFO "Aliasing ${built_image_by_compose} -> ${final_local_alias_for_push} (for push consistency)"
                if docker tag "$built_image_by_compose" "$final_local_alias_for_push"; then
                    ((tag_success_count++))
                else
                    log WARN "Failed to alias ${built_image_by_compose} to ${final_local_alias_for_push}"
                    ((tag_fail_count++))
                fi
            else
                log INFO "Image ${final_local_alias_for_push} already exists (as built by compose or matches target alias name)."
                ((tag_success_count++))
            fi
        else
            log WARN "Could not find image '${built_image_by_compose}' supposedly built by Docker Compose for service '${service_name_from_map}'. Skipping local aliasing."
            ((tag_fail_count++))
        fi
    done

    log OK "Local aliasing for push consistency complete. Success: $tag_success_count, Failed/Skipped: $tag_fail_count."
    if [ $tag_fail_count -gt 0 ]; then
        log WARN "Some images may not have the expected local alias for push. Subsequent push might fail for these."
        # return 1; # Decide if this should be a fatal error
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
        *) components_to_build_list+=("$1") ;; # Collects component argument names
    esac
    shift
done

if $do_setup_registry_flag && [ -n "$REGISTRY_NAME" ]; then
    log WARN "Both --setup-registry and --registry specified, using --registry value: $REGISTRY_NAME"
fi

# --- Main Logic ---
section_header "Image Update Script Started"
log INFO "Repo Path: $repo_path, Build Context: $BUILD_CONTEXT_PATH"
log INFO "Config - Build: $do_build_flag, Push: $do_push_flag, Setup Registry: $do_setup_registry_flag, Tag: $TAG"
log INFO "Config - Registry: ${REGISTRY_NAME:-'Not set (will use compose default or opea/aisolution prefix)'}, No Cache: $do_no_cache_flag"
log INFO "Config - Core Repo: $CORE_REPO_URL ($CORE_REPO_BRANCH)"
log INFO "Config - OPEA Repo: ($OPEA_REPO_BRANCH)"
log INFO "Config - vLLM Fork: $VLLM_FORK_REPO_URL ($VLLM_FORK_REPO_TAG)"

# Populate DEFAULT_COMPONENTS_LIST and global yaml_service_names from docker_build_compose.yaml
populate_default_components_from_compose


if ! setup_local_registry_func; then
    if $do_push_flag && $do_setup_registry_flag && [[ "$REGISTRY_NAME" == "localhost:"* ]] ; then
      log ERROR "Local registry setup failed, and it was requested for push. Aborting."
      exit 1
    else
      log WARN "Failed to set up local registry. Continuing..."
    fi
fi

# Determine components to process based on user input or defaults
if [ ${#components_to_build_list[@]} -eq 0 ]; then
    if [ ${#DEFAULT_COMPONENTS_LIST[@]} -eq 0 ]; then
        log ERROR "No specific components listed for build, and could not determine default components (e.g., from $COMPOSE_FILE or internal map was empty)."
        log ERROR "Please specify components to build or ensure defaults can be determined."
        usage # Show usage, which lists available components from the 'components' map
        exit 1
    fi
    log INFO "No specific components listed, processing default components derived from $COMPOSE_FILE (or fallback)."
    components_to_build_list=("${DEFAULT_COMPONENTS_LIST[@]}")
else
    log INFO "Processing specified components: ${components_to_build_list[*]}"
fi

# Map component arguments to compose service names
services_to_process_for_compose=() # Docker compose service names
valid_component_args_for_push=()   # Valid component argument names for the push loop
for comp_arg in "${components_to_build_list[@]}"; do
    if [[ -n "${components[$comp_arg]}" ]]; then
        read -r service_name _ <<< "${components[$comp_arg]}"
        services_to_process_for_compose+=("$service_name")
        valid_component_args_for_push+=("$comp_arg")
    else
        log WARN "Unknown component argument '$comp_arg'. Skipping."
        # Check if it's a direct service name from compose file but not in our map
        # These variables are reset/re-assigned in each iteration of the loop
        is_direct_service=false
        service_names_to_check_hint=() # Re-initialize array

        # Check if the global yaml_service_names array has elements.
        # This array is populated by populate_default_components_from_compose.
        if [ ${#yaml_service_names[@]} -gt 0 ]; then
            service_names_to_check_hint=("${yaml_service_names[@]}")
        else
            # Fallback: check against known service names from the components map itself
            for comp_key_for_hint in "${!components[@]}"; do
                service_names_to_check_hint+=("$(echo "${components[$comp_key_for_hint]}" | awk '{print $1}')")
            done
        fi

        for yaml_service_name_check in "${service_names_to_check_hint[@]}"; do
            if [[ "$comp_arg" == "$yaml_service_name_check" ]]; then
                is_direct_service=true; break
            fi
        done
        if $is_direct_service; then
             log WARN "Hint: '$comp_arg' looks like a service name from $COMPOSE_FILE. To build it, ensure it has an entry in the 'components' map in this script."
        fi
    fi
done

if [ ${#services_to_process_for_compose[@]} -eq 0 ]; then
    log WARN "No valid components selected for processing. Exiting."
    exit 0
fi
log INFO "Mapped to Docker Compose services for build: ${services_to_process_for_compose[*]}"


# Build images if requested
if $do_build_flag; then
    # Pass the array of compose service names to the build function
    if ! build_images_with_compose "${services_to_process_for_compose[@]}"; then
        log ERROR "Image building process failed."
        exit 1
    fi
else
    log INFO "Skipping build phase (--build not specified)."
fi

# Push images if requested
if $do_push_flag; then
    section_header "Pushing Images"
    # REGISTRY_NAME is the global target registry for push.
    # tag_and_push_func has a check for empty REGISTRY_NAME if base_image_name is simple.
    # For consistency, we could add a primary check here too.
    if [ -z "$REGISTRY_NAME" ]; then
        # Check if any image to be pushed implies a namespaced image name (e.g. myuser/myimage)
        # This is a bit more complex to check perfectly here without inspecting all base_names.
        # The check within tag_and_push_func is more robust per image.
        log WARN "Target registry not specified via --registry. Push might be ambiguous or fail for non-namespaced images."
        log WARN "If pushing to Docker Hub, provide --registry <your_dockerhub_username>."
    fi
    log INFO "Attempting to push to registry: '${REGISTRY_NAME:-"Default (e.g., Docker Hub, image name must be namespaced)"}' with tag: $TAG"

    push_failed_count=0
    # Iterate using valid_component_args_for_push which are the user-facing names that were validated
    for component_arg_name in "${valid_component_args_for_push[@]}"; do
        # service_name_from_map: e.g., "chatqna"
        # base_image_name_from_components_map: e.g., "opea/aisolution/chatqna"
        read -r service_name_from_map base_image_name_from_components_map <<< "${components[$component_arg_name]}"

        # Determine the base name to use for the tag_and_push_func call.
        # This is the name segment that appears AFTER the registry in the final remote name.
        # This variable is reset/re-assigned in each iteration of the loop
        base_name_for_push_call=""
        if [ -n "$REGISTRY_NAME" ]; then
            # If a registry is specified for push, the path on that registry is just the service name.
            base_name_for_push_call="$service_name_from_map" # e.g., "chatqna"
        else
            # If no registry specified (e.g. pushing "opea/aisolution/chatqna" to Docker Hub under implicit user)
            # the base_image_name itself is the full path.
            base_name_for_push_call="$base_image_name_from_components_map" # e.g., "opea/aisolution/chatqna"
        fi

        log INFO "--- Pushing component: $component_arg_name (image base for push: ${base_name_for_push_call}:${TAG}) ---"
        if ! tag_and_push_func "$REGISTRY_NAME" "$base_name_for_push_call" "$TAG"; then
            log WARN "Failed or skipped push for component: $component_arg_name"
            ((push_failed_count++))
        fi
    done

    if [ $push_failed_count -gt 0 ]; then
        log ERROR "$push_failed_count image(s) failed to push."
        # exit 1 # Optional: exit if any push fails
    else
        log OK "All requested images pushed successfully."
    fi
else
    log INFO "Skipping push phase (--push not specified)."
fi


section_header "Image Update Script Finished Successfully"
exit 0
