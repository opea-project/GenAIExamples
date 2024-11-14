#!/usr/bin/env bash

# Copyright (C) 2024 Advanced Micro Devices, Inc.

export HOST_IP=direct-supercomputer1.powerml.co
export CODETRANS_LLM_MODEL_ID="Qwen/Qwen2.5-Coder-7B-Instruct"
export CODETRANS_TGI_SERVICE_PORT=18156
export CODETRANS_TGI_LLM_ENDPOINT="http://${HOST_IP}:${CODETRANS_TGI_SERVICE_PORT}"
export CODETRANS_HUGGINGFACEHUB_API_TOKEN=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
export CODETRANS_LLM_SERVICE_PORT=18157
export CODETRANS_MEGA_SERVICE_HOST_IP=${HOST_IP}
export CODETRANS_LLM_SERVICE_HOST_IP=${HOST_IP}
export CODETRANS_FRONTEND_SERVICE_IP=192.165.1.21
export CODETRANS_FRONTEND_SERVICE_PORT=18155
export CODETRANS_BACKEND_SERVICE_NAME=codetrans
export CODETRANS_BACKEND_SERVICE_IP=192.165.1.21
export CODETRANS_BACKEND_SERVICE_PORT=18154
export CODETRANS_NGINX_PORT=18153
export CODETRANS_BACKEND_SERVICE_URL="http://${HOST_IP}:${CODETRANS_BACKEND_SERVICE_PORT}/v1/codetrans"
