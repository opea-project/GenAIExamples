#!/bin/bash
# Copyright (C) 2024 Intel Corporation
# SPDX-License-Identifier: Apache-2.0

# EdgeCraftRAG Bootstrap - Non-interactive Deployment Orchestrator
# This script validates system requirements and delegates to appropriate deployment scripts.
# For interactive mode with prompts, use quick_start.sh instead.

set -euo pipefail

# Script version
BOOTSTRAP_VERSION="1.0"

# Script directory and workspace detection
SCRIPT_DIR=$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)
WORKPATH=$(cd "${SCRIPT_DIR}/.." && pwd)

# Color codes for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
CYAN='\033[0;36m'
NC='\033[0m' # No Color

# Validation flags
SKIP_VALIDATION=${SKIP_VALIDATION:-0}

# Default values
DEFAULT_INFERENCE_BACKEND="openvino"
DEFAULT_DEPLOYMENT_METHOD="baremetal"

#==============================================================================
# Banner and Information Display
#==============================================================================

print_banner() {
    echo ""
    echo "╔═══════════════════════════════════════════════════════════╗"
    echo "║         EdgeCraftRAG Bootstrap v${BOOTSTRAP_VERSION}                       ║"
    echo "║         Deployment Preparation Tool                       ║"
    echo "╚═══════════════════════════════════════════════════════════╝"
    echo ""
}

