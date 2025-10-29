#!/usr/bin/env bash

# Copyright (C) 2024 Intel Corporation
# SPDX-License-Identifier: Apache-2.0

SCRIPT_DIR=$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" &> /dev/null && pwd)

pushd "$SCRIPT_DIR/../../../../../" > /dev/null
source .set_env.sh
popd > /dev/null

export host_ip=$(hostname -I | awk '{print $1}') # Example: host_ip="192.168.1.1"
export HF_TOKEN=${HF_TOKEN}

export LLM_ENDPOINT_PORT=8008
export LLM_MODEL_ID="meta-llama/Meta-Llama-3-8B-Instruct"

export BLOCK_SIZE=128
export MAX_NUM_SEQS=256
export MAX_SEQ_LEN_TO_CAPTURE=2048
export NUM_CARDS=1
export MAX_INPUT_TOKENS=1024
export MAX_TOTAL_TOKENS=2048

export LLM_PORT=9000
export LLM_ENDPOINT="http://${host_ip}:${LLM_ENDPOINT_PORT}"
export ASR_SERVICE_PORT=7066
export DocSum_COMPONENT_NAME="OpeaDocSumvLLM" # OpeaDocSumTgi
export FRONTEND_SERVICE_PORT=5173
export MEGA_SERVICE_HOST_IP=${host_ip}
export LLM_SERVICE_HOST_IP=${host_ip}
export ASR_SERVICE_HOST_IP=${host_ip}

export BACKEND_SERVICE_PORT=8888
export BACKEND_SERVICE_ENDPOINT="http://${host_ip}:${BACKEND_SERVICE_PORT}/v1/docsum"

export LOGFLAG=True

export NUM_CARDS=1
export BLOCK_SIZE=128
export MAX_NUM_SEQS=256
export MAX_SEQ_LEN_TO_CAPTURE=2048

# Download Grafana configurations
pushd "${SCRIPT_DIR}/grafana/dashboards" > /dev/null
source download_opea_dashboard.sh
popd > /dev/null

# Set network proxy settings
export no_proxy="${no_proxy},${host_ip},docsum-gaudi-vllm-service,docsum-gaudi-tgi-server,docsum-gaudi-backend-server,gaudi-metrics-exporter,opea_prometheus,grafana,node-exporter,$JAEGER_IP" # Example: no_proxy="localhost, 127.0.0.1, 192.168.1.1"
export http_proxy=$http_proxy
export https_proxy=$https_proxy
