#!/usr/bin/env bash

# Copyright (C) 2024 Intel Corporation
# SPDX-License-Identifier: Apache-2.0

# Navigate to the parent directory and source the environment
SCRIPT_DIR=$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" &> /dev/null && pwd)

pushd "$SCRIPT_DIR/../../../../../" > /dev/null
source .set_env.sh
popd > /dev/null

# Function to check if a variable is set
check_var() {
    if [ "$#" -ne 1 ]; then
        echo "Error: Usage: check_var <ENV_VARIABLE_NAME>" >&2
        return 2
    fi

    local var_name="$1"
    if [ -n "${!var_name}" ]; then
        # Variable value is non-empty
        return 0
    else
        # Variable is unset or set to an empty string
        return 1
    fi
}

check_var "HF_TOKEN"
export ip_address=$(hostname -I | awk '{print $1}')

export LLM_ENDPOINT_PORT="${LLM_ENDPOINT_PORT:-8008}"
export LLM_ENDPOINT="http://${ip_address}:${LLM_ENDPOINT_PORT}"
export DATA_PATH="${DATA_PATH-"./data"}"
export LLM_MODEL_ID="${LLM_MODEL_ID-"Qwen/Qwen2.5-VL-32B-Instruct"}"
export MAX_TOTAL_TOKENS="${MAX_TOTAL_TOKENS-12288}"
export NUM_CARDS="${NUM_CARDS-4}"