print_help() {
    cat << EOF
Usage: ${0##*/} [options] [command]

EdgeCraftRAG Bootstrap - Non-interactive deployment orchestrator
This script validates system requirements and delegates to deployment scripts.
For interactive mode, use quick_start.sh instead.

Commands:
  (none)          Run deployment (default)
  cleanup         Stop all services and cleanup

Options:
  --check-only    Validate system requirements only, don't deploy
  --help          Show usage information
  --version       Show script version

Environment Variables (all have defaults):
    INFERENCE_BACKEND    Inference type: openvino|vllm_a770|vllm_b60|ovms (default: openvino)
  DEPLOYMENT_METHOD    Deployment type: baremetal|container (default: baremetal)
  MODEL_PATH           Model storage path (default: workspace/models)
  DOC_PATH             Document storage path (default: workspace)
  HOST_IP              Server IP address (auto-detected if not set)
  LLM_MODEL            LLM model name (default: Qwen/Qwen3-8B)
  SKIP_VALIDATION      Skip system checks: 0|1 (default: 0)

Examples:
  # Default: OpenVINO baremetal deployment
  ./tools/bootstrap.sh

  # vLLM A770 baremetal deployment
  INFERENCE_BACKEND=vllm_a770 ./tools/bootstrap.sh

  # OpenVINO container deployment
  INFERENCE_BACKEND=openvino DEPLOYMENT_METHOD=container ./tools/bootstrap.sh

  # System check only
  ./tools/bootstrap.sh --check-only

  # Stop services
  ./tools/bootstrap.sh cleanup

  # Reuse previous configuration
  source workspace/bootstrap.env
  ./tools/bootstrap.sh

Configuration Persistence:
  After successful deployment, configuration is saved to workspace/bootstrap.env
  Source this file to reuse the same settings in future deployments.

For interactive mode with prompts, use:
  ./tools/quick_start.sh -i

For more information, see: EdgeCraftRAG/tools/README.md

After successful deployment, bootstrap also installs the `ecrag` CLI.
EOF
}

print_info() {
    echo -e "${CYAN}[INFO]${NC} $*"
}

print_success() {
    echo -e "${GREEN}[✓]${NC} $*"
}

print_warning() {
    echo -e "${YELLOW}[!]${NC} $*"
}

print_error() {
    echo -e "${RED}[ERROR]${NC} $*" >&2
}

print_arrow() {
    echo -e "${BLUE}[→]${NC} $*"
}

#==============================================================================
# System Validation Functions
#==============================================================================

check_python_version() {
    if ! command -v python3 &>/dev/null; then
        print_error "Python: python3 not found"
        echo "        → Solution: Install Python 3.10 or later"
        echo "        → Details: Run: sudo apt update && sudo apt install python3"
        return 1
    fi

    local python_version
    python_version=$(python3 -c "import sys; print(f'{sys.version_info.major}.{sys.version_info.minor}')")
    local major minor
    major=$(echo "$python_version" | cut -d. -f1)
    minor=$(echo "$python_version" | cut -d. -f2)

    if [ "$major" -lt 3 ] || { [ "$major" -eq 3 ] && [ "$minor" -lt 10 ]; }; then
        print_error "Python: Version $python_version detected, but 3.10+ required"
        echo "        → Solution: Upgrade Python to 3.10 or later"
        echo "        → Details: Run: sudo apt update && sudo apt install python3.10"
        return 1
    fi

    print_success "Python ${python_version} detected"
    return 0
}

check_docker() {
    local deployment_method="${1:-}"

    # Skip Docker check for baremetal deployment
    if [[ "$deployment_method" == "baremetal" ]]; then
        return 0
    fi

    if ! command -v docker &>/dev/null; then
        print_error "Docker: docker command not found"
        echo "        → Solution: Install Docker"
        echo "        → Details: See https://docs.docker.com/engine/install/"
        return 1
    fi

    if ! docker info &>/dev/null; then
        print_error "Docker: Daemon not running"
        echo "        → Solution: Start Docker service"
        echo "        → Details: Run: sudo systemctl start docker"
        return 1
    fi

    local docker_version
    docker_version=$(docker --version | grep -oP '\d+\.\d+\.\d+' | head -1)
    print_success "Docker ${docker_version} running"
    return 0
}

check_disk_space() {
    local available_gb
    available_gb=$(df -BG "${WORKPATH}" | awk 'NR==2 {print $4}' | sed 's/G//')

    if [ "$available_gb" -lt 50 ]; then
        print_warning "Disk space: Only ${available_gb}GB available, 50GB+ recommended"
        echo "        → Solution: Free up disk space or use custom MODEL_PATH"
        echo "        → Details: Models require ~40GB storage"
        return 0  # Warning, not error
    fi

    print_success "Disk space: ${available_gb}GB available"
    return 0
}

check_groups() {
    local video_gid render_gid

    if getent group video &>/dev/null; then
        video_gid=$(getent group video | cut -d: -f3)
    else
        print_warning "Video group not found (optional for some deployments)"
        video_gid=""
    fi

    if getent group render &>/dev/null; then
        render_gid=$(getent group render | cut -d: -f3)
    else
        print_warning "Render group not found (optional for some deployments)"
        render_gid=""
    fi

    if [[ -n "$video_gid" ]] && [[ -n "$render_gid" ]]; then
        print_success "Video group (gid:${video_gid}) and render group (gid:${render_gid}) found"
        export VIDEOGROUPID="$video_gid"
        export RENDERGROUPID="$render_gid"
    fi

    return 0
}

validate_system_requirements() {
    local deployment_method="${1:-}"

    print_info "Validating system requirements..."

    local all_checks_passed=0

    if ! check_python_version; then
        all_checks_passed=1
    fi

    if ! check_docker "$deployment_method"; then
        all_checks_passed=1
    fi

    check_disk_space  # Always continue, just warn
    check_groups      # Always continue, just warn

    if [ $all_checks_passed -ne 0 ]; then
        print_error "System requirements not met"
        return 1
    fi

    print_success "All system requirements met"
    echo ""
    return 0
}

#==============================================================================
# Environment Setup Functions
#==============================================================================

detect_host_ip() {
    if [[ -z "${HOST_IP:-}" ]]; then
        HOST_IP=$(hostname -I | awk '{print $1}')
        if [[ -z "$HOST_IP" ]]; then
            HOST_IP="127.0.0.1"
            print_warning "Could not detect host IP, using 127.0.0.1"
        fi
    fi
    export HOST_IP
}

set_default_paths() {
    export WORKPATH
    export MODEL_PATH=${MODEL_PATH:-"${WORKPATH}/workspace/models"}
    export DOC_PATH=${DOC_PATH:-"${WORKPATH}/workspace"}
    export TMPFILE_PATH=${TMPFILE_PATH:-"${WORKPATH}/workspace"}
    export LLM_MODEL=${LLM_MODEL:-"Qwen/Qwen3-8B"}
    export MILVUS_ENABLED=${MILVUS_ENABLED:-"1"}
    export CHAT_HISTORY_ROUND=${CHAT_HISTORY_ROUND:-"0"}
}

setup_environment() {
    print_info "Detecting environment..."

    detect_host_ip
    set_default_paths

    print_success "Host IP: ${HOST_IP}"
    print_success "EdgeCraftRAG root: ${WORKPATH}"
    print_success "Model path: ${MODEL_PATH}"
    echo ""

    return 0
}

save_bootstrap_config() {
    local backend="$1"
    local method="$2"
    local config_file="${WORKPATH}/workspace/bootstrap.env"

    # Create workspace directory if it doesn't exist
    mkdir -p "${WORKPATH}/workspace"

    # Save configuration to file
    cat > "${config_file}" << EOF
# EdgeCraftRAG Bootstrap Configuration
# Generated: $(date)
# This file contains the environment variables used for deployment.
# Source this file to reuse the same configuration:
#   source workspace/bootstrap.env
#   ./tools/bootstrap.sh

# Deployment Configuration
export INFERENCE_BACKEND="${backend}"
export DEPLOYMENT_METHOD="${method}"

# Paths
export MODEL_PATH="${MODEL_PATH}"
export DOC_PATH="${DOC_PATH}"
export TMPFILE_PATH="${TMPFILE_PATH}"

# Network
export HOST_IP="${HOST_IP}"

# Model Configuration
export LLM_MODEL="${LLM_MODEL}"
export OV_CONVERSION_METHOD="${OV_CONVERSION_METHOD:-int4}"
export OVMS_SERVICE_PORT="${OVMS_SERVICE_PORT:-8000}"
export OVMS_ENDPOINT="${OVMS_ENDPOINT:-http://${HOST_IP}:${OVMS_SERVICE_PORT:-8000}}"
export OVMS_REST_PORT="${OVMS_REST_PORT:-${OVMS_SERVICE_PORT:-8000}}"
export OVMS_SOURCE_MODEL="${OVMS_SOURCE_MODEL:-${LLM_MODEL}}"
export OVMS_MODEL_REPOSITORY_PATH="${OVMS_MODEL_REPOSITORY_PATH:-/models}"
export OVMS_MODEL_NAME="${OVMS_MODEL_NAME:-${OVMS_SOURCE_MODEL:-${LLM_MODEL}}}"
export OVMS_TARGET_DEVICE="${OVMS_TARGET_DEVICE:-GPU.0}"
export OVMS_TASK="${OVMS_TASK:-text_generation}"
export OVMS_CACHE_DIR="${OVMS_CACHE_DIR:-/models/.ov_cache}"
export OVMS_ENABLE_PREFIX_CACHING="${OVMS_ENABLE_PREFIX_CACHING:-true}"
export OVMS_TOOL_PARSER="${OVMS_TOOL_PARSER:-qwen3coder}"
export OVMS_ENABLE_TOOL_GUIDED_GENERATION="${OVMS_ENABLE_TOOL_GUIDED_GENERATION:-true}"
export OVMS_MAX_NUM_BATCHED_TOKENS="${OVMS_MAX_NUM_BATCHED_TOKENS:-8192}"

# Services
export MILVUS_ENABLED="${MILVUS_ENABLED}"
export CHAT_HISTORY_ROUND="${CHAT_HISTORY_ROUND}"

# Skip validation on reuse (system already validated)
export SKIP_VALIDATION=1
EOF

    chmod 644 "${config_file}"
    print_success "Configuration saved to: workspace/bootstrap.env"
}

install_ecrag_cli() {
    print_info "Installing ecrag CLI..."

    export BOOTSTRAP_ECRAG_COMMAND=""
    export BOOTSTRAP_ECRAG_PATH_HINT=""
    local cli_root="${WORKPATH}/cli"

    if [[ ! -f "${cli_root}/setup.py" ]]; then
        print_error "CLI setup script not found: ${cli_root}/setup.py"
        return 1
    fi

    # Prefer editable install for local development workflows.
    if ! python3 -m pip install -e "${cli_root}" >/dev/null 2>&1; then
        print_warning "Editable install failed, trying PEP668-compatible fallback"
        if ! python3 -m pip install --break-system-packages -e "${cli_root}" >/dev/null 2>&1; then
            print_warning "Fallback editable install failed, trying non-editable install"
            if ! python3 -m pip install "${cli_root}" >/dev/null 2>&1; then
                if ! python3 -m pip install --break-system-packages "${cli_root}" >/dev/null 2>&1; then
                    print_error "Failed to install ecrag CLI"
                    echo "        → Try manually: cd ${cli_root} && python3 -m pip install --break-system-packages -e ."
                    return 1
                fi
            fi
        fi
    fi

    # Refresh command lookup after installation.
    hash -r 2>/dev/null || true

    if command -v ecrag >/dev/null 2>&1; then
        export BOOTSTRAP_ECRAG_COMMAND="ecrag"
        print_success "CLI installed: $(command -v ecrag)"
        return 0
    fi

    if [[ -x "${HOME}/.local/bin/ecrag" ]]; then
        export BOOTSTRAP_ECRAG_COMMAND="${HOME}/.local/bin/ecrag"
        export BOOTSTRAP_ECRAG_PATH_HINT="export PATH=\"${HOME}/.local/bin:\$PATH\""
        print_warning "CLI installed at ${HOME}/.local/bin/ecrag but not in PATH"
        echo "        → Use directly: ${HOME}/.local/bin/ecrag --help"
        echo "        → Add to PATH: ${BOOTSTRAP_ECRAG_PATH_HINT}"
        return 0
    fi

    print_error "CLI installation finished but command not found"
    echo "        → Try manually: cd ${cli_root} && python3 -m pip install --break-system-packages -e ."
    return 1
}

#==============================================================================
# Inference Backend Selection
#==============================================================================

# Removed interactive menu - use environment variables or defaults

normalize_inference_backend() {
    local backend="$1"

    case "$backend" in
        1|openvino|ov|OpenVINO)
            echo "openvino"
            ;;
        2|vllm_a770|vLLM_A770|a770)
            echo "vllm_a770"
            ;;
        3|vllm_b60|vLLM_B60|b60)
            echo "vllm_b60"
            ;;
        4|ovms|OVMS)
            echo "ovms"
            ;;
        *)
            print_error "Invalid inference backend: $backend"
            echo "        → Valid options: openvino, vllm_a770, vllm_b60, ovms"
            return 2
            ;;
    esac
}

