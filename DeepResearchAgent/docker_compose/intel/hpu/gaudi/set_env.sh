#!/usr/bin/env bash

# Copyright (C) 2024 Intel Corporation
# SPDX-License-Identifier: Apache-2.0

# ==============================================================================
# Environment Configuration for DeepResearchAgent on Intel Gaudi HPU
# ==============================================================================

# Get the directory where this script is located
SCRIPT_DIR="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" &> /dev/null && pwd)"

# Source the parent environment configuration file
pushd "$SCRIPT_DIR/../../../../../" > /dev/null
source .set_env.sh
popd > /dev/null

# ------------------------------------------------------------------------------
# Helper Functions
# ------------------------------------------------------------------------------

# Validates that a required environment variable is set
check_var() {
    local var_name="$1"
    local var_value="${!var_name}"
    if [ -z "${var_value}" ]; then
        echo "Error: ${var_name} is not set. Please set ${var_name}."
        return 1  # Return error but don't exit to allow other checks to run
    fi
}

# ------------------------------------------------------------------------------
# Validate Required API Keys
# ------------------------------------------------------------------------------

check_var "HF_TOKEN"        # HuggingFace token for model access
check_var "TAVILY_API_KEY"  # Tavily API key for web search functionality

# ------------------------------------------------------------------------------
# Network Configuration
# ------------------------------------------------------------------------------

# Detect the primary IP address of the host machine
export ip_address=$(hostname -I | awk '{print $1}')
export HOST_IP=${ip_address}

# Update proxy settings to include the host IP
export no_proxy=${no_proxy},${ip_address}
export http_proxy=${http_proxy}
export https_proxy=${https_proxy}

# ------------------------------------------------------------------------------
# vLLM Service Configuration
# ------------------------------------------------------------------------------

# Port where vLLM service will be accessible
export VLLM_PORT="${VLLM_PORT:-8000}"

# ------------------------------------------------------------------------------
# Language Model Configuration
# ------------------------------------------------------------------------------

# LLM model to use for the Deep Research Agent
# See supported models and tool call parsers at:
# https://docs.vllm.ai/en/stable/features/tool_calling/#automatic-function-calling
export LLM_MODEL_ID="${LLM_MODEL_ID:-meta-llama/Llama-3.3-70B-Instruct}"

# Parser for handling function/tool calls (must match the model)
export TOOL_CALL_PARSER="${TOOL_CALL_PARSER:-llama3_json}"

# Maximum sequence length for model context (131072 = ~128K tokens)
export MAX_LEN="${MAX_LEN:-131072}"

# Number of Gaudi accelerator cards to use
export NUM_CARDS="${NUM_CARDS:-4}"

# Directory for caching HuggingFace models
export HF_CACHE_DIR="${HF_CACHE_DIR:-"./data"}"

# OpenAI-compatible API endpoint URL for vLLM
export OPENAI_BASE_URL="http://${ip_address}:${VLLM_PORT}/v1"

# ------------------------------------------------------------------------------
# API Keys and Authentication
# ------------------------------------------------------------------------------

export HF_TOKEN="${HF_TOKEN}"              # HuggingFace authentication token
export OPENAI_API_KEY="empty-api-key"      # Placeholder for vLLM compatibility
export TAVILY_API_KEY="${TAVILY_API_KEY}"  # Tavily search API key

# ------------------------------------------------------------------------------
# Deep Research Agent Configuration
# ------------------------------------------------------------------------------

# Maximum number of research units that can run concurrently
export MAX_CONCURRENT_RESEARCH_UNITS="${MAX_CONCURRENT_RESEARCH_UNITS:-3}"

# Maximum iterations per researcher before stopping
export MAX_RESEARCHER_ITERATIONS="${MAX_RESEARCHER_ITERATIONS:-3}"

# Custom instructions for agent behavior (leave empty for defaults)
export RESEARCHER_INSTRUCTIONS=""               # Instructions for individual researchers
export RESEARCH_WORKFLOW_INSTRUCTIONS=""        # Instructions for overall research workflow
export SUBAGENT_DELEGATION_INSTRUCTIONS=""      # Instructions for task delegation between agents