#!/bin/bash

# Copyright (C) 2025 Advanced Micro Devices, Inc.
# Copyright (C) 2025 Intel Corporation
# SPDX-License-Identifier: Apache-2.0

# export host_ip=<your External Public IP>
host_ip=$(hostname -I | awk '{print $1}')
export host_ip

export LLM_MODEL_ID="haoranxu/ALMA-13B"
export TGI_LLM_ENDPOINT="http://${host_ip}:8008"
export HF_TOKEN=${HF_TOKEN}
export MEGA_SERVICE_HOST_IP=${host_ip}
export LLM_SERVICE_HOST_IP=${host_ip}
export BACKEND_SERVICE_ENDPOINT="http://${host_ip}:8888/v1/translation"
export NGINX_PORT=80
export FRONTEND_SERVICE_IP=${host_ip}
export FRONTEND_SERVICE_PORT=5173
export BACKEND_SERVICE_NAME=translation
export BACKEND_SERVICE_IP=${host_ip}
export BACKEND_SERVICE_PORT=8888