get_inference_backend_from_env() {
    # Priority 1: INFERENCE_BACKEND
    if [[ -n "${INFERENCE_BACKEND:-}" ]]; then
        normalize_inference_backend "$INFERENCE_BACKEND"
        return
    fi

    # Priority 2: COMPOSE_PROFILES (backward compatibility)
    if [[ -n "${COMPOSE_PROFILES:-}" ]]; then
        case "$COMPOSE_PROFILES" in
            vLLM_A770|vllm_on_a770|vLLM)
                echo "vllm_a770"
                return
                ;;
            vLLM_B60|vllm_on_b60)
                echo "vllm_b60"
                return
                ;;
            ovms|OVMS)
                echo "ovms"
                return
                ;;
            *)
                echo "openvino"
                return
                ;;
        esac
    fi

    # No env var set
    echo ""
}

select_inference_backend() {
    local backend

    # Get from environment or use default
    backend=$(get_inference_backend_from_env)

    # If not set, use default
    if [[ -z "$backend" ]]; then
        backend="$DEFAULT_INFERENCE_BACKEND"
    fi

    echo "$backend"
}

#==============================================================================
# Deployment Method Selection
#==============================================================================

# Removed interactive menu - use environment variables or defaults

normalize_deployment_method() {
    local method="$1"

    case "$method" in
        1|baremetal|bare_metal|local|Baremetal)
            echo "baremetal"
            ;;
        2|container|docker|Container)
            echo "container"
            ;;
        *)
            print_error "Invalid deployment method: $method"
            echo "        → Valid options: baremetal, container"
            return 2
            ;;
    esac
}

