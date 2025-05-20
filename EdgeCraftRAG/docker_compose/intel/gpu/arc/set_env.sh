#!/usr/bin/env bash

# Copyright (C) 2024 Intel Corporation
# SPDX-License-Identifier: Apache-2.0
pushd "../../../../../" > /dev/null
source .set_env.sh
popd > /dev/null

export MODEL_PATH=${MODEL_PATH}
export DOC_PATH=${DOC_PATH}
export UI_TMPFILE_PATH=${UI_TMPFILE_PATH}
export HOST_IP=${HOST_IP}
export LLM_MODEL=${LLM_MODEL}
export HF_ENDPOINT=${HF_ENDPOINT}
export vLLM_ENDPOINT=${vLLM_ENDPOINT}
export HUGGINGFACEHUB_API_TOKEN=${HUGGINGFACEHUB_API_TOKEN}
export no_proxy="localhost, 127.0.0.1, 192.168.1.1"
