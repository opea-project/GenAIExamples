#!/usr/bin/env bash

# Copyright (C) 2025 Intel Corporation
# SPDX-License-Identifier: Apache-2.0

# Navigate to the parent directory and source the environment
pushd "../../../../../" > /dev/null
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
check_var "HOST_IP"

# VLLM configuration
export VLLM_PORT="${VLLM_PORT:-8086}"
export VLLM_VOLUME="${VLLM_VOLUME:-/data2/huggingface}"
export VLLM_IMAGE="${VLLM_IMAGE:-opea/vllm-gaudi:latest}"
export LLM_MODEL_ID="${LLM_MODEL_ID:-meta-llama/Llama-3.3-70B-Instruct}"
export LLM_ENDPOINT="http://${HOST_IP}:${VLLM_PORT}"
export MAX_LEN="${MAX_LEN:-16384}"
export NUM_CARDS="${NUM_CARDS:-4}"
export HF_CACHE_DIR="${HF_CACHE_DIR:-"./data"}"

# Data preparation and embedding configuration
export DATAPREP_PORT="${DATAPREP_PORT:-6007}"
export TEI_EMBEDDER_PORT="${TEI_EMBEDDER_PORT:-10221}"
export REDIS_URL_VECTOR="redis://${HOST_IP}:6379"
export REDIS_URL_KV="redis://${HOST_IP}:6380"
export DATAPREP_COMPONENT_NAME="${DATAPREP_COMPONENT_NAME:-OPEA_DATAPREP_REDIS_FINANCE}"
export EMBEDDING_MODEL_ID="${EMBEDDING_MODEL_ID:-BAAI/bge-base-en-v1.5}"
export TEI_EMBEDDING_ENDPOINT="http://${HOST_IP}:${TEI_EMBEDDER_PORT}"

# Hugging Face API token
export HF_TOKEN="${HF_TOKEN}"

# Recursion limits
export RECURSION_LIMIT_WORKER="${RECURSION_LIMIT_WORKER:-12}"
export RECURSION_LIMIT_SUPERVISOR="${RECURSION_LIMIT_SUPERVISOR:-10}"

# LLM configuration
export TEMPERATURE="${TEMPERATURE:-0.5}"
export MAX_TOKENS="${MAX_TOKENS:-4096}"
export MAX_INPUT_TOKENS="${MAX_INPUT_TOKENS:-2048}"
export MAX_TOTAL_TOKENS="${MAX_TOTAL_TOKENS:-4096}"

# Worker URLs
export WORKER_FINQA_AGENT_URL="http://${HOST_IP}:9095/v1/chat/completions"
export WORKER_RESEARCH_AGENT_URL="http://${HOST_IP}:9096/v1/chat/completions"

# DocSum configuration
export DOCSUM_COMPONENT_NAME="${DOCSUM_COMPONENT_NAME:-"OpeaDocSumvLLM"}"
export DOCSUM_ENDPOINT="http://${HOST_IP}:9000/v1/docsum"

# API keys
check_var "FINNHUB_API_KEY"
check_var "FINANCIAL_DATASETS_API_KEY"
export FINNHUB_API_KEY="${FINNHUB_API_KEY}"
export FINANCIAL_DATASETS_API_KEY="${FINANCIAL_DATASETS_API_KEY}"


# Toolset and prompt paths
if check_var "WORKDIR"; then
    export TOOLSET_PATH=$WORKDIR/GenAIExamples/FinanceAgent/tools/
    export PROMPT_PATH=$WORKDIR/GenAIExamples/FinanceAgent/prompts/

    echo "TOOLSET_PATH=${TOOLSET_PATH}"
    echo "PROMPT_PATH=${PROMPT_PATH}"

    # Array of directories to check
    REQUIRED_DIRS=("${TOOLSET_PATH}" "${PROMPT_PATH}")

    for dir in "${REQUIRED_DIRS[@]}"; do
        if [ ! -d "${dir}" ]; then
            echo "Error: Required directory does not exist: ${dir}"
            exit 1
        fi
    done
fi