get_deployment_method_from_env() {
    if [[ -n "${DEPLOYMENT_METHOD:-}" ]]; then
        normalize_deployment_method "$DEPLOYMENT_METHOD"
        return
    fi

    # No env var set
    echo ""
}

select_deployment_method() {
    local method

    # Get from environment or use default
    method=$(get_deployment_method_from_env)

    # If not set, use default
    if [[ -z "$method" ]]; then
        method="$DEFAULT_DEPLOYMENT_METHOD"
    fi

    echo "$method"
}

get_backend_display_name() {
    local backend="$1"

    case "$backend" in
        openvino)
            echo "OpenVINO"
            ;;
        vllm_a770)
            echo "vLLM on Arc A770"
            ;;
        vllm_b60)
            echo "vLLM on Arc B60"
            ;;
        ovms)
            echo "OVMS"
            ;;
        *)
            echo "Unknown"
            ;;
    esac
}

get_deployment_display_name() {
    local method="$1"

    case "$method" in
        container)
            echo "Container (Docker)"
            ;;
        baremetal)
            echo "Baremetal"
            ;;
        *)
            echo "Unknown"
            ;;
    esac
}

#==============================================================================
# Deployment Delegation Functions
#==============================================================================

validate_backend_deployment_combo() {
    local backend="$1"
    local method="$2"

    # All combinations are now supported
    # vLLM baremetal = vLLM container + EdgeCraftRAG bare-metal services
    return 0
}

