#!/usr/bin/env bash

# Copyright (C) 2025 Advanced Micro Devices, Inc.
# Copyright (C) 2025 Intel Corporation
# SPDX-License-Identifier: Apache-2.0

host_ip=$(hostname -I | awk '{print $1}')
export host_ip # Example: host_ip="192.168.1.1"

export no_proxy="${no_proxy},${host_ip}" # Example: no_proxy="localhost,127.0.0.1,192.168.1.1"
export http_proxy=$http_proxy
export https_proxy=$https_proxy
export HF_TOKEN=${HF_TOKEN}

export LLM_ENDPOINT_PORT=8008
export LLM_MODEL_ID="mistralai/Mistral-7B-Instruct-v0.2"
export MAX_INPUT_TOKENS=1024
export MAX_TOTAL_TOKENS=2048

export LLM_PORT=9000
export LLM_SERVICE_PORT=9000
export LLM_ENDPOINT="http://${host_ip}:${LLM_ENDPOINT_PORT}"
export OPEA_ARB_POSTHEARING_ASSISTANT_COMPONENT_NAME="OpeaArbPostHearingAssistantTgi" # OpeaArbPostHearingAssistantVllm
export FRONTEND_SERVICE_PORT=5173
export MEGA_SERVICE_HOST_IP=${host_ip}
export LLM_SERVICE_HOST_IP=${host_ip}

export BACKEND_SERVICE_PORT=8888
export BACKEND_SERVICE_ENDPOINT="http://${host_ip}:${BACKEND_SERVICE_PORT}/v1/arb-post-hearing"

export LOGFLAG=True
export MODEL_CACHE=${model_cache:-"./data"}

export NUM_CARDS=1
export BLOCK_SIZE=128
export MAX_NUM_SEQS=256
export MAX_SEQ_LEN_TO_CAPTURE=2048
