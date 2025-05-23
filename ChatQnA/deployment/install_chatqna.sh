#!/bin/bash
# Copyright (C) 2024 Intel Corporation
# SPDX-License-Identifier: Apache-2.0

# Script's own directory
SCRIPT_DIR_INSTALL=$(cd "$(dirname "${BASH_SOURCE[0]}")" &>/dev/null && pwd)
source "${SCRIPT_DIR_INSTALL}/utils.sh" # Assuming utils.sh is in the same directory
# LOG_FILE="install_chatqna.log" # Optional: specific log file

# Paths
repo_path=$(realpath "$SCRIPT_DIR_INSTALL/../")
manifests_path="$repo_path/deployment/kubernetes"
compose_path="$repo_path/deployment/docker_compose"
set_values_script_path="$SCRIPT_DIR_INSTALL/set_values.sh"

# Namespaces
DEPLOYMENT_NS=chatqna
UI_NS=rag-ui # Used in clear_all_k8s_namespaces

# Deployment variables
DEVICE="" # Target platform: gaudi, xeon
DEPLOY_MODE="docker" # k8s or docker
REGISTRY=""
TAG="latest"
MOUNT_DIR=""
EMBED_MODEL=""
RERANK_MODEL_ID=""
LLM_MODEL_ID=""
HUGGINGFACEHUB_API_TOKEN="" # Mandatory for actual model fetching if not cached
HTTP_PROXY=""
HTTPS_PROXY=""
NO_PROXY=""

# Dynamically find available devices based on subdirectories in manifests_path (for K8s) or compose_path (for Docker)
# This provides a dynamic list for the help message if needed.
get_available_devices() {
    local search_path=""
    if [[ "$DEPLOY_MODE" == "k8s" && -d "$manifests_path" ]]; then
        search_path="$manifests_path"
    elif [[ "$DEPLOY_MODE" == "docker" && -d "$compose_path" ]]; then
        search_path="$compose_path"
    else
        echo "gaudi,xeon" # Fallback
        return
    fi
    # List subdirectories that presumably correspond to devices
    (cd "$search_path" && find . -maxdepth 1 -mindepth 1 -type d -exec basename {} \; | paste -sd ',' || echo "gaudi,xeon")
}
available_devices=$(get_available_devices) # Call once or dynamically if DEPLOY_MODE changes before usage

function usage() {
    # Update available_devices if DEPLOY_MODE might change before this is called
    # For simplicity, using the one determined at script start for now.
    available_devices_for_help=$(get_available_devices)
    echo -e "Usage: $0 --device <DEVICE_NAME> --deploy-mode <MODE> [OPTIONS]"
    echo -e "Core Options:"
    echo -e "\t--device <DEVICE_NAME>: Specify the target device (e.g., $available_devices_for_help)."
    echo -e "\t--deploy-mode <MODE>:   Specify deployment mode: 'k8s' or 'docker' (default: $DEPLOY_MODE)."
    echo -e "\t--hf-token <TOKEN>:     (Required for most operations) Hugging Face Hub API token."
    echo -e "Image Options:"
    echo -e "\t--tag <TAG>:            Use specific image tag for deployment (default: $TAG)."
    echo -e "\t--registry <REGISTRY>:  Use specific container registry (e.g. mydockerhub/myproject)."
    echo -e "Model Options (Overrides defaults set by set_values.sh if not provided here):"
    echo -e "\t--mount-dir <DIR>:     Data mount directory for Docker volumes (default: ./data)."
    echo -e "\t--embed-model <MODEL_ID>: Specify the embedding model ID."
    echo -e "\t--rerank-model <MODEL_ID>:Specify the reranking model ID."
    echo -e "\t--llm-model <MODEL_ID>:   Specify the LLM model ID."
    echo -e "Proxy Options:"
    echo -e "\t--http-proxy <PROXY_URL>: HTTP proxy."
    echo -e "\t--https-proxy <PROXY_URL>:HTTPS proxy."
    echo -e "\t--no-proxy <HOST_LIST>: Comma-separated list of hosts to bypass proxy."
    echo -e "Actions:"
    echo -e "\t--deploy:               (Default action if device and mode specified) Deploy services."
    echo -e "\t--test:                 Run a connection test (requires services to be up)."
    echo -e "\t-cd, --clear-deployment:Clear deployed services for the specified device and mode."
    echo -e "\t-ca, --clear-all:       Clear ALL ChatQnA related K8s namespaces (USE WITH CAUTION, K8s mode only)."
    echo -e "\t-h, --help:             Display this help message."
    echo -e "Example: $0 --device gaudi --deploy-mode k8s --hf-token <your_token> --tag mytag --deploy"
}

