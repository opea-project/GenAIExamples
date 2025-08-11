#!/bin/bash

# Copyright (C) 2025 Advanced Micro Devices, Inc.
# Copyright (C) 2025 Intel Corporation
# SPDX-License-Identifier: Apache-2.0

host_ip=$(hostname -I | awk '{print $1}')
export host_ip

export LLM_MODEL_ID="Qwen/Qwen2.5-Coder-7B-Instruct"
export LLM_ENDPOINT="http://${host_ip}:8008"
export LLM_COMPONENT_NAME="OpeaTextGenService"
export MODEL_CACHE=${model_cache:-"./data"}
export NUM_CARDS=1
export BLOCK_SIZE=128
export MAX_NUM_SEQS=256
export MAX_SEQ_LEN_TO_CAPTURE=2048
export MEGA_SERVICE_HOST_IP=${host_ip}
export LLM_SERVICE_HOST_IP=${host_ip}
export BACKEND_SERVICE_ENDPOINT="http://${host_ip}:7777/v1/codetrans"
export FRONTEND_SERVICE_IP=${host_ip}
export FRONTEND_SERVICE_PORT=5173
export BACKEND_SERVICE_NAME=codetrans
export BACKEND_SERVICE_IP=${host_ip}
export BACKEND_SERVICE_PORT=7777
export NGINX_PORT=${NGINX_PORT:-80}
