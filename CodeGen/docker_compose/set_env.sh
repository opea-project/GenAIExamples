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

export host_ip=$(hostname -I | awk '{print $1}')
export LLM_MODEL_ID="Qwen/Qwen2.5-Coder-7B-Instruct"
export TGI_LLM_ENDPOINT="http://${host_ip}:8028"
export MEGA_SERVICE_HOST_IP=${host_ip}
export LLM_SERVICE_HOST_IP=${host_ip}
export BACKEND_SERVICE_ENDPOINT="http://${host_ip}:7778/v1/codegen"