# Removed helm_install - not used
# Removed start_and_keep_port_forwarding - not used

check_pods_ready() {
    local namespace="$1"
    # Check for existence of pods first
    if ! kubectl get pods -n "$namespace" --no-headers -o custom-columns="NAME:.metadata.name" 2>/dev/null | grep -q "."; then
        log WARN "No pods found in namespace $namespace. Assuming this is okay if it's early in deployment."
        return 0 # Or 1 if pods are strictly expected
    fi

    # Get all pods, then filter for not-ready ones.
    # This checks the "Ready" condition.
    not_ready_pods_details=$(kubectl get pods -n "$namespace" -o jsonpath='{range .items[*]}{.metadata.name}{range .status.conditions[?(@.type=="Ready")]}{"\t"}{.status}{end}{"\n"}{end}' 2>/dev/null | grep -v "True$" )

    if [ -n "$not_ready_pods_details" ]; then
        # log INFO "Still waiting for: $not_ready_pods_details" # Too verbose for every check
        return 1 # Found pods not ready
    else
        return 0 # All pods are ready (or no pods, handled above)
    fi
}

wait_for_pods_ready() {
    local namespace="$1"
    log INFO "Waiting for all pods in namespace '$namespace' to be ready..."
    sleep 15 # Initial delay for resources to be created/settled

    local current_time
    local timeout_seconds=2700 # 45 minutes
    local end_time=$(( $(date +%s) + timeout_seconds ))
    local print_interval=30 # Print status every 30 seconds
    local next_print_time=$(date +%s)

    while true; do
        current_time=$(date +%s)
        if [[ "$current_time" -ge "$end_time" ]]; then
            log ERROR "Timeout reached: Pods in namespace '$namespace' not ready after $((timeout_seconds / 60)) minutes."
            kubectl get pods -n "$namespace" -o wide >> "$LOG_FILE" # Log current pod status
            return 1
        fi

        if check_pods_ready "$namespace"; then
            log OK "All pods in namespace '$namespace' are ready."
            return 0
        else
            if [[ "$current_time" -ge "$next_print_time" ]]; then
                printf "." # Progress indicator
                # log INFO "Still waiting for pods in $namespace..." # Optional more verbose log
                next_print_time=$((current_time + print_interval))
            fi
            sleep 10 # Check interval
        fi
    done
}


