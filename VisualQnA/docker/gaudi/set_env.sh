#!/usr/bin/env bash

# Copyright (C) 2024 Intel Corporation
# SPDX-License-Identifier: Apache-2.0

export LVM_MODEL_ID="llava-hf/llava-v1.6-mistral-7b-hf"
export LVM_ENDPOINT="http://${host_ip}:8399"
export LVM_SERVICE_PORT=9399
export MEGA_SERVICE_HOST_IP=${host_ip}
export LVM_SERVICE_HOST_IP=${host_ip}
export BACKEND_SERVICE_ENDPOINT="http://${host_ip}:8888/v1/visualqna"
