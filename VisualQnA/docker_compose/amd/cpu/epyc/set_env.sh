#!/usr/bin/env bash

# Copyright (C) 2025 Advanced Micro Devices, Inc.
# Copyright (C) 2024 Intel Corporation
# SPDX-License-Identifier: Apache-2.0

host_ip=$(hostname -I | awk '{print $1}')
export host_ip

export no_proxy="$host_ip,$no_proxy"
export LVM_MODEL_ID="llava-hf/llava-v1.6-mistral-7b-hf"
export LVM_ENDPOINT="http://${host_ip}:8399"
export LVM_SERVICE_PORT=9399
export MEGA_SERVICE_HOST_IP=${host_ip}
export LVM_SERVICE_HOST_IP=${host_ip}
export BACKEND_SERVICE_ENDPOINT="http://${host_ip}:8888/v1/visualqna"
export FRONTEND_SERVICE_IP=${host_ip}
export FRONTEND_SERVICE_PORT=5173
export BACKEND_SERVICE_NAME=visualqna
export BACKEND_SERVICE_IP=${host_ip}
export BACKEND_SERVICE_PORT=8888
