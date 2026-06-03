#!/bin/bash
# Copyright (C) 2024 Intel Corporation
# SPDX-License-Identifier: Apache-2.0

# EdgeCraftRAG Quick Start
# One-command deployment with automatic model download and setup

set -e

SCRIPT_DIR=$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)
WORKPATH=$(cd "${SCRIPT_DIR}/.." && pwd)

# Default values
ip_address=$(hostname -I | awk '{print $1}')
export HOST_IP=${HOST_IP:-"${ip_address}"}
export MODEL_PATH=${MODEL_PATH:-"${WORKPATH}/workspace/models"}
export LLM_MODEL=${LLM_MODEL:-"Qwen/Qwen3-8B"}
export EMBEDDING_MODEL=${EMBEDDING_MODEL:-"BAAI/bge-small-en-v1.5"}
export RERANKER_MODEL=${RERANKER_MODEL:-"BAAI/bge-reranker-large"}
export MODEL_DOWNLOAD_SOURCE=${MODEL_DOWNLOAD_SOURCE:-"modelscope"}
export OV_CONVERSION_METHOD=${OV_CONVERSION_METHOD:-"int4"}
export DOC_PATH=${DOC_PATH:-"${WORKPATH}/workspace"}
export TMPFILE_PATH=${TMPFILE_PATH:-"${WORKPATH}/workspace"}
export MILVUS_ENABLED=${MILVUS_ENABLED:-"1"}
export CHAT_HISTORY_ROUND=${CHAT_HISTORY_ROUND:-"0"}
export SKIP_MODEL_CHECK=${SKIP_MODEL_CHECK:-"0"}
export SKIP_INTEL_GPU_DRIVER_CHECK=${SKIP_INTEL_GPU_DRIVER_CHECK:-"0"}
export AUTO_INSTALL_INTEL_GPU_DRIVER=${AUTO_INSTALL_INTEL_GPU_DRIVER:-"1"}
export AUTO_INSTALL_NPM=${AUTO_INSTALL_NPM:-"1"}
export RESTART_ON_RERUN=${RESTART_ON_RERUN:-"0"}

# Explicitly propagate proxy variables to all child scripts/processes.
export http_proxy=${http_proxy:-${HTTP_PROXY:-}}
export https_proxy=${https_proxy:-${HTTPS_PROXY:-}}
export no_proxy=${no_proxy:-${NO_PROXY:-}}
export HTTP_PROXY=${HTTP_PROXY:-${http_proxy:-}}
export HTTPS_PROXY=${HTTPS_PROXY:-${https_proxy:-}}
export NO_PROXY=${NO_PROXY:-${no_proxy:-}}

# vLLM runtime options
export MAX_MODEL_LEN=${MAX_MODEL_LEN:-"8192"}
export GPU_MEMORY_UTIL=${GPU_MEMORY_UTIL:-"0.8"}
export QUANTIZATION=${QUANTIZATION:-"fp8"}
export TOOL_PARSER=${TOOL_PARSER:-"qwen3_coder"}

if [[ "${MODEL_DOWNLOAD_SOURCE,,}" == "huggingface" ]]; then
    export HF_ENDPOINT=${HF_ENDPOINT:-"https://hf-mirror.com"}
fi

#==============================================================================
# Python Virtual Environment Setup
#==============================================================================

ENV_NAME="${WORKPATH}/ecrag_venv"

setup_python_venv() {
    # Prefer Python 3.10 or 3.11 for best compatibility
    local PYTHON_CMD="python3"
    if command -v python3.11 &>/dev/null; then
        PYTHON_CMD="python3.11"
        echo "Using Python 3.11 (recommended)"
    elif command -v python3.10 &>/dev/null; then
        PYTHON_CMD="python3.10"
        echo "Using Python 3.10 (recommended)"
    else
        echo "Using $(python3 --version 2>&1)"
        echo "⚠ Note: Python 3.10 or 3.11 recommended for best compatibility"
    fi

    # Check if python3-venv (ensurepip) is fully available; install if missing
    if ! $PYTHON_CMD -c "import ensurepip" &>/dev/null; then
        echo "python3-venv (ensurepip) not found, installing..."
        PY_VER=$($PYTHON_CMD -c "import sys; print(f'{sys.version_info.major}.{sys.version_info.minor}')")
        if command -v apt-get &>/dev/null; then
            sudo apt-get install -y "python${PY_VER}-venv"
        elif command -v dnf &>/dev/null; then
            sudo dnf install -y python3-virtualenv
        elif command -v yum &>/dev/null; then
            sudo yum install -y python3-virtualenv
        else
            echo "ERROR: Cannot install python3-venv: unsupported package manager. Please install it manually."
            exit 1
        fi
    fi

    # Create venv if missing or broken (activate script absent)
    if [ ! -f "${ENV_NAME}/bin/activate" ] && [ ! -f "${ENV_NAME}/Scripts/activate" ]; then
        echo "Creating virtual environment at ${ENV_NAME}..."
        rm -rf "${ENV_NAME}"
        $PYTHON_CMD -m venv "${ENV_NAME}"
    fi

    # Activate venv
    if [ -f "${ENV_NAME}/bin/activate" ]; then
        source "${ENV_NAME}/bin/activate"
    elif [ -f "${ENV_NAME}/Scripts/activate" ]; then
        source "${ENV_NAME}/Scripts/activate"
    else
        echo "ERROR: Failed to activate virtual environment at ${ENV_NAME}"
        exit 1
    fi

    echo "Python virtual environment activated: ${ENV_NAME}"
}

verify_venv_activated() {
    echo ""
    echo "[Venv Check] Verifying virtual environment..."

    # Check if VIRTUAL_ENV is set
    if [[ -z "${VIRTUAL_ENV:-}" ]]; then
        echo "[Venv Check] ERROR: Virtual environment not activated"
        echo "             VIRTUAL_ENV variable is not set"
        exit 1
    fi

    # Check if we're using the expected venv
    if [[ "${VIRTUAL_ENV}" != "${ENV_NAME}" ]]; then
        echo "[Venv Check] WARNING: Using different venv than expected"
        echo "             Expected: ${ENV_NAME}"
        echo "             Active:   ${VIRTUAL_ENV}"
    else
        echo "[Venv Check] ✓ Virtual environment properly activated: ${VIRTUAL_ENV}"
    fi

    # Check Python version
    python_version=$(python --version 2>&1 | awk '{print $2}')
    python_major=$(echo "$python_version" | cut -d. -f1)
    python_minor=$(echo "$python_version" | cut -d. -f2)

    if [[ "$python_major" -lt 3 ]] || [[ "$python_major" -eq 3 && "$python_minor" -lt 10 ]]; then
        echo "[Venv Check] ERROR: Python 3.10+ required, but found $python_version"
        exit 1
    fi

    echo "[Venv Check] ✓ Python version: $python_version"

    # Python 3.12+ is supported with a docarray compatibility pin during pip install.
    # Keep this as an explicit warning so users understand why extra handling is applied.
    if [[ "$python_major" -eq 3 && "$python_minor" -ge 12 ]]; then
        echo ""
        echo "[Venv Check] ⚠ Python 3.12+ detected"
        echo "             Applying docarray compatibility pin during dependency installation"
        echo "             (recommended fallback: Python 3.10 or 3.11)"
        echo ""
    fi
}

