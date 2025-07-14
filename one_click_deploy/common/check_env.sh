#!/bin/bash
# Copyright (C) 2025 Intel Corporation
# SPDX-License-Identifier: Apache-2.0

# Script's own directory
SCRIPT_DIR_ENV=$(cd "$(dirname "${BASH_SOURCE[0]}")" &>/dev/null && pwd)
# Source utility functions
source "${SCRIPT_DIR_ENV}/utils.sh" # Assuming utils.sh is in the same directory

# =================== CONFIG ===================
REQUIRED_CMDS=("git" "docker" "curl" "vim" "nproc") # Added nproc for CPU check
THRESHOLD_GB=5
EXAMPLE_MIN_CPU=32
EXAMPLE_MIN_HPU=1
# LOG_FILE is now managed by utils.sh, can be overridden here if needed:
# LOG_FILE="check_env.log" # Specific log file for this script

# ================ ARG PARSING =================
DEVICE="" # Standardized to DEVICE
DEPLOYMENT_MODE="online" # Default to online, can be overridden

while [[ $# -gt 0 ]]; do
    case "$1" in
        --log-file)
            LOG_FILE="$2" # Allow overriding utils.sh default
            shift 2
            ;;
        --device) # Changed from --xeon/--gaudi to --device xeon/gaudi
            DEVICE="$2"
            if [[ "$DEVICE" != "xeon" && "$DEVICE" != "gaudi" ]]; then
                log ERROR "Invalid --device: $DEVICE. Must be 'xeon' or 'gaudi'."
                exit 1
            fi
            shift 2
            ;;
        --mode) # For online/offline package installation
            DEPLOYMENT_MODE="$2"
            if [[ "$DEPLOYMENT_MODE" != "online" && "$DEPLOYMENT_MODE" != "offline" ]]; then
                log ERROR "--mode must be either 'online' or 'offline'."
                exit 1
            fi
            shift 2
            ;;
        *)
            log WARN "Unknown argument: $1"
            shift
            ;;
    esac
done

if [[ -z "$DEVICE" ]]; then
    log ERROR "Usage: $0 --device [xeon|gaudi] [--mode online|offline] [--log-file <filename>]"
    exit 1
fi

log INFO "Starting environment check for DEVICE: $DEVICE, MODE: $DEPLOYMENT_MODE"

# ================ DRIVER CHECKS =============
check_habana_modules() {
    log INFO "Checking Habana kernel modules..."
    local missing=0
    local required_modules=("habanalabs" "habanalabs_cn" "habanalabs_ib" "habanalabs_en")
    for module in "${required_modules[@]}"; do
        if ! lsmod | grep -q "^${module}\s"; then
            log ERROR "Module missing: ${module}"
            missing=$((missing + 1))
        else
            log OK "Module loaded: ${module}"
        fi
    done
    if [ $missing -gt 0 ]; then
        log ERROR "$missing required Habana modules missing. Please ensure Habana drivers are correctly installed."
        return 1 # Changed to return 1 for main to catch
    else
        log OK "All required Habana modules loaded."
        return 0
    fi
}

check_habana_sw() {
    log INFO "Listing installed Habana packages..."
    if ! apt list --installed 2>/dev/null | grep habana | tee -a "$LOG_FILE"; then
        log WARN "No Habana packages found via 'apt list'. This might be normal if installed differently, or an issue."
    fi
}

hl_qual_test() {
    log INFO "Starting Gaudi Function Tests (hl_qual)..."
    # Check if hl_qual exists
    if ! command_exists /opt/habanalabs/qual/gaudi2/bin/hl_qual; then
        log ERROR "hl_qual command not found at /opt/habanalabs/qual/gaudi2/bin/hl_qual. Skipping test."
        return 1
    fi
    export HABANA_LOGS="/tmp/hl_qual.log"
    # Temporarily cd for test, ensure we cd back
    local current_dir=$(pwd)
    cd /opt/habanalabs/qual/gaudi2/bin || { log ERROR "Failed to cd to hl_qual directory."; return 1; }

    # Run test, capture output and exit code
    # Reduced verbosity for general log, full output to $LOG_FILE
    # Consider making '-l extreme -t 2' configurable or less aggressive for a quick check
    output=$(./hl_qual -gaudi2 -c all -rmod parallel -f2 -l extreme -t 2 2>&1)
    exit_code=$?
    cd "$current_dir" # Go back to original directory

    echo "$output" >> "$LOG_FILE" # Log full output

    if [ $exit_code -ne 0 ]; then
        log ERROR "hl_qual test failed (exit code: $exit_code). Check $LOG_FILE for details."
        return 1
    fi

    # More robust parsing of PASSED
    if echo "$output" | grep -q "hl qual report" && echo "$output" | grep -q "PASSED"; then
        log OK "hl_qual test PASSED."
    else
        log ERROR "hl_qual test FAILED (did not detect 'PASSED' after 'hl qual report'). Check $LOG_FILE for details."
        return 1
    fi
    return 0
}