kill_processes_by_pattern() {
    local pattern="$1"
    local pids
    mapfile -t pids < <(pgrep -f "$pattern") # -f matches against full argument list

    if [ ${#pids[@]} -eq 0 ]; then
        log INFO "No processes found matching pattern: $pattern"
        return
    fi

    for pid in "${pids[@]}"; do
        # Verify the command before killing, especially with broad patterns
        local full_command
        full_command=$(ps -p "$pid" -o cmd= --no-headers || true) # Get command, allow failure if PID vanished
        if [ -z "$full_command" ]; then
            log INFO "Process $pid (matching '$pattern') already gone."
            continue
        fi

        log INFO "Attempting to kill process '$full_command' (PID $pid) matching pattern '$pattern'"
        # Try progressively stronger signals
        if sudo kill -SIGINT "$pid" 2>/dev/null; then
            sleep 1
            if ! ps -p "$pid" > /dev/null; then log INFO "PID $pid killed with SIGINT."; continue; fi
        fi
        if sudo kill -SIGTERM "$pid" 2>/dev/null; then
            sleep 2
            if ! ps -p "$pid" > /dev/null; then log INFO "PID $pid killed with SIGTERM."; continue; fi
        fi
        if sudo kill -SIGKILL "$pid" 2>/dev/null; then
            log INFO "PID $pid killed with SIGKILL."
        else
            log WARN "Failed to kill PID $pid. It might require manual intervention or already be gone."
        fi
    done
}

function configure_services_via_set_values() {
    section_header "Configuring services parameters (set_values.sh)"
    if [ ! -f "$set_values_script_path" ]; then
        log ERROR "set_values.sh script not found at $set_values_script_path. Cannot configure services."
        return 1
    fi

    local set_values_options=()
    # Mandatory for set_values.sh
    set_values_options+=("-d" "$DEVICE")
    set_values_options+=("-m" "$DEPLOY_MODE")

    # Optional ones, pass if set in this script
    [ -n "$REGISTRY" ] && set_values_options+=("-r" "$REGISTRY")
    [ -n "$TAG" ] && set_values_options+=("-t" "$TAG")
    [ -n "$MOUNT_DIR" ] && set_values_options+=("-u" "$MOUNT_DIR")
    [ -n "$EMBED_MODEL" ] && set_values_options+=("-e" "$EMBED_MODEL")
    [ -n "$RERANK_MODEL_ID" ] && set_values_options+=("-a" "$RERANK_MODEL_ID") # -a for rerank in set_values.sh
    [ -n "$LLM_MODEL_ID" ] && set_values_options+=("-l" "$LLM_MODEL_ID")     # -l for llm in set_values.sh
    [ -n "$HUGGINGFACEHUB_API_TOKEN" ] && set_values_options+=("-g" "$HUGGINGFACEHUB_API_TOKEN")
    [ -n "$HTTP_PROXY" ] && set_values_options+=("-p" "$HTTP_PROXY")
    [ -n "$HTTPS_PROXY" ] && set_values_options+=("-s" "$HTTPS_PROXY")   # -s for https in set_values.sh
    [ -n "$NO_PROXY" ] && set_values_options+=("-n" "$NO_PROXY")       # -n for no_proxy additions

    if [ ${#set_values_options[@]} -gt 2 ]; then # At least -d and -m are there
        log INFO "Running: bash $set_values_script_path ${set_values_options[*]}"
        # Use `bash` not `source` if set_values.sh is standalone and doesn't need to modify current shell's env
        if source "$set_values_script_path" "${set_values_options[@]}"; then
            log OK "set_values.sh executed successfully."
        else
            log ERROR "set_values.sh failed. Exiting."
            return 1
        fi
    else
        log INFO "No specific configurations to pass to set_values.sh beyond device and mode."
    fi
}

function start_k8s_deployment() {
    local target_device="$1"
    local k8s_device_manifest_dir="$manifests_path/$target_device/"

    section_header "Starting K8S deployment for DEVICE: $target_device"

    if [ ! -d "$k8s_device_manifest_dir" ]; then
        log ERROR "K8s manifest directory $k8s_device_manifest_dir not found for device $target_device."
        return 1
    fi
    # Check if there are any .yaml or .yml files in the directory
    if ! ls "$k8s_device_manifest_dir"/*.yaml >/dev/null 2>&1 && ! ls "$k8s_device_manifest_dir"/*.yml >/dev/null 2>&1; then
        log ERROR "No YAML manifest files found in $k8s_device_manifest_dir."
        return 1
    fi


    log INFO "Creating namespace $DEPLOYMENT_NS if it doesn't exist (sudo for kubectl may be needed if not configured)."
    if ! kubectl get namespace "$DEPLOYMENT_NS" > /dev/null 2>&1; then
        kubectl create namespace "$DEPLOYMENT_NS" || { log ERROR "Failed to create namespace $DEPLOYMENT_NS."; return 1; }
    fi

    log INFO "Applying manifests from $k8s_device_manifest_dir to namespace $DEPLOYMENT_NS."
    # kubectl apply -f directory/ will apply all .yaml, .yml, .json files
    if kubectl apply -f "$k8s_device_manifest_dir" -n "$DEPLOYMENT_NS"; then
        log OK "Manifests applied successfully."
    else
        log ERROR "Failed to apply manifests from $k8s_device_manifest_dir. Exiting."
        return 1
    fi

    wait_for_pods_ready "$DEPLOYMENT_NS" || return 1 # Exit if pods don't become ready
    log OK "All pods in $DEPLOYMENT_NS are ready."
}

function clear_k8s_deployment() {
    # This function clears a specific deployment namespace, not all.
    # The DEVICE parameter is not strictly needed here if we only use DEPLOYMENT_NS.
    section_header "Clearing K8S deployment in namespace $DEPLOYMENT_NS"
    log INFO "Deleting namespace $DEPLOYMENT_NS..."
    if kubectl get ns "$DEPLOYMENT_NS" > /dev/null 2>&1; then
        if kubectl delete ns "$DEPLOYMENT_NS" --wait=true --timeout=5m; then # Added --wait and timeout
            log OK "Namespace $DEPLOYMENT_NS deleted successfully."
        else
            log WARN "Failed to delete namespace $DEPLOYMENT_NS or deletion timed out. It might be stuck in Terminating state."
            log WARN "You may need to manually clean up resources in $DEPLOYMENT_NS."
        fi
    else
        log INFO "Namespace $DEPLOYMENT_NS does not exist, nothing to clear."
    fi
    log INFO "Attempting to kill any lingering kubectl port-forward processes for $DEPLOYMENT_NS (sudo may be required)..."
    # Be specific with pkill to avoid killing unrelated port-forwards if possible
    kill_processes_by_pattern "kubectl port-forward.*--namespace +$DEPLOYMENT_NS"
}

function start_docker_deployment() {
    local target_device="$1"
    local target_compose_dir="$compose_path/$target_device"

    section_header "Starting Docker Compose deployment for DEVICE: $target_device"

    if [ ! -d "$target_compose_dir" ]; then
        log ERROR "Docker Compose directory $target_compose_dir not found for device $target_device."
        return 1
    fi
    if [ ! -f "$target_compose_dir/compose.yaml" ] && [ ! -f "$target_compose_dir/docker-compose.yaml" ]; then
        log ERROR "No compose.yaml or docker-compose.yaml found in $target_compose_dir."
        return 1
    fi

    log INFO "Changing directory to $target_compose_dir"
    pushd "$target_compose_dir" > /dev/null || { log ERROR "Failed to cd into $target_compose_dir."; return 1; }

    # Source the set_env.sh if it exists, to make sure env vars are set for docker compose
    if [ -f "./set_env.sh" ]; then
        log INFO "Sourcing set_env.sh for Docker environment..."
        source ./set_env.sh
    else
        log WARN "set_env.sh not found in $target_compose_dir. Docker compose will use existing environment or .env file."
    fi

    log INFO "Starting Docker Compose services in detached mode (sudo for docker may be needed)..."
    # Use 'docker compose' (v2 syntax) preferentially
    local compose_cmd="docker compose"

    if $compose_cmd up -d; then
        log OK "Docker Compose services for $target_device started successfully."
    else
        log ERROR "Docker Compose for $target_device failed to start. Check logs above."
        $compose_cmd ps >> "$LOG_FILE" # Log status of containers
        $compose_cmd logs --tail="50" >> "$LOG_FILE" # Log last 50 lines from services
        popd > /dev/null
        return 1
    fi
    popd > /dev/null # Go back to original script dir
    log INFO "Docker deployment started. Services should be running in the background."
}

function clear_docker_deployment() {
    local target_device="$1"
    local target_compose_dir="$compose_path/$target_device"

    section_header "Clearing Docker Compose deployment for DEVICE: $target_device"

    if [ ! -d "$target_compose_dir" ];then
        log INFO "Docker Compose directory $target_compose_dir not found. Assuming already cleared or never deployed."
        return
    fi
     if [ ! -f "$target_compose_dir/compose.yaml" ] && [ ! -f "$target_compose_dir/docker-compose.yaml" ]; then
        log WARN "No compose.yaml or docker-compose.yaml found in $target_compose_dir. Cannot run 'down'."
        return
    fi

    log INFO "Changing directory to $target_compose_dir"
    pushd "$target_compose_dir" > /dev/null || { log ERROR "Failed to cd into $target_compose_dir."; return 1; }

    local compose_cmd="docker compose" # Default to v2

    log INFO "Stopping and removing Docker Compose services (sudo for docker may be needed)..."
    # Add --remove-orphans to remove containers for services not defined in the Compose file
    # Add -v to remove named volumes declared in the `volumes` section of the Compose file
    if $compose_cmd down --remove-orphans -v; then
        log OK "Docker Compose services for $target_device stopped and removed successfully."
    else
        log WARN "Docker Compose down command failed for $target_device. Some resources might remain."
        # Don't exit with error, allow script to continue if part of a larger cleanup
    fi
    popd > /dev/null # Go back
}

function clear_all_k8s_namespaces_dangerously() {
    section_header "DANGER ZONE: Removing ALL ChatQnA related K8s namespaces"
    # Add all relevant namespaces here
    local namespaces_to_clear=("$DEPLOYMENT_NS" "$UI_NS") # Add others as needed

    log WARN "This will attempt to delete the following K8s namespaces: ${namespaces_to_clear[*]}"
    log WARN "This is a destructive operation. Ensure you want to proceed."
    read -p "Type 'YES' to confirm deletion of these namespaces: " confirmation
    if [[ "$confirmation" != "YES" ]]; then
        log INFO "Namespace deletion aborted by user."
        return
    fi

    for ns in "${namespaces_to_clear[@]}"; do
        log INFO "Attempting to delete namespace $ns (sudo for kubectl may be needed)..."
        if kubectl get ns "$ns" > /dev/null 2>&1; then
            if kubectl delete ns "$ns" --wait=true --timeout=5m; then
                log OK "Namespace $ns deleted."
            else
                log WARN "Failed to delete namespace $ns or timed out. It might be stuck in Terminating state."
            fi
        else
            log INFO "Namespace $ns does not exist."
        fi
    done
    log INFO "Attempting to kill ALL lingering kubectl port-forward processes (sudo may be required)..."
    kill_processes_by_pattern "kubectl port-forward" # Kills all kubectl port-forwards, be cautious
}

# --- Argument Parsing ---
action="deploy" # Default action

# Parse arguments
# Using long options for better readability
while [[ "$#" -gt 0 ]]; do
    case $1 in
        --device)
            DEVICE="$2"; shift ;;
        --deploy-mode)
            DEPLOY_MODE="$2"; shift ;;
        --tag)
            TAG="$2"; shift ;;
        --registry)
            REGISTRY="$2"; shift ;;
        --mount-dir)
            MOUNT_DIR="$2"; shift ;;
        --embed-model)
            EMBED_MODEL="$2"; shift ;;
        --rerank-model)
            RERANK_MODEL_ID="$2"; shift ;;
        --llm-model)
            LLM_MODEL_ID="$2"; shift ;;
        --hf-token)
            HUGGINGFACEHUB_API_TOKEN="$2"; shift ;;
        --http-proxy)
            HTTP_PROXY="$2"; shift ;;
        --https-proxy)
            HTTPS_PROXY="$2"; shift ;;
        --no-proxy)
            NO_PROXY="$2"; shift ;;
        --deploy) # Explicit deploy action
            action="deploy" ;;
        --test)
            action="test" ;;
        -cd|--clear-deployment)
            action="clear-deployment" ;;
        -ca|--clear-all)
            action="clear-all" ;;
        -h|--help)
            usage; exit 0 ;;
        *)
            log ERROR "Unknown option or action: $1"
            usage; exit 1 ;;
    esac
    shift
done


# Validate core parameters based on action
if [[ "$action" == "deploy" || "$action" == "clear-deployment" ]]; then
    if [ -z "$DEVICE" ]; then
        log ERROR "--device <DEVICE_NAME> is required for action '$action'."
        usage; exit 1
    fi
    # DEPLOY_MODE has a default, so it's always set. Validate it.
    if [[ "$DEPLOY_MODE" != "k8s" && "$DEPLOY_MODE" != "docker" ]]; then
        log ERROR "Invalid --deploy-mode '$DEPLOY_MODE'. Must be 'k8s' or 'docker'."
        usage; exit 1
    fi
    if [[ "$action" == "deploy" && -z "$HUGGINGFACEHUB_API_TOKEN" ]]; then
        # Warn, but don't exit, if models might be locally cached or don't need HF token
        log WARN "HUGGINGFACEHUB_API_TOKEN (--hf-token) is not set. Deployment might fail if models need to be downloaded."
    fi
fi

if [[ "$action" == "clear-all" && "$DEPLOY_MODE" != "k8s" ]]; then
    log WARN "--clear-all is primarily for K8s. Specified --deploy-mode '$DEPLOY_MODE' will be ignored. Action targets K8s."
fi


# --- Main Action Logic ---
case "$action" in
    deploy)
        log INFO "Selected action: Deploy $DEVICE using $DEPLOY_MODE"
        if ! configure_services_via_set_values; then
            log ERROR "Service configuration failed. Aborting deployment."
            exit 1
        fi

        if [ "$DEPLOY_MODE" = "k8s" ]; then
            start_k8s_deployment "$DEVICE" || exit 1
        elif [ "$DEPLOY_MODE" = "docker" ]; then
            start_docker_deployment "$DEVICE" || exit 1
        fi
        log OK "Deployment of $DEVICE finished."
        log INFO "Waiting a bit for services to fully initialize before testing..."
        progress_bar 180

        log INFO "Proceeding with connection test..."
        if [ -f "$SCRIPT_DIR_INSTALL/test_connection.sh" ]; then
            if ! bash "$SCRIPT_DIR_INSTALL/test_connection.sh" --deploy-mode "$DEPLOY_MODE" --device "$DEVICE"; then
                log ERROR "Connection test FAILED. Check test_connection.sh's logs."
                exit 1
            fi
            log OK "Connection test passed."
        else
            log WARN "test_connection.sh not found. Skipping automatic test."
        fi
        ;;
    clear-deployment)
        log INFO "Selected action: Clear deployment for $DEVICE using $DEPLOY_MODE"
        if [ "$DEPLOY_MODE" = "k8s" ]; then
            clear_k8s_deployment # Uses global $DEPLOYMENT_NS
        elif [ "$DEPLOY_MODE" = "docker" ]; then
            clear_docker_deployment "$DEVICE"
        fi
        log OK "Clearing deployment for $DEVICE finished."
        ;;
    clear-all)
        log INFO "Selected action: Clear all ChatQnA K8s namespaces"
        if [[ "$DEPLOY_MODE" != "k8s" ]]; then
             log WARN "Clear-all is a K8s specific action. It will proceed assuming K8s context."
        fi
        clear_all_k8s_namespaces_dangerously
        log OK "Clearing all K8s namespaces finished."
        ;;
    test)
        section_header "Connection Test"
        if [ -f "$SCRIPT_DIR_INSTALL/test_connection.sh" ]; then
            if ! bash "$SCRIPT_DIR_INSTALL/test_connection.sh" --deploy-mode "$DEPLOY_MODE" --device "$DEVICE"; then
                log ERROR "Connection test FAILED. Check test_connection.sh's logs."
                exit 1
            fi
            log OK "Connection test passed."
        else
            log WARN "test_connection.sh not found. Skipping automatic test."
        fi
        ;;
    *)
        log ERROR "Unknown action '$action'. This should not happen due to argument parsing."
        usage
        exit 1
        ;;
esac

log OK "Script finished successfully for action: $action."
exit 0