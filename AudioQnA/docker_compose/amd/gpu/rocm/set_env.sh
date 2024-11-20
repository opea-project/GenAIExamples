#!/usr/bin/env bash                                                                                                           set_env.sh

# Copyright (C) 2024 Advanced Micro Devices, Inc.
# SPDX-License-Identifier: Apache-2.0


# export host_ip=<your External Public IP>    # export host_ip=$(hostname -I | awk '{print $1}')

export host_ip="192.165.1.21"
export HUGGINGFACEHUB_API_TOKEN=${YOUR_HUGGINGFACEHUB_API_TOKEN}
# <token>

export TGI_LLM_ENDPOINT=http://$host_ip:3006
export LLM_MODEL_ID=Intel/neural-chat-7b-v3-3

export ASR_ENDPOINT=http://$host_ip:7066
export TTS_ENDPOINT=http://$host_ip:7055

export MEGA_SERVICE_HOST_IP=${host_ip}
export ASR_SERVICE_HOST_IP=${host_ip}
export TTS_SERVICE_HOST_IP=${host_ip}
export LLM_SERVICE_HOST_IP=${host_ip}

export ASR_SERVICE_PORT=3001
export TTS_SERVICE_PORT=3002
export LLM_SERVICE_PORT=3007
