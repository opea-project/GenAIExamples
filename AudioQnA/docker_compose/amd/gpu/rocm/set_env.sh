#!/usr/bin/env bash                                                                                                           set_env.sh

# Copyright (C) 2024 Advanced Micro Devices, Inc.
# SPDX-License-Identifier: Apache-2.0


# export host_ip=<your External Public IP>    # export host_ip=$(hostname -I | awk '{print $1}')

export host_ip="192.165.1.21"
export HUGGINGFACEHUB_API_TOKEN=${YOUR_HUGGINGFACEHUB_API_TOKEN}
# <token>

export LLM_MODEL_ID=Intel/neural-chat-7b-v3-3

export MEGA_SERVICE_HOST_IP=${host_ip}
export WHISPER_SERVER_HOST_IP=${host_ip}
export SPEECHT5_SERVER_HOST_IP=${host_ip}
export LLM_SERVER_HOST_IP=${host_ip}

export WHISPER_SERVER_PORT=7066
export SPEECHT5_SERVER_PORT=7055
export LLM_SERVER_PORT=3006

export BACKEND_SERVICE_ENDPOINT=http://${host_ip}:3008/v1/audioqna
