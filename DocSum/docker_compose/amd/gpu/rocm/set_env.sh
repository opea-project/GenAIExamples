#!/usr/bin/env bash

# Copyright (C) 2024 Advanced Micro Devices, Inc.
# SPDX-License-Identifier: Apache-2.0

export MAX_INPUT_TOKENS=2048
export MAX_TOTAL_TOKENS=4096
export DOCSUM_TGI_IMAGE="ghcr.io/huggingface/text-generation-inference:2.3.1-rocm"
export DOCSUM_LLM_MODEL_ID="Intel/neural-chat-7b-v3-3"
export HOST_IP=${host_ip}
export DOCSUM_TGI_SERVICE_PORT="8008"
export DOCSUM_TGI_LLM_ENDPOINT="http://${HOST_IP}:${DOCSUM_TGI_SERVICE_PORT}"
export DOCSUM_HUGGINGFACEHUB_API_TOKEN=${your_hf_api_token}
export DOCSUM_LLM_SERVER_PORT="9000"
export DOCSUM_BACKEND_SERVER_PORT="8888"
export DOCSUM_FRONTEND_PORT="5173"
export BACKEND_SERVICE_ENDPOINT="http://${HOST_IP}:${DOCSUM_BACKEND_SERVER_PORT}/v1/docsum"
