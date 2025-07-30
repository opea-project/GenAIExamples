#!/usr/bin/env bash
# Copyright (C) 2025 Advanced Micro Devices, Inc.
# Copyright (C) 2025 Intel Corporation
# SPDX-License-Identifier: Apache-2.0

# export host_ip=<your External Public IP>
host_ip=$(hostname -I | awk '{print $1}')
export host_ip

export HF_TOKEN=${HF_TOKEN}

export LLM_MODEL_ID="meta-llama/Meta-Llama-3-8B-Instruct"
export MODEL_CACHE=${model_cache:-"./data"}

export MEGA_SERVICE_HOST_IP=${host_ip}
export WHISPER_SERVER_HOST_IP=${host_ip}
export SPEECHT5_SERVER_HOST_IP=${host_ip}
export LLM_SERVER_HOST_IP=${host_ip}
export GPT_SOVITS_SERVER_HOST_IP=${host_ip}
export GPT_SOVITS_SERVER_PORT=9880
export WHISPER_SERVER_PORT=7066
export SPEECHT5_SERVER_PORT=7055
export LLM_SERVER_PORT=3006

export BACKEND_SERVICE_ENDPOINT=http://${host_ip}:3008/v1/audioqna