map_deployment_to_script() {
    local backend="$1"
    local method="$2"
    local script=""
    local script_args=""

    # Validate combination first
    if ! validate_backend_deployment_combo "$backend" "$method"; then
        return 2
    fi

    if [[ "$method" == "container" ]]; then
        case "$backend" in
            openvino)
                script="${SCRIPT_DIR}/run_ov_container.sh"
                script_args="start"
                export COMPOSE_PROFILES=""
                ;;
            vllm_a770)
                script="${SCRIPT_DIR}/run_vllm_container.sh"
                script_args="start"
                export VLLM_BACKEND="a770"
                ;;
            vllm_b60)
                script="${SCRIPT_DIR}/run_vllm_container.sh"
                script_args="start"
                export VLLM_BACKEND="b60"
                ;;
            ovms)
                script="${SCRIPT_DIR}/run_ovms_container.sh"
                script_args="start"
                ;;
        esac
    elif [[ "$method" == "baremetal" ]]; then
        case "$backend" in
            openvino)
                script="${SCRIPT_DIR}/run_ov_baremetal.sh"
                script_args="start all"
                ;;
            vllm_a770)
                script="${SCRIPT_DIR}/run_vllm_baremetal.sh"
                script_args="start all"
                export VLLM_BACKEND="a770"
                ;;
            vllm_b60)
                script="${SCRIPT_DIR}/run_vllm_baremetal.sh"
                script_args="start all"
                export VLLM_BACKEND="b60"
                ;;
            ovms)
                script="${SCRIPT_DIR}/run_ovms_baremetal.sh"
                script_args="start all"
                ;;
        esac
    else
        print_error "Unknown deployment method: $method"
        return 2
    fi

    if [ ! -f "$script" ]; then
        print_error "Deployment script not found: $script"
        return 4
    fi

    echo "$script $script_args"
}