check_hl_cards() {
    log INFO "Checking Habana HPU cards via hl-smi..."
    if ! command_exists hl-smi; then
        log ERROR "hl-smi command not found. Cannot check HPU cards."
        return 1
    fi
    local total_cards available_cards
    # Ensure hl-smi output is parsable, handle errors
    if ! hl_smi_output=$(hl-smi); then
        log ERROR "hl-smi command failed to execute properly."
        return 1
    fi

    total_cards=$(echo "$hl_smi_output" | grep -E '^\| +[0-9]+ +HL-' | wc -l)
    # Assuming 'N/A' in a specific column indicates available for use (this might need verification based on actual hl-smi output for "available")
    # A more robust check might be needed depending on what "available" truly means in context of hl-smi
    available_cards=$(echo "$hl_smi_output" | grep -E '^\| +[0-9]+ +N/A' | wc -l) # This interpretation of "available" might need review

    log INFO "Total HL-SMI cards detected: $total_cards"
    log INFO "Cards reported as 'N/A' (interpreted as available): $available_cards"

    if [ "$available_cards" -lt "$EXAMPLE_MIN_HPU" ]; then
        log ERROR "Available HPU cards ($available_cards) is less than required minimum ($EXAMPLE_MIN_HPU)."
        return 1
    else
        log OK "Sufficient HPU cards available ($available_cards >= $EXAMPLE_MIN_HPU)."
    fi
    return 0
}

get_cpu_info() {
    log INFO "Checking CPU information..."
    local cpu_model total_cores
    cpu_model=$(grep -m1 'model name' /proc/cpuinfo | cut -d ':' -f2 | sed 's/^[[:space:]]*//')

    # Using nproc --all for logical cores, or lscpu for physical if preferred.
    if command_exists nproc; then
        total_cores=$(nproc --all)
    elif command_exists lscpu; then # Fallback if nproc is not available
        total_cores=$(lscpu | grep '^CPU(s):' | awk '{print $2}')
    else
        log WARN "Cannot determine CPU core count (nproc and lscpu not found). Skipping CPU core check."
        return 0 # Or return 1 if this is critical
    fi

    log INFO "CPU Model: $cpu_model"
    log INFO "Total logical CPU cores: $total_cores"

    if [ "$total_cores" -lt "$EXAMPLE_MIN_CPU" ]; then
        log ERROR "Detected CPU cores ($total_cores) is less than required minimum ($EXAMPLE_MIN_CPU)."
        return 1
    else
        log OK "CPU core count ($total_cores) is sufficient."
    fi

    log INFO "Attempting to set CPU governor to performance mode..."
    if echo "performance" | sudo tee /sys/devices/system/cpu/cpu*/cpufreq/scaling_governor > /dev/null 2>&1; then
        log OK "CPU governor set to performance mode for all cores."
    else
        log WARN "Failed to set CPU governor to performance. This might require sudo privileges or a different path."
    fi
    return 0
}

# ================ SOFTWARE CHECKS ===============

