#!/usr/bin/env bash

# Copyright (C) 2024 Intel Corporation
# SPDX-License-Identifier: Apache-2.0

host_ip=$(hostname -I | awk '{print $1}')

export MEGA_SERVICE_HOST_IP=${host_ip}
export EMBEDDING_SERVICE_HOST_IP=${host_ip}
export RETRIEVER_SERVICE_HOST_IP=${host_ip}
export RERANK_SERVICE_HOST_IP=${host_ip}
export LVM_SERVICE_HOST_IP=${host_ip}

export LVM_ENDPOINT="http://${host_ip}:9009"
export BACKEND_SERVICE_ENDPOINT="http://${host_ip}:8888/v1/videoqna"
export BACKEND_HEALTH_CHECK_ENDPOINT="http://${host_ip}:8888/v1/health_check"
export DATAPREP_SERVICE_ENDPOINT="http://${host_ip}:6007/v1/dataprep"
export DATAPREP_GET_FILE_ENDPOINT="http://${host_ip}:6007/v1/dataprep/get_file"
export DATAPREP_GET_VIDEO_LIST_ENDPOINT="http://${host_ip}:6007/v1/dataprep/get_videos"

export VDMS_HOST=${host_ip}
export VDMS_PORT=8001
export INDEX_NAME="mega-videoqna"
export USECLIP=1
export LLM_DOWNLOAD="True" # Set to "False" before redeploy LVM server to avoid model download