print_deployment_summary() {
    local backend="$1"
    local method="$2"
    local backend_name
    local method_name

    backend_name=$(get_backend_display_name "$backend")
    method_name=$(get_deployment_display_name "$method")

    echo ""
    print_info "Inference Backend: ${backend_name}"
    print_info "Deployment Method: ${method_name}"
    print_info "Host IP: ${HOST_IP}"
    print_info "Model Path: ${MODEL_PATH}"
    print_info "LLM Model: ${LLM_MODEL}"
    echo ""
}

delegate_to_deployment_script() {
    local backend="$1"
    local method="$2"
    local script_cmd

    script_cmd=$(map_deployment_to_script "$backend" "$method")
    if [ $? -ne 0 ]; then
        return 4
    fi

    print_deployment_summary "$backend" "$method"

    print_arrow "Delegating to deployment script..."
    echo ""
    echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
    echo ""

    # Execute the deployment script
    if ! bash -c "$script_cmd"; then
        echo ""
        echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
        print_error "Deployment script failed"
        return 4
    fi

    echo ""
    echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"

    return 0
}

print_completion_info() {
    local backend="$1"
    local method="$2"
    local cli_command="${BOOTSTRAP_ECRAG_COMMAND:-ecrag}"

    echo ""
    echo "╔═══════════════════════════════════════════════════════════╗"
    echo "║         Deployment Complete!                              ║"
    echo "╚═══════════════════════════════════════════════════════════╝"
    echo ""

    echo "UI Access: http://${HOST_IP}:8082"
    if [[ "$method" == "baremetal" ]]; then
        echo "API Endpoint: http://${HOST_IP}:16010"
    fi
    echo ""
    echo "Next steps:"
    echo "  • Upload documents via the UI"
    echo "  • Try the chat interface"
    echo "  • Run CLI: ${cli_command} --help"
    if [[ -n "${BOOTSTRAP_ECRAG_PATH_HINT:-}" ]]; then
        echo "  • Add CLI to PATH: ${BOOTSTRAP_ECRAG_PATH_HINT}"
    fi

    # Show appropriate stop/status commands based on backend and method
    case "$backend" in
        openvino)
            case "$method" in
                baremetal)
                    echo "  • Stop services: ./tools/run_ov_baremetal.sh stop"
                    echo "  • View status: ./tools/run_ov_baremetal.sh status"
                    ;;
                container)
                    echo "  • Stop services: ./tools/run_ov_container.sh stop"
                    echo "  • View status: ./tools/run_ov_container.sh status"
                    echo "  • View logs: ./tools/run_ov_container.sh logs [server|mega|ui]"
                    ;;
            esac
            ;;
        vllm_a770|vllm_b60)
            case "$method" in
                baremetal)
                    echo "  • Stop services: ./tools/run_vllm_baremetal.sh stop"
                    echo "  • View status: ./tools/run_vllm_baremetal.sh status"
                    ;;
                container)
                    echo "  • Stop services: ./tools/run_vllm_container.sh stop"
                    echo "  • View status: ./tools/run_vllm_container.sh status"
                    echo "  • View logs: ./tools/run_vllm_container.sh logs [vllm|server|mega|ui]"
                    ;;
            esac
            ;;
        ovms)
            case "$method" in
                baremetal)
                    echo "  • Stop services: ./tools/run_ovms_baremetal.sh stop"
                    echo "  • View status: ./tools/run_ovms_baremetal.sh status"
                    ;;
                container)
                    echo "  • Stop services: ./tools/run_ovms_container.sh stop"
                    echo "  • View status: ./tools/run_ovms_container.sh status"
                    echo "  • View logs: ./tools/run_ovms_container.sh logs [ovms|server|mega|ui]"
                    ;;
            esac
            ;;
    esac

    echo ""
    echo "To reuse this configuration:"
    echo "  source workspace/bootstrap.env"
    echo "  ./tools/bootstrap.sh"
    echo ""
    echo "For troubleshooting: see EdgeCraftRAG/README.md"
    echo ""
}

