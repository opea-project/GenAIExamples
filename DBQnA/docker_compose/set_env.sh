#!/usr/bin/env bash

# Copyright (C) 2024 Intel Corporation
# SPDX-License-Identifier: Apache-2.0
pushd "../../" > /dev/null
source .set_env.sh
popd > /dev/null

if [ -z "$HF_TOKEN" ]; then
    echo "Error: The HF_TOKEN environment variable is **NOT** set. Please set it"
    return -1
fi

export TGI_PORT=8008
export TGI_LLM_ENDPOINT="http://${your_ip}:${TGI_PORT}"
export LLM_MODEL_ID="mistralai/Mistral-7B-Instruct-v0.3"
