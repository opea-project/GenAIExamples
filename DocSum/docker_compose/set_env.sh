#!/usr/bin/env bash

# Copyright (C) 2024 Intel Corporation
# SPDX-License-Identifier: Apache-2.0


export HUGGINGFACEHUB_API_TOKEN=""
export host_ip=$(hostname -I | awk '{print $1}')
export ip_address=$(hostname -I | awk '{print $1}')
export no_proxy="${no_proxy},${host_ip}"

export LLM_MODEL_ID="Intel/neural-chat-7b-v3-3"
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




# export ASR_ENDPOINT=http://$host_ip:7066
# export ASR_SERVICE_HOST_IP=${host_ip}
# export ASR_SERVICE_PORT=9099 # 3001
