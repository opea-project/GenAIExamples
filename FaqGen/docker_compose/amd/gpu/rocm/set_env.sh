#!/usr/bin/env bash

# Copyright (C) 2024 Advanced Micro Devices, Inc.
# SPDX-License-Identifier: Apache-2.0

export FAQGEN_LLM_MODEL_ID="meta-llama/Meta-Llama-3-8B-Instruct"
export FAQGEN_TGI_SERVICE_IMAGE="ghcr.io/huggingface/text-generation-inference:2.3.1-rocm"
export HOST_IP=${host_ip}
export FAQGEN_CARD_ID="card0"
export FAQGEN_RENDER_ID="renderD128"
export FAQGEN_TGI_SERVICE_PORT=8883
export FAQGEN_LLM_SERVER_PORT=9001
export FAQGEN_HUGGINGFACEHUB_API_TOKEN=${your_hf_api_token}
export FAQGEN_BACKEND_SERVER_PORT=8881
export FAGGEN_UI_PORT=5174
