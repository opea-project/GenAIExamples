#!/usr/bin/env bash

# Copyright (C) 2024 Advanced Micro Devices, Inc.
# SPDX-License-Identifier: Apache-2.0

export HOST_IP=''
export EXTERNAL_HOST_IP=''
export FAQGEN_LLM_MODEL_ID="meta-llama/Meta-Llama-3-8B-Instruct"
export FAQGEN_TGI_SERVICE_PORT=8883
export FAQGEN_LLM_SERVER_PORT=9001
export FAQGEN_HUGGINGFACEHUB_API_TOKEN=${HUGGINGFACEHUB_API_TOKEN}
export FAQGEN_BACKEND_SERVER_PORT=18074
export FAQGEN_BACKEND_ENDPOINT="http://${EXTERNAL_HOST_IP}:${FAQGEN_BACKEND_SERVER_PORT}/v1/faqgen"
export FAGGEN_UI_PORT=18075
