#!/usr/bin/env bash

# Copyright (C) 2024 Intel Corporation
# SPDX-License-Identifier: Apache-2.0
SCRIPT_DIR=$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" &> /dev/null && pwd)

pushd "$SCRIPT_DIR/../../../../../" > /dev/null
source .set_env.sh
popd > /dev/null

# Download Grafana configurations
pushd "${SCRIPT_DIR}/grafana/dashboards" > /dev/null
source download_opea_dashboard.sh
popd > /dev/null

export host_ip=$(hostname -I | awk '{print $1}')
# Set network proxy settings
export no_proxy="${no_proxy},${host_ip},vllm-service,tgi-llava-xeon-server,visualqna-xeon-backend-server,opea_prometheus,grafana,node-exporter,$JAEGER_IP" # Example: no_proxy="localhost, 127.0.0.1, 192.168.1.1"
export LVM_MODEL_ID="llava-hf/llava-v1.6-mistral-7b-hf"
export LVM_ENDPOINT="http://${host_ip}:8399"
export LVM_SERVICE_PORT=9399
export MEGA_SERVICE_HOST_IP=${host_ip}
export LVM_SERVICE_HOST_IP=${host_ip}
export BACKEND_SERVICE_ENDPOINT="http://${host_ip}:8888/v1/visualqna"
export FRONTEND_SERVICE_IP=${host_ip}
export FRONTEND_SERVICE_PORT=5173
export BACKEND_SERVICE_NAME=visualqna
export BACKEND_SERVICE_IP=${host_ip}
export BACKEND_SERVICE_PORT=8888
