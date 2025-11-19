#!/usr/bin/env bash

# Copyright (C) 2024 Intel Corporation
# SPDX-License-Identifier: Apache-2.0

# Navigate to the parent directory and source the environment
SCRIPT_DIR="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" &> /dev/null && pwd)"

pushd "$SCRIPT_DIR/../../../../../" > /dev/null
source .set_env.sh
popd > /dev/null

# Function to check if a variable is set
check_var() {
    local var_name="$1"
    local var_value="${!var_name}"
    if [ -z "${var_value}" ]; then
        echo "Error: ${var_name} is not set. Please set ${var_name}."
        return 1  # Return an error code but do not exit the script
    fi
}

# Check critical variables
check_var "HF_TOKEN"
export ip_address=$(hostname -I | awk '{print $1}')

# VLLM configuration
export VLLM_PORT="${VLLM_PORT:-8000}"
export VLLM_VOLUME="${VLLM_VOLUME:-/data2/huggingface}"
export VLLM_IMAGE="${VLLM_IMAGE:-opea/vllm-gaudi:latest}"
export LLM_MODEL_ID="${LLM_MODEL_ID:-meta-llama/Llama-3.3-70B-Instruct}"
export MAX_LEN="${MAX_LEN:-131072}"
export NUM_CARDS="${NUM_CARDS:-4}"
export HF_CACHE_DIR="${HF_CACHE_DIR:-"./data"}"
export OPENAI_BASE_URL="http://${ip_address}:8000/v1"
export OPENAI_API_KEY="empty"
export no_proxy=${no_proxy}
export http_proxy=${http_proxy}
export https_proxy=${https_proxy}


# Hugging Face API token
export HF_TOKEN="${HF_TOKEN}"

# API keys
check_var "TAVILY_API_KEY"
export TAVILY_API_KEY="${TAVILY_API_KEY}"
