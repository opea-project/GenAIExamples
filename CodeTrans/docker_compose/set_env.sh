#!/usr/bin/env bash

# Copyright (C) 2024 Intel Corporation
# SPDX-License-Identifier: Apache-2.0
pushd "../../" > /dev/null
source .set_env.sh
popd > /dev/null


export LLM_MODEL_ID="mistralai/Mistral-7B-Instruct-v0.3"
export TGI_LLM_ENDPOINT="http://${host_ip}:8008"
export MEGA_SERVICE_HOST_IP=${host_ip}
export LLM_SERVICE_HOST_IP=${host_ip}
export BACKEND_SERVICE_ENDPOINT="http://${host_ip}:7777/v1/codetrans"
export FRONTEND_SERVICE_IP=${host_ip}
export FRONTEND_SERVICE_PORT=5173
export BACKEND_SERVICE_NAME=codetrans
export BACKEND_SERVICE_IP=${host_ip}
export BACKEND_SERVICE_PORT=7777
