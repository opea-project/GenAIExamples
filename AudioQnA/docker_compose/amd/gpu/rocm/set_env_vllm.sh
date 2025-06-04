#!/usr/bin/env bash                                                                                                           set_env.sh

# Copyright (C) 2024 Advanced Micro Devices, Inc.
# SPDX-License-Identifier: Apache-2.0


# export host_ip=<your External Public IP>    # export host_ip=$(hostname -I | awk '{print $1}')

export host_ip=${ip_address}
export external_host_ip=${ip_address}
export HUGGINGFACEHUB_API_TOKEN=${HUGGINGFACEHUB_API_TOKEN}
export HF_CACHE_DIR="./data"
export LLM_MODEL_ID="Intel/neural-chat-7b-v3-3"
export VLLM_SERVICE_PORT="8081"

export MEGA_SERVICE_HOST_IP=${host_ip}
export WHISPER_SERVER_HOST_IP=${host_ip}
export SPEECHT5_SERVER_HOST_IP=${host_ip}
export LLM_SERVER_HOST_IP=${host_ip}

export WHISPER_SERVER_PORT=7066
export SPEECHT5_SERVER_PORT=7055
export LLM_SERVER_PORT=${VLLM_SERVICE_PORT}
export BACKEND_SERVICE_PORT=18038
export FRONTEND_SERVICE_PORT=18039

export BACKEND_SERVICE_ENDPOINT=http://${external_host_ip}:${BACKEND_SERVICE_PORT}/v1/audioqna
