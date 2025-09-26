#!/bin/bash
# Copyright (C) 2025 Intel Corporation
# SPDX-License-Identifier: Apache-2.0


# ========= Shared logging utilities ===========
LOG_FILE=${LOG_FILE:-deploy.log}

# ================ ANSI COLORS =================
COLOR_RESET="\033[0m"
COLOR_OK="\033[1;32m"
COLOR_ERROR="\033[1;31m"

# =============== LOGGING FUNCTIONS ============
log() {
    local level=$1
    local message=$2
    local icon color=""
    case "$level" in
        INFO)  icon="📘"; color="";;
        OK)    icon="✅"; color=$COLOR_OK;;
        ERROR) icon="❌"; color=$COLOR_ERROR;;
        *)     icon="🔹"; color="";;
    esac

    local timestamp
    timestamp=$(date '+%Y-%m-%d %H:%M:%S')
    local plain="$timestamp $icon [$level] $message"

    printf "%s %b\n" "$timestamp" "${color}${icon} [$level] $message${COLOR_RESET}"
    echo "$plain" >> "$LOG_FILE"
}

section_header() {
    local title="$1"
    local width=96
    local border_top="┌"
    local border_side="│"
    local border_bot="└"
    local fill_char="="

    local title_len=${#title}
    local pad=$(( (width - title_len) / 2 ))
    local pad_left=$(printf '%*s' "$pad" "")
    local pad_right=$(printf '%*s' "$((width - pad - title_len))" "")

    echo "" | tee -a "$LOG_FILE"
    echo "${border_top}$(printf '%*s' $width '' | tr ' ' "$fill_char")┐" | tee -a "$LOG_FILE"
    printf "${border_side}%-${width}s${border_side}\n" "${pad_left}${title}${pad_right}" | tee -a "$LOG_FILE"
    echo "${border_bot}$(printf '%*s' $width '' | tr ' ' "$fill_char")┘" | tee -a "$LOG_FILE"
}

command_exists() {
    command -v "$1" >/dev/null 2>&1
}


progress_bar() {
    local duration=${1:-60}
    local max_cols=$(($(tput cols)-10))
    local cols=0

    for ((i=0; i<=$duration; i++)); do
        percent=$((100*i/duration))

        cols=$((max_cols*i/duration))

        printf "\r["
        for ((j=0; j<$cols; j++)); do printf "#"; done
        for ((j=$cols; j<$max_cols; j++)); do printf " "; done
        printf "] %3d%%" $percent

        sleep 1
    done
    printf "\n"
}

get_huggingface_token() {
    local token_file="$HOME/.cache/huggingface/token"
    if [ -f "$token_file" ] && [ -r "$token_file" ]; then
        cat "$token_file" | tr -d '\n'
        return 0
    else
        return 1
    fi
}
