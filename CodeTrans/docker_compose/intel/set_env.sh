#!/usr/bin/env bash

# Copyright (C) 2024 Intel Corporation
# SPDX-License-Identifier: Apache-2.0
SCRIPT_DIR=$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" &> /dev/null && pwd)

pushd "$SCRIPT_DIR/../../../" > /dev/null
source .set_env.sh
popd > /dev/null


export LLM_MODEL_ID="mistralai/Mistral-7B-Instruct-v0.3"
export LLM_ENDPOINT="http://${host_ip}:8008"
export LLM_COMPONENT_NAME="OpeaTextGenService"
export NUM_CARDS=1
export BLOCK_SIZE=128
export MAX_NUM_SEQS=256
export MAX_SEQ_LEN_TO_CAPTURE=2048
export MEGA_SERVICE_HOST_IP=${host_ip}
export LLM_SERVICE_HOST_IP=${host_ip}
export BACKEND_SERVICE_ENDPOINT="http://${host_ip}:7777/v1/codetrans"
export FRONTEND_SERVICE_IP=${host_ip}
export FRONTEND_SERVICE_PORT=5173
export BACKEND_SERVICE_NAME=codetrans
export BACKEND_SERVICE_IP=${host_ip}
export BACKEND_SERVICE_PORT=7777
