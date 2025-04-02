#!/usr/bin/env bash

# Copyright (C) 2024 Intel Corporation
# SPDX-License-Identifier: Apache-2.0
pushd "../../" > /dev/null
source .set_env.sh
popd > /dev/null


export no_proxy="${no_proxy},${host_ip}"

export LLM_ENDPOINT_PORT=8008
export LLM_MODEL_ID="Intel/neural-chat-7b-v3-3"
export MAX_INPUT_TOKENS=1024
export MAX_TOTAL_TOKENS=2048

export LLM_PORT=9000
export LLM_ENDPOINT="http://${host_ip}:${LLM_ENDPOINT_PORT}"
export DocSum_COMPONENT_NAME="OpeaDocSumTgi"

export MEGA_SERVICE_HOST_IP=${host_ip}
export LLM_SERVICE_HOST_IP=${host_ip}
export ASR_SERVICE_HOST_IP=${host_ip}

export BACKEND_SERVICE_PORT=8888
export BACKEND_SERVICE_ENDPOINT="http://${host_ip}:${BACKEND_SERVICE_PORT}/v1/docsum"
