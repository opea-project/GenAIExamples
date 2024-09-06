#!/usr/bin/env bash

# Copyright (C) 2024 Intel Corporation
# SPDX-License-Identifier: Apache-2.0

export no_proxy=${your_no_proxy}
export http_proxy=${your_http_proxy}
export https_proxy=${your_http_proxy}
export EMBEDDER_PORT=6006
export MMEI_EMBEDDING_ENDPOINT="http://${host_ip}:$EMBEDDER_PORT/v1/encode"
export REDIS_URL="redis://${host_ip}:6379"
export INDEX_NAME="mm-rag-redis"
export LLAVA_SERVER_PORT=8399
export LVM_ENDPOINT="http://${host_ip}:8399/v1/lvm"
export EMBEDDING_MODEL_ID="BridgeTower/bridgetower-large-itm-mlm-itc"
export WHISPER_MODEL="base"