#==============================================================================
# Cleanup Function
#==============================================================================

handle_cleanup() {
    print_info "Stopping EdgeCraftRAG services..."

    # Try all deployment script cleanups
    if [ -f "${SCRIPT_DIR}/run_ov_container.sh" ]; then
        bash "${SCRIPT_DIR}/run_ov_container.sh" stop 2>/dev/null || true
    fi

    if [ -f "${SCRIPT_DIR}/run_ov_baremetal.sh" ]; then
        bash "${SCRIPT_DIR}/run_ov_baremetal.sh" stop 2>/dev/null || true
    fi

    if [ -f "${SCRIPT_DIR}/run_vllm_container.sh" ]; then
        bash "${SCRIPT_DIR}/run_vllm_container.sh" stop 2>/dev/null || true
    fi

    if [ -f "${SCRIPT_DIR}/run_vllm_baremetal.sh" ]; then
        bash "${SCRIPT_DIR}/run_vllm_baremetal.sh" stop 2>/dev/null || true
    fi

    if [ -f "${SCRIPT_DIR}/run_ovms_container.sh" ]; then
        bash "${SCRIPT_DIR}/run_ovms_container.sh" stop 2>/dev/null || true
    fi

    if [ -f "${SCRIPT_DIR}/run_ovms_baremetal.sh" ]; then
        bash "${SCRIPT_DIR}/run_ovms_baremetal.sh" stop 2>/dev/null || true
    fi

    print_success "Cleanup complete"
    return 0
}

#==============================================================================
# Main Function
#==============================================================================

