#!/usr/bin/env bash

# Copyright (C) 2024 Advanced Micro Devices, Inc.
# SPDX-License-Identifier: Apache-2.0

export HOST_IP=''
export EXTERNAL_HOST_IP=''
export DOCSUM_HUGGINGFACEHUB_API_TOKEN=''
export DOCSUM_MAX_INPUT_TOKENS=2048
export DOCSUM_MAX_TOTAL_TOKENS=4096
export DOCSUM_LLM_MODEL_ID="Intel/neural-chat-7b-v3-3"
export DOCSUM_VLLM_SERVICE_PORT="8008"
export DOCSUM_LLM_ENDPOINT="http://${HOST_IP}:${DOCSUM_VLLM_SERVICE_PORT}"
export DOCSUM_WHISPER_PORT="7066"
export ASR_SERVICE_HOST_IP=${HOST_IP}
export DOCSUM_LLM_SERVER_PORT="9000"
export DOCSUM_BACKEND_SERVER_PORT="18072"
export DOCSUM_FRONTEND_PORT="18073"
export BACKEND_SERVICE_ENDPOINT="http://${EXTERNAL_HOST_IP}:${DOCSUM_BACKEND_SERVER_PORT}/v1/docsum"