install_docker() {
    subsection_header "Installing Docker"

    # install docker
    if ! sudo apt install -y docker.io 2>&1 | tee -a "$LOG_FILE"; then
        log ERROR "Failed to install Docker."
        return 1
    fi

    sudo chmod 666 /var/run/docker.sock

    # install docker compose
    DOCKER_CONFIG=${DOCKER_CONFIG:-$HOME/.docker}
    mkdir -p $DOCKER_CONFIG/cli-plugins
    curl -SL https://github.com/docker/compose/releases/download/v2.36.0/docker-compose-linux-x86_64 -o $DOCKER_CONFIG/cli-plugins/docker-compose
    chmod +x $DOCKER_CONFIG/cli-plugins/docker-compose

    if docker compose version &>> "$LOG_FILE"; then
        log OK "Docker and Docker Compose successfully installed."
    else
        log ERROR "Docker Compose installation failed."
        return 1
    fi

    # set docker proxy
    sudo mkdir -p /etc/systemd/system/docker.service.d
    HTTP_PROXY=${http_proxy:-}
    HTTPS_PROXY=${https_proxy:-}
    NO_PROXY=${no_proxy:-}

    sudo tee /etc/systemd/system/docker.service.d/http-proxy.conf > /dev/null <<EOF
[Service]
Environment="HTTP_PROXY=${http_proxy}" "HTTPS_PROXY=${https_proxy}" "NO_PROXY=${no_proxy}"
EOF

    # restart docker
    sudo systemctl daemon-reexec
    sudo systemctl daemon-reload
    sudo systemctl restart docker

    log OK "Docker restarted successfully."
    log INFO "Docker proxy:"
    log INFO "HTTP_PROXY=$HTTP_PROXY"
    log INFO "HTTPS_PROXY=$HTTPS_PROXY"
    log INFO "NO_PROXY=$NO_PROXY"
}

check_required_commands() {
    local all_ready=true
    for cmd in "${REQUIRED_CMDS[@]}"; do
        if ! command -v "$cmd" &> /dev/null; then
            log ERROR "$cmd is not installed, try to install it..."

            if [[ "$cmd" == "docker" ]]; then
                log INFO "Installing Docker and Docker Compose..."
                if ! install_docker; then
                    all_ready=false
                    continue
                fi
            else
                log INFO "Attempting to install $cmd..."
                apt-get update -qq
                apt-get install -y "$cmd" &>> "$LOG_FILE"

                if command -v "$cmd" &> /dev/null; then
                    log OK "$cmd successfully installed."
                else
                    log ERROR "Failed to install $cmd automatically."
                    all_ready=false
                fi
            fi
        else
            log OK "$cmd is available."
        fi
    done
    $all_ready || return 1
}

# ================ DISK SPACE CHECKS ===============
check_disk_space() {
    log INFO "Checking available disk space on / ..."
    local available_gb
    # df -BG / might not be portable, -P is more POSIX compliant, awk for calculation
    available_bytes=$(df -P / | awk 'NR==2 {print $4}')
    available_gb=$((available_bytes / 1024 / 1024)) # KiloBytes to GigaBytes

    log INFO "Available disk space: ${available_gb}GB"
    if (( available_gb < THRESHOLD_GB )); then
        log ERROR "Not enough disk space. Required: ${THRESHOLD_GB}GB, Available: ${available_gb}GB."
        return 1
    else
        log OK "Disk space is sufficient (${available_gb}GB)."
    fi
    return 0
}

# ================ MAIN ========================
main() {
    local checks_failed=0

    section_header "HARDWARE & DRIVER ENVIRONMENT CHECK"
    if [[ "$DEVICE" == "xeon" ]]; then
        get_cpu_info || checks_failed=$((checks_failed + 1))
    elif [[ "$DEVICE" == "gaudi" ]]; then
        # For Gaudi, CPU info is also relevant
        get_cpu_info || checks_failed=$((checks_failed + 1))
        check_habana_modules || checks_failed=$((checks_failed + 1))
        check_habana_sw # This is informational, not typically a fail condition
        check_hl_cards || checks_failed=$((checks_failed + 1))
        hl_qual_test || checks_failed=$((checks_failed + 1))
    fi

    section_header "SOFTWARE DEPENDENCIES CHECK"
    check_required_commands || checks_failed=$((checks_failed + 1))

    section_header "DISK SPACE CHECK"
    check_disk_space || checks_failed=$((checks_failed + 1))

    if [ $checks_failed -gt 0 ]; then
        log ERROR "Environment check failed with $checks_failed error(s). Please review the logs."
        exit 1
    else
        log OK "All environment checks passed. System should be ready for deployment."
    fi
}

main
