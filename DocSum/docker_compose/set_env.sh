#!/usr/bin/env bash

# Copyright (C) 2024 Intel Corporation
# SPDX-License-Identifier: Apache-2.0
pushd "../../" > /dev/null
source .set_env.sh
popd > /dev/null

export MAX_INPUT_TOKENS=1024
export MAX_TOTAL_TOKENS=2048

export no_proxy="${no_proxy},${host_ip}"
export TGI_LLM_ENDPOINT="http://${host_ip}:8008"
export MEGA_SERVICE_HOST_IP=${host_ip}
export LLM_SERVICE_HOST_IP=${host_ip}
export BACKEND_SERVICE_ENDPOINT="http://${host_ip}:8888/v1/docsum"

export V2A_SERVICE_HOST_IP=${host_ip}
export V2A_ENDPOINT=http://$host_ip:7078

export A2T_ENDPOINT=http://$host_ip:7066
export A2T_SERVICE_HOST_IP=${host_ip}
export A2T_SERVICE_PORT=9099

export DATA_ENDPOINT=http://$host_ip:7079
export DATA_SERVICE_HOST_IP=${host_ip}
export DATA_SERVICE_PORT=7079
