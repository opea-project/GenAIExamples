#!/usr/bin/env bash

# Copyright (C) 2024 Intel Corporation
# SPDX-License-Identifier: Apache-2.0
pushd "../../../../../" > /dev/null
source .set_env.sh
popd > /dev/null

export host_ip=$(hostname -I | awk '{print $1}')

export MM_EMBEDDING_SERVICE_HOST_IP=${host_ip}
export MM_RETRIEVER_SERVICE_HOST_IP=${host_ip}
export LVM_SERVICE_HOST_IP=${host_ip}
export MEGA_SERVICE_HOST_IP=${host_ip}

export no_proxy=${your_no_proxy}
export http_proxy=${your_http_proxy}
export https_proxy=${your_http_proxy}

export REDIS_DB_PORT=6379
export REDIS_INSIGHTS_PORT=8001
export REDIS_URL="redis://${host_ip}:${REDIS_DB_PORT}"
export REDIS_HOST=${host_ip}
export INDEX_NAME="mm-rag-redis"

export WHISPER_MODEL="base"
export WHISPER_PORT=7066
export WHISPER_SERVER_ENDPOINT="http://${host_ip}:${WHISPER_PORT}/v1/asr"
export MAX_IMAGES=1

export DATAPREP_MMR_PORT=6007
export DATAPREP_INGEST_SERVICE_ENDPOINT="http://${host_ip}:${DATAPREP_MMR_PORT}/v1/dataprep/ingest"
export DATAPREP_GEN_TRANSCRIPT_SERVICE_ENDPOINT="http://${host_ip}:${DATAPREP_MMR_PORT}/v1/dataprep/generate_transcripts"
export DATAPREP_GEN_CAPTION_SERVICE_ENDPOINT="http://${host_ip}:${DATAPREP_MMR_PORT}/v1/dataprep/generate_captions"
export DATAPREP_GET_FILE_ENDPOINT="http://${host_ip}:${DATAPREP_MMR_PORT}/v1/dataprep/get"
export DATAPREP_DELETE_FILE_ENDPOINT="http://${host_ip}:${DATAPREP_MMR_PORT}/v1/dataprep/delete"

export EMM_BRIDGETOWER_PORT=6006
export EMBEDDING_MODEL_ID="BridgeTower/bridgetower-large-itm-mlm-itc"
export MMEI_EMBEDDING_ENDPOINT="http://${host_ip}:$EMM_BRIDGETOWER_PORT"
export MM_EMBEDDING_PORT_MICROSERVICE=6000
export BRIDGE_TOWER_EMBEDDING=true

export REDIS_RETRIEVER_PORT=7000

export LVM_PORT=9399
export LLAVA_SERVER_PORT=8399
export TGI_GAUDI_PORT="${LLAVA_SERVER_PORT}:80"
export LVM_MODEL_ID="llava-hf/llava-v1.6-vicuna-13b-hf"

export LVM_ENDPOINT="http://${host_ip}:${LLAVA_SERVER_PORT}"

export MEGA_SERVICE_PORT=8888
export BACKEND_SERVICE_ENDPOINT="http://${host_ip}:${MEGA_SERVICE_PORT}/v1/multimodalqna"

export UI_PORT=5173
