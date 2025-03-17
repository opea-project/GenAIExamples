#!/usr/bin/env bash

# Copyright (C) 2024 Intel Corporation
# SPDX-License-Identifier: Apache-2.0
pushd "../../" > /dev/null
source .set_env.sh
popd > /dev/null

export host_ip=$(hostname -I | awk '{print $1}')

if [ -z "${HUGGINGFACEHUB_API_TOKEN}" ]; then
    echo "Error: HUGGINGFACEHUB_API_TOKEN is not set. Please set HUGGINGFACEHUB_API_TOKEN"
fi

if [ -z "${host_ip}" ]; then
    echo "Error: host_ip is not set. Please set host_ip first."
fi

export no_proxy=${no_proxy},${host_ip}

export LLM_MODEL_ID="Qwen/Qwen2.5-Coder-7B-Instruct"
export LLM_ENDPOINT="http://${host_ip}:8028"
export MEGA_SERVICE_HOST_IP=${host_ip}
export LLM_SERVICE_HOST_IP=${host_ip}
export BACKEND_SERVICE_ENDPOINT="http://${host_ip}:7778/v1/codegen"
export MODEL_CACHE="./data"
