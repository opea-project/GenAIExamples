#!/usr/bin/env bash

# Copyright (C) 2024 Advanced Micro Devices, Inc
# SPDX-License-Identifier: Apache-2.0

export HOST_IP=${Your_host_ip_address}
export VISUALQNA_TGI_SERVICE_PORT="8399"
export VISUALQNA_HUGGINGFACEHUB_API_TOKEN=${Your_HUGGINGFACEHUB_API_TOKEN}
export VISUALQNA_CARD_ID="card1"
export VISUALQNA_RENDER_ID="renderD136"
export LVM_MODEL_ID="Xkev/Llama-3.2V-11B-cot"
export LVM_ENDPOINT="http://${HOST_IP}:8399"
export LVM_SERVICE_PORT=9399
export MEGA_SERVICE_HOST_IP=${HOST_IP}
export LVM_SERVICE_HOST_IP=${HOST_IP}
export BACKEND_SERVICE_ENDPOINT="http://${host_ip}:${BACKEND_SERVICE_PORT}/v1/visualqna"
export FRONTEND_SERVICE_IP=${HOST_IP}
export FRONTEND_SERVICE_PORT=18001
export BACKEND_SERVICE_NAME=visualqna
export BACKEND_SERVICE_IP=${HOST_IP}
export BACKEND_SERVICE_PORT=18002
export NGINX_PORT=18003
