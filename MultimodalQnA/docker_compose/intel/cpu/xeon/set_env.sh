#!/usr/bin/env bash

# Copyright (C) 2024 Intel Corporation
# SPDX-License-Identifier: Apache-2.0
pushd "../../../../../" > /dev/null
source .set_env.sh
popd > /dev/null

export no_proxy=${your_no_proxy}
export http_proxy=${your_http_proxy}
export https_proxy=${your_http_proxy}
export EMBEDDER_PORT=6006
export MMEI_EMBEDDING_ENDPOINT="http://${host_ip}:$EMBEDDER_PORT"
export MM_EMBEDDING_PORT_MICROSERVICE=6000
export WHISPER_SERVER_PORT=7066
export WHISPER_SERVER_ENDPOINT="http://${host_ip}:${WHISPER_SERVER_PORT}/v1/asr"
export REDIS_URL="redis://${host_ip}:6379"
export REDIS_HOST=${host_ip}
export INDEX_NAME="mm-rag-redis"
export BRIDGE_TOWER_EMBEDDING=true
export LLAVA_SERVER_PORT=8399
export LVM_ENDPOINT="http://${host_ip}:8399"
export EMBEDDING_MODEL_ID="BridgeTower/bridgetower-large-itm-mlm-itc"
export LVM_MODEL_ID="llava-hf/llava-1.5-7b-hf"
export WHISPER_MODEL="base"
export MM_EMBEDDING_SERVICE_HOST_IP=${host_ip}
export MM_RETRIEVER_SERVICE_HOST_IP=${host_ip}
export LVM_SERVICE_HOST_IP=${host_ip}
export MEGA_SERVICE_HOST_IP=${host_ip}
export BACKEND_SERVICE_ENDPOINT="http://${host_ip}:8888/v1/multimodalqna"
export DATAPREP_INGEST_SERVICE_ENDPOINT="http://${host_ip}:5000/v1/dataprep/ingest"
export DATAPREP_GEN_TRANSCRIPT_SERVICE_ENDPOINT="http://${host_ip}:5000/v1/dataprep/generate_transcripts"
export DATAPREP_GEN_CAPTION_SERVICE_ENDPOINT="http://${host_ip}:5000/v1/dataprep/generate_captions"
export DATAPREP_GET_FILE_ENDPOINT="http://${host_ip}:5000/v1/dataprep/get"
export DATAPREP_DELETE_FILE_ENDPOINT="http://${host_ip}:5000/v1/dataprep/delete"
