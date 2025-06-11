#!/usr/bin/env bash

# Copyright (C) 2024 Intel Corporation
# SPDX-License-Identifier: Apache-2.0
pushd "../../../../../" > /dev/null
source .set_env.sh
popd > /dev/null

export MODEL_PATH=${MODEL_PATH}
export DOC_PATH=${DOC_PATH}
export UI_TMPFILE_PATH=${UI_TMPFILE_PATH}
export HOST_IP=${HOST_IP}
export LLM_MODEL=${LLM_MODEL}
export HF_ENDPOINT=${HF_ENDPOINT}
export vLLM_ENDPOINT=${vLLM_ENDPOINT}
export HF_TOKEN=${HF_TOKEN}
export no_proxy="localhost, 127.0.0.1, 192.168.1.1"
export UI_UPLOAD_PATH=${UI_UPLOAD_PATH}
export LLM_MODEL_PATH=${LLM_MODEL_PATH}
export NGINX_PORT_0=${NGINX_PORT_0}
export NGINX_PORT_1=${NGINX_PORT_1}
export VLLM_SERVICE_PORT_0=${VLLM_SERVICE_PORT_0}
export VLLM_SERVICE_PORT_1=${VLLM_SERVICE_PORT_1}
export TENSOR_PARALLEL_SIZE=${TENSOR_PARALLEL_SIZE}
export NGINX_CONFIG_PATH=${NGINX_CONFIG_PATH}
export SELECTED_XPU_0=${SELECTED_XPU_0}
export SELECTED_XPU_1=${SELECTED_XPU_1}
export vLLM_ENDPOINT=${vLLM_ENDPOINT}
