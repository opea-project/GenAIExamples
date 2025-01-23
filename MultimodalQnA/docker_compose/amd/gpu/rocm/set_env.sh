#!/usr/bin/env bash

# Copyright (C) 2024 Advanced Micro Devices, Inc.
# SPDX-License-Identifier: Apache-2.0

export HOST_IP=${your_host_ip_address}
export MULTIMODAL_HUGGINGFACEHUB_API_TOKEN=${your_huggingfacehub_token}
export MULTIMODAL_TGI_SERVICE_PORT="8399"
export no_proxy=${your_no_proxy}
export http_proxy=${your_http_proxy}
export https_proxy=${your_http_proxy}
export BRIDGE_TOWER_EMBEDDING=true
export EMBEDDER_PORT=6006
export MMEI_EMBEDDING_ENDPOINT="http://${HOST_IP}:$EMBEDDER_PORT"
export MM_EMBEDDING_PORT_MICROSERVICE=6000
export REDIS_URL="redis://${HOST_IP}:6379"
export REDIS_HOST=${HOST_IP}
export INDEX_NAME="mm-rag-redis"
export LLAVA_SERVER_PORT=8399
export LVM_ENDPOINT="http://${HOST_IP}:8399"
export EMBEDDING_MODEL_ID="BridgeTower/bridgetower-large-itm-mlm-itc"
export LVM_MODEL_ID="Xkev/Llama-3.2V-11B-cot"
export WHISPER_MODEL="base"
export MM_EMBEDDING_SERVICE_HOST_IP=${HOST_IP}
export MM_RETRIEVER_SERVICE_HOST_IP=${HOST_IP}
export LVM_SERVICE_HOST_IP=${HOST_IP}
export MEGA_SERVICE_HOST_IP=${HOST_IP}
export BACKEND_SERVICE_ENDPOINT="http://${HOST_IP}:8888/v1/multimodalqna"
export DATAPREP_INGEST_SERVICE_ENDPOINT="http://${HOST_IP}:6007/v1/dataprep/ingest"
export DATAPREP_GEN_TRANSCRIPT_SERVICE_ENDPOINT="http://${HOST_IP}:6007/v1/dataprep/generate_transcripts"
export DATAPREP_GEN_CAPTION_SERVICE_ENDPOINT="http://${HOST_IP}:6007/v1/dataprep/generate_captions"
export DATAPREP_GET_FILE_ENDPOINT="http://${HOST_IP}:6007/v1/dataprep/get"
export DATAPREP_DELETE_FILE_ENDPOINT="http://${HOST_IP}:6007/v1/dataprep/delete"