main() {
    local check_only=0
    local command=""

    # Parse command-line arguments
    while [[ $# -gt 0 ]]; do
        case "$1" in
            --help|-h)
                print_help
                exit 0
                ;;
            --version|-v)
                echo "EdgeCraftRAG Bootstrap v${BOOTSTRAP_VERSION}"
                exit 0
                ;;
            --check-only)
                check_only=1
                shift
                ;;
            cleanup)
                command="cleanup"
                shift
                ;;
            *)
                print_error "Unknown option: $1"
                echo ""
                print_help
                exit 2
                ;;
        esac
    done

    # Handle cleanup command
    if [[ "$command" == "cleanup" ]]; then
        handle_cleanup
        exit $?
    fi

    # Load previous configuration if it exists.
    # Explicitly provided environment variables for the current run must win
    # over values persisted from an earlier deployment.
    local config_file="${WORKPATH}/workspace/bootstrap.env"
    if [[ -f "$config_file" ]]; then
        local saved_inference_backend="${INFERENCE_BACKEND-__BOOTSTRAP_UNSET__}"
        local saved_deployment_method="${DEPLOYMENT_METHOD-__BOOTSTRAP_UNSET__}"
        local saved_model_path="${MODEL_PATH-__BOOTSTRAP_UNSET__}"
        local saved_doc_path="${DOC_PATH-__BOOTSTRAP_UNSET__}"
        local saved_tmpfile_path="${TMPFILE_PATH-__BOOTSTRAP_UNSET__}"
        local saved_host_ip="${HOST_IP-__BOOTSTRAP_UNSET__}"
        local saved_llm_model="${LLM_MODEL-__BOOTSTRAP_UNSET__}"
        local saved_ov_conversion_method="${OV_CONVERSION_METHOD-__BOOTSTRAP_UNSET__}"
        local saved_milvus_enabled="${MILVUS_ENABLED-__BOOTSTRAP_UNSET__}"
        local saved_chat_history_round="${CHAT_HISTORY_ROUND-__BOOTSTRAP_UNSET__}"
        local saved_skip_validation="${SKIP_VALIDATION-__BOOTSTRAP_UNSET__}"

        print_info "Loading saved configuration from workspace/bootstrap.env"
        # Source the file to load environment variables
        # shellcheck disable=SC1090
        source "$config_file"

        if [[ "$saved_inference_backend" != "__BOOTSTRAP_UNSET__" ]]; then
            export INFERENCE_BACKEND="$saved_inference_backend"
        fi
        if [[ "$saved_deployment_method" != "__BOOTSTRAP_UNSET__" ]]; then
            export DEPLOYMENT_METHOD="$saved_deployment_method"
        fi
        if [[ "$saved_model_path" != "__BOOTSTRAP_UNSET__" ]]; then
            export MODEL_PATH="$saved_model_path"
        fi
        if [[ "$saved_doc_path" != "__BOOTSTRAP_UNSET__" ]]; then
            export DOC_PATH="$saved_doc_path"
        fi
        if [[ "$saved_tmpfile_path" != "__BOOTSTRAP_UNSET__" ]]; then
            export TMPFILE_PATH="$saved_tmpfile_path"
        fi
        if [[ "$saved_host_ip" != "__BOOTSTRAP_UNSET__" ]]; then
            export HOST_IP="$saved_host_ip"
        fi
        if [[ "$saved_llm_model" != "__BOOTSTRAP_UNSET__" ]]; then
            export LLM_MODEL="$saved_llm_model"
        fi
        if [[ "$saved_ov_conversion_method" != "__BOOTSTRAP_UNSET__" ]]; then
            export OV_CONVERSION_METHOD="$saved_ov_conversion_method"
        fi
        if [[ "$saved_milvus_enabled" != "__BOOTSTRAP_UNSET__" ]]; then
            export MILVUS_ENABLED="$saved_milvus_enabled"
        fi
        if [[ "$saved_chat_history_round" != "__BOOTSTRAP_UNSET__" ]]; then
            export CHAT_HISTORY_ROUND="$saved_chat_history_round"
        fi
        if [[ "$saved_skip_validation" != "__BOOTSTRAP_UNSET__" ]]; then
            export SKIP_VALIDATION="$saved_skip_validation"
        fi

        print_success "Previous configuration loaded"
        echo ""
    fi

    # Print banner
    print_banner

    # Setup environment first (needed for validation)
    setup_environment

    # Get inference backend
    local inference_backend
    inference_backend=$(select_inference_backend)
    if [ $? -ne 0 ]; then
        exit 2
    fi

    # Get deployment method
    local deployment_method
    deployment_method=$(select_deployment_method)
    if [ $? -ne 0 ]; then
        exit 2
    fi

    # Validate system requirements unless skipped
    if [ "$SKIP_VALIDATION" -ne 1 ]; then
        if ! validate_system_requirements "$deployment_method"; then
            exit 1
        fi
    fi

    # If check-only, exit here
    if [ $check_only -eq 1 ]; then
        print_info "System check complete - ready for deployment"
        exit 0
    fi

    # Store normalized values for later use
    export BOOTSTRAP_INFERENCE_BACKEND="$inference_backend"
    export BOOTSTRAP_DEPLOYMENT_METHOD="$deployment_method"

    # Delegate to deployment script
    if ! delegate_to_deployment_script "$inference_backend" "$deployment_method"; then
        exit 4
    fi

    # Save configuration for reuse
    save_bootstrap_config "$inference_backend" "$deployment_method"

    # Install CLI so users can access ecrag directly after bootstrap
    if ! install_ecrag_cli; then
        exit 5
    fi

    # Print completion information
    print_completion_info "$inference_backend" "$deployment_method"

    exit 0
}

# Execute main function
main "$@"