check_pip_requirements() {
    local requirements_file="${WORKPATH}/edgecraftrag/requirements.txt"
    local python_version
    python_version=$(python --version 2>&1 | awk '{print $2}')
    local python_major python_minor
    python_major=$(echo "$python_version" | cut -d. -f1)
    python_minor=$(echo "$python_version" | cut -d. -f2)

    echo ""
    echo "[Pip Check] Checking Python package requirements..."

    # Check if requirements.txt exists
    if [[ ! -f "$requirements_file" ]]; then
        echo "[Pip Check] WARNING: requirements.txt not found at $requirements_file"
        echo "            Skipping package check"
        return 0
    fi

    # Check if timeout command is available
    local HAS_TIMEOUT=1
    if ! command -v timeout &>/dev/null; then
        echo "[Pip Check] Note: 'timeout' command not found, checks may take longer"
        HAS_TIMEOUT=0
    fi

    # Upgrade pip if needed
    echo "[Pip Check] Ensuring pip is up to date..."
    python -m pip install --quiet --upgrade pip

    # Ensure docarray compatibility for Python 3.12+.
    # Some transitive dependency chains may otherwise resolve an incompatible version.
    if [[ "$python_major" -eq 3 && "$python_minor" -ge 12 ]]; then
        echo "[Pip Check] Python 3.12+ detected, pinning docarray==0.40.0..."
        if ! python -m pip install --quiet "docarray==0.40.0"; then
            echo "[Pip Check] ERROR: Failed to install docarray==0.40.0 for Python 3.12+"
            exit 1
        fi
    fi

    # Check for critical packages
    local critical_packages=(
        "langchain-core"
        "llama-index"
        "opea-comps"
        "transformers"
    )

    local missing_packages=()
    local installed_count=0

    for package in "${critical_packages[@]}"; do
        echo -n "[Pip Check] Checking $package... "
        local check_start=$SECONDS

        # Skip import check, just verify package is installed via pip
        # Import checks can hang on some packages like llama-index
        # Use timeout to prevent pip show from hanging
        local show_result=1
        if [[ $HAS_TIMEOUT -eq 1 ]]; then
            if timeout 5 python -m pip show "${package}" >/dev/null 2>&1; then
                show_result=0
            else
                show_result=$?
            fi
        else
            if python -m pip show "${package}" >/dev/null 2>&1; then
                show_result=0
            else
                show_result=$?
            fi
        fi

        if [[ $show_result -eq 0 ]]; then
            local check_elapsed=$((SECONDS - check_start))
            echo "✓ (${check_elapsed}s)"
            installed_count=$((installed_count + 1))
        elif [[ $show_result -eq 124 ]]; then
            local check_elapsed=$((SECONDS - check_start))
            echo "⏱ (${check_elapsed}s, timeout - treating as missing)"
            missing_packages+=("$package")
        else
            local check_elapsed=$((SECONDS - check_start))
            echo "✗ (${check_elapsed}s, missing)"
            missing_packages+=("$package")
        fi
    done

    echo "[Pip Check] Package check loop completed: $installed_count installed, ${#missing_packages[@]} missing"

    if [[ ${#missing_packages[@]} -gt 0 ]]; then
        echo ""
        echo "[Pip Check] Missing ${#missing_packages[@]} critical packages"
        echo "[Pip Check] Missing package list: ${missing_packages[*]}"
        echo "[Pip Check] Installing requirements from $requirements_file..."
        echo ""

        # Install all requirements with PyTorch CPU index
        # Note: requirements.txt contains torch==2.8.0+cpu which needs PyTorch's extra index
        if python -m pip install -r "$requirements_file" \
            --extra-index-url https://download.pytorch.org/whl/cpu; then
            echo ""
            echo "[Pip Check] ✓ All requirements installed successfully"
        else
            echo ""
            echo "[Pip Check] ERROR: Failed to install requirements"
            echo "[Pip Check] You can manually install with:"
            echo "            python -m pip install -r $requirements_file \\"
            echo "              --extra-index-url https://download.pytorch.org/whl/cpu"
            exit 1
        fi
    else
        echo "[Pip Check] ✓ All critical packages are installed ($installed_count/${#critical_packages[@]})"

        # Skip pip check to avoid potential hangs - critical packages are installed
        echo "[Pip Check] Skipping full dependency check (critical packages verified)"
    fi

    echo "[Pip Check] Completed successfully"
}

check_npm_requirements() {
    echo ""
    echo "[NPM Check] Checking Node.js/npm for baremetal UI startup..."

    if command -v npm &>/dev/null; then
        local npm_version
        npm_version=$(npm --version 2>/dev/null || echo "unknown")
        echo "[NPM Check] ✓ npm is available: ${npm_version}"
        return 0
    fi

    echo "[NPM Check] npm not found"

    if [[ "${AUTO_INSTALL_NPM}" != "1" ]]; then
        echo "[NPM Check] ERROR: Auto-install disabled (AUTO_INSTALL_NPM=${AUTO_INSTALL_NPM})"
        echo "[NPM Check] Please install Node.js/npm manually, or set AUTO_INSTALL_NPM=1"
        exit 1
    fi

    echo "[NPM Check] Attempting to install npm..."
    if command -v apt-get &>/dev/null; then
        sudo apt-get update
        sudo apt-get install -y npm
    elif command -v dnf &>/dev/null; then
        sudo dnf install -y npm
    elif command -v yum &>/dev/null; then
        sudo yum install -y npm
    else
        echo "[NPM Check] ERROR: Unsupported package manager. Please install npm manually."
        exit 1
    fi

    if command -v npm &>/dev/null; then
        local installed_npm_version
        installed_npm_version=$(npm --version 2>/dev/null || echo "unknown")
        echo "[NPM Check] ✓ npm installed successfully: ${installed_npm_version}"
    else
        echo "[NPM Check] ERROR: npm installation completed but npm is still unavailable"
        exit 1
    fi
}

#==============================================================================
# Intel GPU Driver Validation and Installation
#==============================================================================

has_intel_gpu_device() {
    if ! command -v lspci &>/dev/null; then
        # lspci may be unavailable on minimal systems; fall back to /dev/dri presence.
        [[ -e /dev/dri/card0 || -e /dev/dri/renderD128 ]]
        return $?
    fi

    if lspci | grep -Ei 'VGA|3D|Display' | grep -qi 'intel'; then
        return 0
    fi

    return 1
}

is_intel_gpu_driver_ready() {
    if ! command -v clinfo &>/dev/null; then
        echo "[GPU Driver Check] clinfo not found"
        return 1
    fi

    if clinfo 2>/dev/null | grep -q "Device Name"; then
        return 0
    fi

    echo "[GPU Driver Check] clinfo did not report any Device Name entries"
    return 1
}

install_intel_gpu_driver_ubuntu() {
    local version_codename
    local apt_update_log
    local missing_key
    local candidate_packages
    local level_zero_runtime_pkg=""
    local level_zero_loader_pkg=""
    local available_packages=()
    version_codename=$(source /etc/os-release && echo "${VERSION_CODENAME:-}")

    if [[ -z "${version_codename}" ]]; then
        echo "[GPU Driver Check] ERROR: Unable to detect Ubuntu codename"
        return 1
    fi

    echo "[GPU Driver Check] Installing Intel GPU runtime packages for Ubuntu ${version_codename}..."

    sudo apt-get update
    sudo apt-get install -y ca-certificates curl gpg

    # Always refresh Intel repo key to handle key rotation on existing machines.
    curl -fsSL https://repositories.intel.com/gpu/intel-graphics.key | \
        sudo gpg --dearmor --yes -o /usr/share/keyrings/intel-graphics.gpg
    sudo chmod a+r /usr/share/keyrings/intel-graphics.gpg

    echo "deb [signed-by=/usr/share/keyrings/intel-graphics.gpg arch=amd64] https://repositories.intel.com/gpu/ubuntu ${version_codename} unified" | \
        sudo tee /etc/apt/sources.list.d/intel-gpu.list >/dev/null

    apt_update_log=$(mktemp)
    if ! sudo apt-get update 2>&1 | tee "${apt_update_log}"; then
        missing_key=$(grep -oE 'NO_PUBKEY [0-9A-F]+' "${apt_update_log}" | awk '{print $2}' | head -n1)
        if [[ -n "${missing_key}" ]]; then
            echo "[GPU Driver Check] Importing missing apt key: ${missing_key}"
            if sudo gpg --batch --keyserver hkps://keyserver.ubuntu.com --recv-keys "${missing_key}" && \
               sudo gpg --batch --export "${missing_key}" | sudo gpg --dearmor --yes -o /usr/share/keyrings/intel-graphics.gpg; then
                sudo chmod a+r /usr/share/keyrings/intel-graphics.gpg
                sudo apt-get update
            else
                rm -f "${apt_update_log}"
                echo "[GPU Driver Check] ERROR: Failed to import missing key ${missing_key}"
                return 1
            fi
        else
            rm -f "${apt_update_log}"
            echo "[GPU Driver Check] ERROR: apt-get update failed for Intel GPU repository"
            return 1
        fi
    fi
    rm -f "${apt_update_log}"

    # Prefer newer package names first to avoid conflicts on newer Ubuntu releases
    # where libze-intel-gpu1 may break intel-level-zero-gpu.
    if apt-cache show libze-intel-gpu1 >/dev/null 2>&1; then
        level_zero_runtime_pkg="libze-intel-gpu1"
    elif apt-cache show intel-level-zero-gpu >/dev/null 2>&1; then
        level_zero_runtime_pkg="intel-level-zero-gpu"
    fi

    if apt-cache show libze1 >/dev/null 2>&1; then
        level_zero_loader_pkg="libze1"
    elif apt-cache show level-zero >/dev/null 2>&1; then
        level_zero_loader_pkg="level-zero"
    fi

    candidate_packages=(intel-opencl-icd xpu-smi clinfo)
    if [[ -n "${level_zero_runtime_pkg}" ]]; then
        candidate_packages+=("${level_zero_runtime_pkg}")
    fi
    if [[ -n "${level_zero_loader_pkg}" ]]; then
        candidate_packages+=("${level_zero_loader_pkg}")
    fi
    for pkg in "${candidate_packages[@]}"; do
        if apt-cache show "${pkg}" >/dev/null 2>&1; then
            available_packages+=("${pkg}")
        else
            echo "[GPU Driver Check] WARNING: Package not found in current repos: ${pkg}"
        fi
    done

    if [[ ${#available_packages[@]} -eq 0 ]]; then
        echo "[GPU Driver Check] ERROR: No Intel GPU runtime packages available to install"
        return 1
    fi

    if ! sudo apt-get install -y "${available_packages[@]}"; then
        echo "[GPU Driver Check] ERROR: Failed to install Intel GPU runtime packages: ${available_packages[*]}"
        return 1
    fi
}

install_intel_gpu_driver() {
    if command -v apt-get &>/dev/null; then
        install_intel_gpu_driver_ubuntu
        return $?
    fi

    echo "[GPU Driver Check] ERROR: Automatic Intel GPU driver installation is only supported on apt-based Linux in quick_start.sh"
    echo "[GPU Driver Check] Please install Intel GPU drivers manually for your distribution"
    return 1
}

ensure_intel_gpu_driver_ready() {
    if [[ "${SKIP_INTEL_GPU_DRIVER_CHECK}" == "1" ]]; then
        echo "[GPU Driver Check] Skipping Intel GPU driver validation (--skip-gpu-driver-check enabled)"
        return 0
    fi

    if ! has_intel_gpu_device; then
        echo "[GPU Driver Check] No Intel GPU device detected, skipping Intel GPU driver installation"
        return 0
    fi

    echo ""
    echo "[GPU Driver Check] Validating Intel GPU driver/runtime..."

    if is_intel_gpu_driver_ready; then
        echo "[GPU Driver Check] ✓ Intel GPU driver/runtime looks ready"
        return 0
    fi

    echo "[GPU Driver Check] Intel GPU driver/runtime not ready"

    if [[ "${AUTO_INSTALL_INTEL_GPU_DRIVER}" != "1" ]]; then
        echo "[GPU Driver Check] ERROR: Auto-install disabled (AUTO_INSTALL_INTEL_GPU_DRIVER=${AUTO_INSTALL_INTEL_GPU_DRIVER})"
        echo "[GPU Driver Check] Set AUTO_INSTALL_INTEL_GPU_DRIVER=1 or use --skip-gpu-driver-check"
        exit 1
    fi

    echo "[GPU Driver Check] Attempting automatic installation..."
    if ! install_intel_gpu_driver; then
        echo "[GPU Driver Check] ERROR: Intel GPU driver installation failed"
        echo "[GPU Driver Check] Refer to: https://dgpu-docs.intel.com/driver/client/overview.html"
        exit 1
    fi

    if is_intel_gpu_driver_ready; then
        echo "[GPU Driver Check] ✓ Intel GPU driver/runtime installed successfully"
    else
        echo "[GPU Driver Check] ERROR: Driver installation finished but GPU runtime is still unavailable"
        echo "[GPU Driver Check] Try rebooting the machine and rerun quick_start.sh"
        exit 1
    fi
}

#==============================================================================
# Model Download Functions (Unique Value of quick_start.sh)
#==============================================================================

run_model_download_tool() {
    local mode="$1"
    local tool_script="${SCRIPT_DIR}/model_download.sh"

    if [[ ! -f "${tool_script}" ]]; then
        echo "[Model Check] ERROR: Model download tool not found: ${tool_script}"
        exit 1
    fi

    bash "${tool_script}" "${mode}"
}

ensure_required_models_for_vllm() {
    run_model_download_tool "vllm"
}

ensure_required_models_for_ov() {
    run_model_download_tool "ov"
}

resolve_download_mode_for_backend() {
    local backend="$1"
    local llm_model="$2"

    case "$backend" in
        openvino|ovms)
            if [[ "$llm_model" == OpenVINO/*-ov ]]; then
                echo "vllm"
            else
                echo "ov"
            fi
            ;;
        vllm_a770|vllm_b60)
            echo "vllm"
            ;;
        *)
            echo "ov"
            ;;
    esac
}

download_required_models_for_backend() {
    local backend="$1"
    local llm_model="$2"
    local download_mode

    download_mode=$(resolve_download_mode_for_backend "$backend" "$llm_model")
    echo "[Model Check] Resolved download mode for backend '${backend}': ${download_mode}"
    run_model_download_tool "${download_mode}"
}

#==============================================================================
# Interactive Helper Functions
#==============================================================================

get_user_input() {
    local var_name=$1
    local default_value=$2
    read -p "To set ${var_name} as [${default_value}], press Enter to confirm, or type a new value: " user_input
    echo ${user_input:-$default_value}
}

get_enable_function() {
    local var_name=$1
    local default_value=$2
    read -p "Do you want to enable ${var_name} [${default_value}]: " user_input
    echo ${user_input:-$default_value}
}

print_ui_access_info() {
    echo ""
    echo "════════════════════════════════════════════════════════════"
    echo "Service launched successfully!"
    echo "════════════════════════════════════════════════════════════"
    echo ""
    echo "UI access URL: http://${HOST_IP}:8082"
    echo ""
    echo "If you are accessing from another machine, replace ${HOST_IP}"
    echo "with the server's reachable IP or hostname."
    echo ""
}

restart_services_before_deploy() {
    if [[ "${RESTART_ON_RERUN}" != "1" ]]; then
        return 0
    fi

    echo ""
    echo "Restart-on-rerun enabled: stopping existing services before deployment..."
    # Best effort cleanup to guarantee a clean restart path.
    bash "${SCRIPT_DIR}/bootstrap.sh" cleanup || true
}

resolve_runtime_script() {
    local backend="$1"
    local deployment_method="$2"

    if [[ "$backend" == "openvino" ]]; then
        if [[ "$deployment_method" == "container" ]]; then
            echo "${SCRIPT_DIR}/run_ov_container.sh"
        else
            echo "${SCRIPT_DIR}/run_ov_baremetal.sh"
        fi
    elif [[ "$backend" == "ovms" ]]; then
        if [[ "$deployment_method" == "container" ]]; then
            echo "${SCRIPT_DIR}/run_ovms_container.sh"
        else
            echo "${SCRIPT_DIR}/run_ovms_baremetal.sh"
        fi
    else
        if [[ "$deployment_method" == "container" ]]; then
            echo "${SCRIPT_DIR}/run_vllm_container.sh"
        else
            echo "${SCRIPT_DIR}/run_vllm_baremetal.sh"
        fi
    fi
}

are_target_services_running() {
    local backend="$1"
    local deployment_method="$2"
    local runtime_script
    local status_output

    runtime_script=$(resolve_runtime_script "$backend" "$deployment_method")
    if [[ ! -f "$runtime_script" ]]; then
        return 1
    fi

    status_output=$(bash "$runtime_script" status 2>/dev/null || true)

    if echo "$status_output" | grep -Eqi "stopped|not running"; then
        return 1
    fi

    if echo "$status_output" | grep -Eqi "running"; then
        return 0
    fi

    return 1
}

check_docker_and_compose_ready() {
    echo ""
    echo "[Docker Check] Validating Docker and Docker Compose..."

    if ! command -v docker &>/dev/null || ! docker compose version >/dev/null 2>&1; then
        echo "[Docker Check] Docker and/or Docker Compose not found. Installing on Ubuntu 24.04..."

        if ! command -v apt-get &>/dev/null; then
            echo "[Docker Check] ERROR: apt-get not found. Automatic installation only supports Ubuntu 24.04"
            exit 1
        fi

        sudo apt-get update

        # Ubuntu 24.04 package names can differ across mirrors/releases.
        # Try the common variants for Compose plugin.
        if ! sudo apt-get install -y docker.io docker-compose-v2; then
            if ! sudo apt-get install -y docker.io docker-compose-plugin; then
                echo "[Docker Check] ERROR: Failed to install docker.io and Docker Compose plugin"
                exit 1
            fi
        fi
    fi

    if ! systemctl is-active --quiet docker; then
        echo "[Docker Check] Starting Docker daemon..."
        sudo systemctl enable --now docker
        sudo systemctl start docker || true
    fi

    local docker_ready=0
    local daemon_running=0

    # Give systemd a short window to finish service activation.
    for _ in {1..8}; do
        if systemctl is-active --quiet docker; then
            daemon_running=1
            break
        fi
        sleep 1
    done

    if docker info >/dev/null 2>&1; then
        docker_ready=1
    elif sudo docker info >/dev/null 2>&1; then
        echo "[Docker Check] ERROR: Docker daemon is running but current user cannot access Docker socket"
        echo "[Docker Check] Run: sudo usermod -aG docker ${USER}"
        echo "[Docker Check] Then re-login (or run: newgrp docker) and rerun quick_start.sh"
        exit 1
    fi

    if [[ "${docker_ready}" -ne 1 ]]; then
        if [[ "${daemon_running}" -ne 1 ]]; then
            echo "[Docker Check] ERROR: Docker daemon failed to start after installation"
        else
            echo "[Docker Check] ERROR: Docker daemon is not available after installation/start attempt"
        fi
        echo "[Docker Check] Recent docker service logs (last 20 lines):"
        sudo journalctl -u docker --no-pager -n 20 || true
        exit 1
    fi

    if ! docker compose version >/dev/null 2>&1; then
        echo "[Docker Check] ERROR: Docker Compose plugin is still unavailable after installation"
        exit 1
    fi

    echo "[Docker Check] ✓ Docker and Docker Compose are ready"
}

save_bootstrap_env_snapshot() {
    local backend="$1"
    local deployment_method="$2"
    local config_file="${WORKPATH}/workspace/bootstrap.env"

    mkdir -p "${WORKPATH}/workspace"

    {
        echo "# EdgeCraftRAG deployment environment snapshot"
        echo "# Generated by quick_start.sh on $(date)"
        echo "# Reuse with: source workspace/bootstrap.env && ./tools/bootstrap.sh"
        echo ""

        printf 'export INFERENCE_BACKEND=%q\n' "${backend}"
        printf 'export DEPLOYMENT_METHOD=%q\n' "${deployment_method}"

        local env_vars=(
            HOST_IP
            MODEL_PATH
            DOC_PATH
            TMPFILE_PATH
            LLM_MODEL
            OVMS_SERVICE_PORT
            OVMS_ENDPOINT
            EMBEDDING_MODEL
            RERANKER_MODEL
            MODEL_DOWNLOAD_SOURCE
            OV_CONVERSION_METHOD
            HF_ENDPOINT
            MILVUS_ENABLED
            CHAT_HISTORY_ROUND
            SKIP_MODEL_CHECK
            SKIP_INTEL_GPU_DRIVER_CHECK
            AUTO_INSTALL_INTEL_GPU_DRIVER
            AUTO_INSTALL_NPM
            RESTART_ON_RERUN
            http_proxy
            https_proxy
            no_proxy
            HTTP_PROXY
            HTTPS_PROXY
            NO_PROXY
            VLLM_BACKEND
            TP
            DP
            DTYPE
            MAX_MODEL_LEN
            GPU_MEMORY_UTIL
            QUANTIZATION
            TOOL_PARSER
            ZE_AFFINITY_MASK
            CCL_DG2_USM
            OVMS_REST_PORT
            OVMS_SOURCE_MODEL
            OVMS_MODEL_REPOSITORY_PATH
            OVMS_MODEL_NAME
            OVMS_TARGET_DEVICE
            OVMS_TASK
            OVMS_CACHE_DIR
            OVMS_ENABLE_PREFIX_CACHING
            OVMS_TOOL_PARSER
            OVMS_ENABLE_TOOL_GUIDED_GENERATION
            OVMS_MAX_NUM_BATCHED_TOKENS
        )

        local var_name
        for var_name in "${env_vars[@]}"; do
            if [[ -n "${!var_name+x}" ]]; then
                printf 'export %s=%q\n' "${var_name}" "${!var_name}"
            fi
        done

        # Keep bootstrap checks skipped on replay, matching quick_start behavior.
        echo "export SKIP_VALIDATION=1"
    } > "${config_file}"

    chmod 644 "${config_file}"
    echo "[Config] Saved deployment environment to workspace/bootstrap.env"
}

set_ovms_defaults() {
    export OVMS_SERVICE_PORT=${OVMS_SERVICE_PORT:-8000}
    export OVMS_ENDPOINT=${OVMS_ENDPOINT:-"http://${HOST_IP}:${OVMS_SERVICE_PORT}"}
    export OVMS_REST_PORT=${OVMS_REST_PORT:-${OVMS_SERVICE_PORT}}
    export OVMS_SOURCE_MODEL=${OVMS_SOURCE_MODEL:-${LLM_MODEL}}
    export OVMS_MODEL_REPOSITORY_PATH=${OVMS_MODEL_REPOSITORY_PATH:-/models}
    export OVMS_MODEL_NAME=${OVMS_MODEL_NAME:-${OVMS_SOURCE_MODEL}}
    export OVMS_TARGET_DEVICE=${OVMS_TARGET_DEVICE:-GPU.0}
    export OVMS_TASK=${OVMS_TASK:-text_generation}
    export OVMS_CACHE_DIR=${OVMS_CACHE_DIR:-/models/.ov_cache}
    export OVMS_ENABLE_PREFIX_CACHING=${OVMS_ENABLE_PREFIX_CACHING:-true}
    export OVMS_TOOL_PARSER=${OVMS_TOOL_PARSER:-qwen3coder}
    export OVMS_ENABLE_TOOL_GUIDED_GENERATION=${OVMS_ENABLE_TOOL_GUIDED_GENERATION:-true}
    export OVMS_MAX_NUM_BATCHED_TOKENS=${OVMS_MAX_NUM_BATCHED_TOKENS:-8192}
}

set_vllm_defaults() {
    export MAX_MODEL_LEN=${MAX_MODEL_LEN:-8192}
    export GPU_MEMORY_UTIL=${GPU_MEMORY_UTIL:-0.8}
    export QUANTIZATION=${QUANTIZATION:-fp8}
    export TOOL_PARSER=${TOOL_PARSER:-qwen3_coder}
}

#==============================================================================
# Deployment Functions (Delegate to bootstrap.sh)
#==============================================================================

deploy_openvino_interactive() {
    local force_model_download=0

    echo ""
    echo "═══════════════════════════════════════════"
    echo "  OpenVINO Deployment Setup"
    echo "═══════════════════════════════════════════"
    echo ""

    # Ask about deployment method
    read -p "Deployment method (baremetal/container) [baremetal]: " deployment_method_input
    deployment_method_input=${deployment_method_input:-"baremetal"}
    export DEPLOYMENT_METHOD="${deployment_method_input}"

    echo ""
    echo "Selected deployment method: ${DEPLOYMENT_METHOD}"
    if [[ "${DEPLOYMENT_METHOD}" == "baremetal" ]]; then
        echo "  → Python processes with virtual environment"
    else
        echo "  → Docker containers"
    fi
    echo ""

    if [[ "${DEPLOYMENT_METHOD}" == "container" ]]; then
        check_docker_and_compose_ready
    fi

    if [[ "${RESTART_ON_RERUN}" != "1" ]] && are_target_services_running "openvino" "${DEPLOYMENT_METHOD}"; then
        echo "OpenVINO ${DEPLOYMENT_METHOD} services are already running."
        echo "Skipping redeploy. Use './tools/quick_start.sh restart' to force restart."
        return 0
    fi

    # Setup Python environment if baremetal deployment
    if [[ "${DEPLOYMENT_METHOD}" == "baremetal" ]]; then
        setup_python_venv
        verify_venv_activated
        check_pip_requirements
        check_npm_requirements
        echo ""
        echo "Python environment ready."
        echo ""
    fi

    # Gather user inputs
    ip_address=$(hostname -I | awk '{print $1}')
    HOST_IP=$(get_user_input "host ip" "${ip_address}")
    DOC_PATH=$(get_user_input "DOC_PATH" "$WORKPATH/workspace")
    TMPFILE_PATH=$(get_user_input "TMPFILE_PATH" "$WORKPATH/workspace")
    MILVUS_ENABLED=$(get_enable_function "MILVUS DB(Enter 0 to disable)" "1")
    CHAT_HISTORY_ROUND=$(get_user_input "chat history round" "0")
    LLM_MODEL=$(get_user_input "your LLM model" "Qwen/Qwen3-8B")
    MODEL_PATH=$(get_user_input "your model path" "${WORKPATH}/workspace/models")

    # Ask about model preparation
    read -p "Have you prepared models in ${MODEL_PATH}? (yes/no) [yes]: " user_input
    user_input=${user_input:-"yes"}
    user_input=${user_input,,}

    if [[ "$user_input" != "yes" && "$user_input" != "y" ]]; then
        force_model_download=1
        echo "Models not prepared. Auto downloading required models into ${MODEL_PATH}..."
    fi

    # Export environment variables
    export HOST_IP
    export MODEL_PATH
    export DOC_PATH
    export TMPFILE_PATH
    export MILVUS_ENABLED
    export CHAT_HISTORY_ROUND
    export LLM_MODEL

    # If user explicitly said models are not prepared, force download in interactive mode.
    if [[ "${force_model_download}" == "1" ]]; then
        if [[ "${SKIP_MODEL_CHECK}" == "1" ]]; then
            echo "User selected models not prepared; forcing model download (ignoring --skip-model-check)"
        fi
        download_required_models_for_backend "openvino" "${LLM_MODEL}"
    # In interactive mode, user-confirmed prepared models should skip verification/download.
    elif [[ "${DEPLOYMENT_METHOD}" == "baremetal" ]]; then
        echo "User confirmed models are prepared; skipping model verification/download in interactive mode."
    fi

    # Delegate to bootstrap.sh
    echo ""
    echo "Starting OpenVINO deployment..."
    restart_services_before_deploy
    export INFERENCE_BACKEND="openvino"
    # Use existing DEPLOYMENT_METHOD if set, otherwise default to baremetal
    export DEPLOYMENT_METHOD="${DEPLOYMENT_METHOD:-baremetal}"
    export SKIP_VALIDATION=1
    save_bootstrap_env_snapshot "${INFERENCE_BACKEND}" "${DEPLOYMENT_METHOD}"
    bash "${SCRIPT_DIR}/bootstrap.sh"
}

deploy_openvino_noninteractive() {
    echo ""
    echo "Starting OpenVINO deployment (non-interactive)..."

    if [[ "${DEPLOYMENT_METHOD}" == "container" ]]; then
        check_docker_and_compose_ready
    fi

    if [[ "${RESTART_ON_RERUN}" != "1" ]] && are_target_services_running "openvino" "${DEPLOYMENT_METHOD}"; then
        echo "OpenVINO ${DEPLOYMENT_METHOD} services are already running."
        echo "Skipping redeploy. Use './tools/quick_start.sh restart' to force restart."
        return 0
    fi

    # Download/verify models (only for baremetal, containers handle this internally)
    if [[ "${DEPLOYMENT_METHOD}" == "baremetal" ]]; then
        if [[ "${SKIP_MODEL_CHECK}" == "1" ]]; then
            echo "Skipping model verification/download (--skip-model-check enabled)"
        else
            ensure_required_models_for_ov
        fi
    fi

    # Delegate to bootstrap.sh
    restart_services_before_deploy
    export INFERENCE_BACKEND="openvino"
    # Use existing DEPLOYMENT_METHOD if set, otherwise default to baremetal
    export DEPLOYMENT_METHOD="${DEPLOYMENT_METHOD:-baremetal}"
    export SKIP_VALIDATION=1
    save_bootstrap_env_snapshot "${INFERENCE_BACKEND}" "${DEPLOYMENT_METHOD}"
    bash "${SCRIPT_DIR}/bootstrap.sh"
}

deploy_vllm_interactive() {
    local backend=$1  # a770 or b60
    local force_model_download=0

    echo ""
    echo "═══════════════════════════════════════════"
    echo "  vLLM ${backend^^} Deployment Setup"
    echo "═══════════════════════════════════════════"
    echo ""

    # Ask about deployment method
    read -p "Deployment method (baremetal/container) [baremetal]: " deployment_method_input
    deployment_method_input=${deployment_method_input:-"baremetal"}
    export DEPLOYMENT_METHOD="${deployment_method_input}"

    echo ""
    echo "Selected deployment method: ${DEPLOYMENT_METHOD}"
    if [[ "${DEPLOYMENT_METHOD}" == "baremetal" ]]; then
        echo "  → vLLM container + EdgeCraftRAG services as Python processes"
    else
        echo "  → All services in Docker containers"
    fi
    echo ""

    # vLLM deployments always use Docker for model serving.
    check_docker_and_compose_ready

    if [[ "${RESTART_ON_RERUN}" != "1" ]] && are_target_services_running "vllm" "${DEPLOYMENT_METHOD}"; then
        echo "vLLM ${DEPLOYMENT_METHOD} services are already running."
        echo "Skipping redeploy. Use './tools/quick_start.sh restart' to force restart."
        return 0
    fi

    # Setup Python environment if baremetal deployment
    if [[ "${DEPLOYMENT_METHOD}" == "baremetal" ]]; then
        setup_python_venv
        verify_venv_activated
        check_pip_requirements
        check_npm_requirements
        echo ""
        echo "Python environment ready."
        echo ""
    fi

    # Gather user inputs
    ip_address=$(hostname -I | awk '{print $1}')
    HOST_IP=$(get_user_input "host ip" "${ip_address}")
    DOC_PATH=$(get_user_input "DOC_PATH" "$WORKPATH/workspace")
    TMPFILE_PATH=$(get_user_input "TMPFILE_PATH" "$WORKPATH/workspace")
    MILVUS_ENABLED=$(get_enable_function "MILVUS DB(Enter 0 to disable)" "1")
    CHAT_HISTORY_ROUND=$(get_user_input "chat history round" "0")
    LLM_MODEL=$(get_user_input "your LLM model" "Qwen/Qwen3-8B")
    MODEL_PATH=$(get_user_input "your model path" "${WORKPATH}/workspace/models")

    # Ask about model preparation
    read -p "Have you prepared models in ${MODEL_PATH}? (yes/no) [yes]: " user_input
    user_input=${user_input:-"yes"}

    if [ "$user_input" != "yes" ]; then
        force_model_download=1
        echo "Models not prepared. Auto downloading required models into ${MODEL_PATH}..."
    fi

    # Export environment variables
    export HOST_IP
    export MODEL_PATH
    export DOC_PATH
    export TMPFILE_PATH
    export MILVUS_ENABLED
    export CHAT_HISTORY_ROUND
    export LLM_MODEL
    export VLLM_BACKEND="${backend}"

    # vLLM specific parameters
    set_vllm_defaults
    export MAX_MODEL_LEN=$(get_user_input "MAX_MODEL_LEN" "${MAX_MODEL_LEN}")
    export GPU_MEMORY_UTIL=$(get_user_input "GPU_MEMORY_UTIL (e.g. 0.8)" "${GPU_MEMORY_UTIL}")
    export QUANTIZATION=$(get_user_input "QUANTIZATION (fp8/sym_int4)" "${QUANTIZATION}")
    export TOOL_PARSER=$(get_user_input "tool_parser (qwen3_coder/hermes)" "${TOOL_PARSER}")

    if [ "$backend" == "a770" ]; then
        read -p "Tensor parallel size (TP size) [1]: " TP
        TP=${TP:-1}
        export TP
        export CCL_DG2_USM=$(get_user_input "Set USM (Core=1, Xeon=0, default=0)" 0)
    elif [ "$backend" == "b60" ]; then
        read -p "DP number (how many containers to run) [1]: " DP
        export DP=${DP:-1}
        read -p "Tensor parallel size (TP size) [1]: " TP
        export TP=${TP:-1}
        export DTYPE=$(get_user_input "DTYPE (vLLM data type, e.g. float16/bfloat16)" "float16")
        export ZE_AFFINITY_MASK=$(get_user_input "ZE_AFFINITY_MASK (GPU affinity mask)" "0")
    fi

    # If user explicitly said models are not prepared, force download in interactive mode.
    if [[ "${force_model_download}" == "1" ]]; then
        if [[ "${SKIP_MODEL_CHECK}" == "1" ]]; then
            echo "User selected models not prepared; forcing model download (ignoring --skip-model-check)"
        fi
        download_required_models_for_backend "vllm_${backend}" "${LLM_MODEL}"
    # Download/verify models (only for baremetal, containers handle this internally)
    elif [[ "${DEPLOYMENT_METHOD}" == "baremetal" ]]; then
        if [[ "${SKIP_MODEL_CHECK}" == "1" ]]; then
            echo "Skipping model verification/download (--skip-model-check enabled)"
        else
            download_required_models_for_backend "vllm_${backend}" "${LLM_MODEL}"
        fi
    fi

    # Delegate to bootstrap.sh
    echo ""
    echo "Starting vLLM ${backend^^} deployment..."
    restart_services_before_deploy
    if [ "$backend" == "a770" ]; then
        export INFERENCE_BACKEND="vllm_a770"
    else
        export INFERENCE_BACKEND="vllm_b60"
    fi
    # Use existing DEPLOYMENT_METHOD if set, otherwise default to baremetal
    export DEPLOYMENT_METHOD="${DEPLOYMENT_METHOD:-baremetal}"
    export SKIP_VALIDATION=1
    save_bootstrap_env_snapshot "${INFERENCE_BACKEND}" "${DEPLOYMENT_METHOD}"
    bash "${SCRIPT_DIR}/bootstrap.sh"
}

deploy_vllm_noninteractive() {
    local backend=$1  # a770 or b60

    echo ""
    echo "Starting vLLM ${backend^^} deployment (non-interactive)..."

    # vLLM deployments always use Docker for model serving.
    check_docker_and_compose_ready

    if [[ "${RESTART_ON_RERUN}" != "1" ]] && are_target_services_running "vllm" "${DEPLOYMENT_METHOD}"; then
        echo "vLLM ${backend^^} ${DEPLOYMENT_METHOD} services are already running."
        echo "Skipping redeploy. Use './tools/quick_start.sh restart' to force restart."
        return 0
    fi

    export VLLM_BACKEND="${backend}"
    set_vllm_defaults

    # Download/verify models (only for baremetal, containers handle this internally)
    if [[ "${DEPLOYMENT_METHOD}" == "baremetal" ]]; then
        if [[ "${SKIP_MODEL_CHECK}" == "1" ]]; then
            echo "Skipping model verification/download (--skip-model-check enabled)"
        else
            ensure_required_models_for_vllm
        fi
    fi

    # Delegate to bootstrap.sh
    restart_services_before_deploy
    if [ "$backend" == "a770" ]; then
        export INFERENCE_BACKEND="vllm_a770"
    else
        export INFERENCE_BACKEND="vllm_b60"
    fi
    # Use existing DEPLOYMENT_METHOD if set, otherwise default to baremetal
    export DEPLOYMENT_METHOD="${DEPLOYMENT_METHOD:-baremetal}"
    export SKIP_VALIDATION=1
    save_bootstrap_env_snapshot "${INFERENCE_BACKEND}" "${DEPLOYMENT_METHOD}"
    bash "${SCRIPT_DIR}/bootstrap.sh"
}

deploy_ovms_interactive() {
    local force_model_download=0

    echo ""
    echo "═══════════════════════════════════════════"
    echo "  OVMS Deployment Setup"
    echo "═══════════════════════════════════════════"
    echo ""

    read -p "Deployment method (baremetal/container) [baremetal]: " deployment_method_input
    deployment_method_input=${deployment_method_input:-"baremetal"}
    export DEPLOYMENT_METHOD="${deployment_method_input}"

    echo ""
    echo "Selected deployment method: ${DEPLOYMENT_METHOD}"
    if [[ "${DEPLOYMENT_METHOD}" == "baremetal" ]]; then
        echo "  → OVMS container + EdgeCraftRAG services as Python processes"
    else
        echo "  → All services in Docker containers"
    fi
    echo ""

    check_docker_and_compose_ready

    if [[ "${RESTART_ON_RERUN}" != "1" ]] && are_target_services_running "ovms" "${DEPLOYMENT_METHOD}"; then
        echo "OVMS ${DEPLOYMENT_METHOD} services are already running."
        echo "Skipping redeploy. Use './tools/quick_start.sh restart' to force restart."
        return 0
    fi

    if [[ "${DEPLOYMENT_METHOD}" == "baremetal" ]]; then
        setup_python_venv
        verify_venv_activated
        check_pip_requirements
        check_npm_requirements
        echo ""
        echo "Python environment ready."
        echo ""
    fi

    ip_address=$(hostname -I | awk '{print $1}')
    HOST_IP=$(get_user_input "host ip" "${ip_address}")
    DOC_PATH=$(get_user_input "DOC_PATH" "$WORKPATH/workspace")
    TMPFILE_PATH=$(get_user_input "TMPFILE_PATH" "$WORKPATH/workspace")
    MILVUS_ENABLED=$(get_enable_function "MILVUS DB(Enter 0 to disable)" "1")
    CHAT_HISTORY_ROUND=$(get_user_input "chat history round" "0")
    LLM_MODEL=$(get_user_input "your LLM model" "Qwen/Qwen3-8B")
    MODEL_PATH=$(get_user_input "your model path" "${WORKPATH}/workspace/models")
    OVMS_SERVICE_PORT=$(get_user_input "OVMS service port" "8000")

    # Ask about model preparation
    read -p "Have you prepared models in ${MODEL_PATH}? (yes/no) [yes]: " user_input
    user_input=${user_input:-"yes"}
    if [ "$user_input" != "yes" ]; then
        force_model_download=1
        echo "Models not prepared. Auto downloading required models into ${MODEL_PATH}..."
    fi

    export HOST_IP
    export MODEL_PATH
    export DOC_PATH
    export TMPFILE_PATH
    export MILVUS_ENABLED
    export CHAT_HISTORY_ROUND
    export LLM_MODEL
    export OVMS_SERVICE_PORT
    unset OVMS_ENDPOINT OVMS_REST_PORT OVMS_SOURCE_MODEL OVMS_MODEL_REPOSITORY_PATH OVMS_MODEL_NAME \
        OVMS_TARGET_DEVICE OVMS_TASK OVMS_CACHE_DIR OVMS_ENABLE_PREFIX_CACHING OVMS_TOOL_PARSER \
        OVMS_ENABLE_TOOL_GUIDED_GENERATION OVMS_MAX_NUM_BATCHED_TOKENS
    set_ovms_defaults

    if [[ "${force_model_download}" == "1" ]]; then
        if [[ "${SKIP_MODEL_CHECK}" == "1" ]]; then
            echo "User selected models not prepared; forcing model download (ignoring --skip-model-check)"
        fi
        download_required_models_for_backend "ovms" "${LLM_MODEL}"
    elif [[ "${DEPLOYMENT_METHOD}" == "baremetal" ]]; then
        if [[ "${SKIP_MODEL_CHECK}" == "1" ]]; then
            echo "Skipping model verification/download (--skip-model-check enabled)"
        else
            download_required_models_for_backend "ovms" "${LLM_MODEL}"
        fi
    fi

    echo ""
    echo "Starting OVMS deployment..."
    restart_services_before_deploy
    export INFERENCE_BACKEND="ovms"
    export DEPLOYMENT_METHOD="${DEPLOYMENT_METHOD:-baremetal}"
    export SKIP_VALIDATION=1
    save_bootstrap_env_snapshot "${INFERENCE_BACKEND}" "${DEPLOYMENT_METHOD}"
    bash "${SCRIPT_DIR}/bootstrap.sh"
}

deploy_ovms_noninteractive() {
    echo ""
    echo "Starting OVMS deployment (non-interactive)..."

    check_docker_and_compose_ready

    if [[ "${RESTART_ON_RERUN}" != "1" ]] && are_target_services_running "ovms" "${DEPLOYMENT_METHOD}"; then
        echo "OVMS ${DEPLOYMENT_METHOD} services are already running."
        echo "Skipping redeploy. Use './tools/quick_start.sh restart' to force restart."
        return 0
    fi

    set_ovms_defaults

    if [[ "${DEPLOYMENT_METHOD}" == "baremetal" ]]; then
        if [[ "${SKIP_MODEL_CHECK}" == "1" ]]; then
            echo "Skipping model verification/download (--skip-model-check enabled)"
        else
            ensure_required_models_for_vllm
        fi
    fi

    restart_services_before_deploy
    export INFERENCE_BACKEND="ovms"
    export DEPLOYMENT_METHOD="${DEPLOYMENT_METHOD:-baremetal}"
    export SKIP_VALIDATION=1
    save_bootstrap_env_snapshot "${INFERENCE_BACKEND}" "${DEPLOYMENT_METHOD}"
    bash "${SCRIPT_DIR}/bootstrap.sh"
}

#==============================================================================
# Usage Information
#==============================================================================

usage() {
    cat << EOF
EdgeCraftRAG Quick Start
One-command deployment with automatic model download and setup

USAGE:
    ./tools/quick_start.sh [COMMAND] [OPTIONS]

COMMANDS:
    (none)          Start deployment (interactive or non-interactive mode)
    cleanup         Stop all services and cleanup
    restart         Restart all services, then deploy

OPTIONS:
    -h, --help      Show this help message
    --version       Show script version
    -i, --interactive Enable interactive mode (prompt for deployment selection)
    --skip-model-check Skip model verification/download steps
    --skip-gpu-driver-check Skip Intel GPU driver validation/install steps

MODES:
    Interactive Mode:
        ./tools/quick_start.sh -i

        Prompts for:
                    • Deployment type (OpenVINO/vLLM_A770/vLLM_B60/OVMS)
          • Deployment method (baremetal/container)
          • Configuration parameters (HOST_IP, MODEL_PATH, etc.)

    Non-Interactive Mode (default):
        ./tools/quick_start.sh

        Uses environment variables (see below)
        Default: OpenVINO baremetal deployment

ENVIRONMENT VARIABLES:
    Deployment Selection:
        INFERENCE_BACKEND   Inference backend: openvino|vllm_a770|vllm_b60|ovms (default: openvino)
        COMPOSE_PROFILES    Backward-compatible alias for legacy profile selection
        DEPLOYMENT_METHOD   Deployment method: baremetal|container (default: baremetal)
                           baremetal = Python processes with venv/pip checks
                           container = Docker containers (skips venv/pip checks)

    Common Configuration:
        HOST_IP            Server IP address (default: auto-detected)
        MODEL_PATH         Model storage path (default: workspace/models)
        DOC_PATH           Document storage path (default: workspace)
        TMPFILE_PATH       Temporary files path (default: workspace)
        LLM_MODEL          LLM model name (default: Qwen/Qwen3-8B)
        EMBEDDING_MODEL    Embedding model ID (default: BAAI/bge-small-en-v1.5)
        RERANKER_MODEL     Reranker model ID (default: BAAI/bge-reranker-large)
        MODEL_DOWNLOAD_SOURCE Model source: modelscope|huggingface (default: modelscope)
        MILVUS_ENABLED     Enable Milvus DB: 0|1 (default: 1)
        CHAT_HISTORY_ROUND Chat history length (default: 0)
        SKIP_MODEL_CHECK   Skip model verification/download: 0|1 (default: 0)
        SKIP_INTEL_GPU_DRIVER_CHECK Skip Intel GPU driver validation/install: 0|1 (default: 0)
        AUTO_INSTALL_INTEL_GPU_DRIVER Auto install Intel GPU driver/runtime when missing: 0|1 (default: 1)
        AUTO_INSTALL_NPM   Auto install npm when missing for baremetal UI startup: 0|1 (default: 1)
        RESTART_ON_RERUN  Restart services when quick_start is run again: 0|1 (default: 0)
                          (set to 1 automatically when using 'restart' command)

    vLLM Specific (A770/B60):
        MAX_MODEL_LEN      Maximum model context length (default: 8192)
        GPU_MEMORY_UTIL    GPU memory utilization ratio (default: 0.8)
        QUANTIZATION       Quantization mode: fp8|sym_int4 (default: fp8)
        TOOL_PARSER        Tool parser: qwen3_coder|hermes (default: qwen3_coder)

    vLLM Specific (A770):
        TP                 Tensor parallel size (default: 1)
        CCL_DG2_USM        USM setting (default: 0)

    vLLM Specific (B60):
        DP                 Data parallel instances (default: 1)
        TP                 Tensor parallel size (default: 1)
        DTYPE              Data type: float16|bfloat16 (default: float16)
        ZE_AFFINITY_MASK   GPU affinity mask (default: 0)

FEATURES:
    ✓ Automatic Python virtual environment setup (baremetal mode)
    ✓ Virtual environment activation verification (Python 3.10+ check)
    ✓ Automatic pip requirements check and installation (baremetal mode)
    ✓ Automatic npm check and installation for baremetal UI startup
    ✓ Optional full-service restart via 'restart' command
    ✓ Automatic model download (default ModelScope, optional Hugging Face)
    ✓ Model download logic extracted to tools/model_download.sh
    ✓ Supports both baremetal and container deployment methods
    ✓ Delegates to bootstrap.sh for deployment
    ✓ Interactive prompts or environment variable configuration

EXAMPLES:
    # Interactive mode (prompts for deployment selection)
    ./tools/quick_start.sh -i

    # Non-interactive OpenVINO deployment (default)
    ./tools/quick_start.sh

    # Non-interactive vLLM A770 deployment
    export INFERENCE_BACKEND=vllm_a770
    export MODEL_PATH=/data/models
    ./tools/quick_start.sh

    # Non-interactive vLLM B60 deployment with custom settings
    export INFERENCE_BACKEND=vllm_b60
    export MODEL_PATH=/data/models
    export DP=2
    export TP=1
    ./tools/quick_start.sh

    # Container deployment (skips venv and pip checks)
    export DEPLOYMENT_METHOD=container
    export MODEL_PATH=/data/models
    ./tools/quick_start.sh

    # OVMS deployment
    export INFERENCE_BACKEND=ovms
    ./tools/quick_start.sh

    # Skip model verification/download (models must already exist)
    ./tools/quick_start.sh --skip-model-check

    # Skip Intel GPU driver validation/install
    ./tools/quick_start.sh --skip-gpu-driver-check

    # Cleanup (stop all services)
    ./tools/quick_start.sh cleanup

    # Restart all services, then deploy
    ./tools/quick_start.sh restart

DEPLOYMENT METHOD:
    This script supports two deployment methods (set via DEPLOYMENT_METHOD):

    Baremetal (default):
      • Runs services as Python processes with virtual environment
      • Automatic venv setup and pip requirements installation
      • OpenVINO: All services as Python processes (no Docker)
      • vLLM: vLLM container + EdgeCraftRAG services as processes
      • Benefits: Faster startup, direct log access, easier debugging

    Container:
      • Runs all services in Docker containers
      • Skips venv and pip checks (containers are pre-built)
      • All services managed via Docker Compose
      • Benefits: Isolated environment, easier distribution

LOGS:
    OpenVINO: workspace/logs/bare_metal/
    vLLM:     workspace/logs/vllm_baremetal/

SERVICE MANAGEMENT:
    Start:    ./tools/quick_start.sh
    Status:   ./tools/run_ov_baremetal.sh status
              ./tools/run_vllm_baremetal.sh status
              ./tools/run_ovms_baremetal.sh status
    Stop:     ./tools/quick_start.sh cleanup
    Restart:  ./tools/quick_start.sh restart

NOTES:
    • First run will download models automatically if missing (unless --skip-model-check is used)
    • Intel GPU driver/runtime is validated automatically and installed when missing (apt-based Linux)
    • Python 3.10+ required; 3.10/3.11 recommended for the smoothest setup
    • For container deployment, use bootstrap.sh with DEPLOYMENT_METHOD=container
    • Backward compatible with previous COMPOSE_PROFILES settings

For more details, see: EdgeCraftRAG/tools/README.md

EOF
}

#==============================================================================
# Cleanup Function
#==============================================================================

cleanup_services() {
    # Delegate to bootstrap.sh
    bash "${SCRIPT_DIR}/bootstrap.sh" cleanup
}

#==============================================================================
# Main Function
#==============================================================================

main() {
    local command=""

    # Parse command line arguments
    while [[ $# -gt 0 ]]; do
        case "$1" in
            -h|--help|help)
                usage
                exit 0
                ;;
            --version)
                echo "EdgeCraftRAG Quick Start v1.0"
                exit 0
                ;;
            -i|--interactive)
                export INTERACTIVE_MODE=1
                ;;
            --skip-model-check)
                export SKIP_MODEL_CHECK=1
                ;;
            --skip-gpu-driver-check)
                export SKIP_INTEL_GPU_DRIVER_CHECK=1
                ;;
            cleanup)
                if [[ -n "${command}" ]]; then
                    echo "ERROR: Multiple commands provided."
                    usage
                    exit 1
                fi
                command="cleanup"
                ;;
            restart)
                if [[ -n "${command}" ]]; then
                    echo "ERROR: Multiple commands provided."
                    usage
                    exit 1
                fi
                command="restart"
                ;;
            *)
                echo "ERROR: Unknown argument: $1"
                usage
                exit 1
                ;;
        esac
        shift
    done

    if [[ "${command}" == "cleanup" ]]; then
        cleanup_services
        exit 0
    fi

    if [[ "${command}" == "restart" ]]; then
        export RESTART_ON_RERUN=1
    fi

    ensure_intel_gpu_driver_ready

    # For interactive mode, skip venv/pip checks here
    # The deploy_*_interactive functions will handle environment setup based on user's choice
    if [[ "${INTERACTIVE_MODE:-0}" != "1" ]]; then
        # Non-interactive mode: detect deployment method and setup environment
        DEPLOYMENT_METHOD=${DEPLOYMENT_METHOD:-baremetal}

        # Skip venv and pip checks for container deployments
        if [[ "${DEPLOYMENT_METHOD}" == "container" ]]; then
            echo ""
            echo "Container deployment detected - skipping Python environment setup"
            echo ""
        else
            # Setup Python virtual environment for baremetal deployments
            setup_python_venv

            # Verify venv is activated
            verify_venv_activated

            # Check and install pip requirements
            check_pip_requirements

            # Check and install npm for baremetal UI startup
            check_npm_requirements

            echo ""
            echo "Deployment preparation complete."
            echo ""
        fi
    fi

    # Detect interactive vs non-interactive mode
    # Use INTERACTIVE_MODE variable set by -i flag or environment
    if [[ "${INTERACTIVE_MODE:-0}" == "1" ]]; then
        # Interactive mode: prompt user
        echo ""
        echo "════════════════════════════════════════════════════════════"
        echo "  EdgeCraftRAG Quick Start - Interactive Mode"
        echo "════════════════════════════════════════════════════════════"
        echo ""

        # Use timeout with read to prevent hanging
        if read -t 60 -p "Do you want to start vLLM, OVMS, or local OpenVINO services? (vLLM_A770/vLLM_B60/ovms/ov) [ov]: " user_input; then
            user_input=${user_input:-"ov"}
        else
            echo ""
            echo "No input received (timeout or non-interactive), defaulting to OpenVINO..."
            user_input="ov"
        fi

        if [[ "$user_input" == "vLLM_A770" ]]; then
            deploy_vllm_interactive "a770"
        elif [[ "$user_input" == "vLLM_B60" ]]; then
            deploy_vllm_interactive "b60"
        elif [[ "$user_input" == "ovms" || "$user_input" == "OVMS" ]]; then
            deploy_ovms_interactive
        else
            deploy_openvino_interactive
        fi
    else
        # Non-interactive mode: resolve INFERENCE_BACKEND with openvino as the default
        echo "Running in non-interactive mode..."
        export COMPOSE_PROFILES=${COMPOSE_PROFILES:-""}

        selected_backend="${INFERENCE_BACKEND:-}"
        if [[ -z "${selected_backend}" ]]; then
            case "${COMPOSE_PROFILES}" in
                vLLM_A770|vLLM|vllm_on_a770)
                    selected_backend="vllm_a770"
                    ;;
                vLLM_B60|vLLM_b60|vllm_on_b60)
                    selected_backend="vllm_b60"
                    ;;
                ovms|OVMS)
                    selected_backend="ovms"
                    ;;
                *)
                    selected_backend="openvino"
                    ;;
            esac
        fi
        export INFERENCE_BACKEND="${selected_backend}"

        if [[ "$selected_backend" == "vllm_a770" || "$selected_backend" == "vLLM_A770" || "$selected_backend" == "vLLM" || "$selected_backend" == "vllm_on_a770" ]]; then
            echo "Detected vLLM A770 inference backend"
            deploy_vllm_noninteractive "a770"
        elif [[ "$selected_backend" == "vllm_b60" || "$selected_backend" == "vLLM_B60" || "$selected_backend" == "vLLM_b60" || "$selected_backend" == "vllm_on_b60" ]]; then
            echo "Detected vLLM B60 inference backend"
            deploy_vllm_noninteractive "b60"
        elif [[ "$selected_backend" == "ovms" || "$selected_backend" == "OVMS" ]]; then
            echo "Detected OVMS inference backend"
            deploy_ovms_noninteractive
        else
            echo "Detected OpenVINO inference backend (default)"
            deploy_openvino_noninteractive
        fi
    fi
}

main "$@"
