#!/usr/bin/env bash

# Copyright (C) 2024 Intel Corporation
# SPDX-License-Identifier: Apache-2.0
pushd "../../../../../" > /dev/null
source .set_env.sh
popd > /dev/null

host_ip=$(hostname -I | awk '{print $1}')

export HF_TOKEN=${HF_TOKEN}

export INDEX_NAME="mega-videoqna"
export LLM_DOWNLOAD="True" # Set to "False" before redeploy LVM server to avoid model download
export RERANK_COMPONENT_NAME="OPEA_VIDEO_RERANKING"
export LVM_COMPONENT_NAME="OPEA_VIDEO_LLAMA_LVM"
export EMBEDDING_COMPONENT_NAME="OPEA_CLIP_EMBEDDING"
export USECLIP=1
export LOGFLAG=True

export EMBEDDING_SERVICE_HOST_IP=${host_ip}
export LVM_SERVICE_HOST_IP=${host_ip}
export MEGA_SERVICE_HOST_IP=${host_ip}
export RERANK_SERVICE_HOST_IP=${host_ip}
export RETRIEVER_SERVICE_HOST_IP=${host_ip}
export VDMS_HOST=${host_ip}

export BACKEND_PORT=8888
export DATAPREP_PORT=6007
export EMBEDDER_PORT=6990
export MULTIMODAL_CLIP_EMBEDDER_PORT=6991
export LVM_PORT=9399
export RERANKING_PORT=8000
export RETRIEVER_PORT=7000
export UI_PORT=5173
export VDMS_PORT=8001
export VIDEO_LLAMA_PORT=9009

export BACKEND_HEALTH_CHECK_ENDPOINT="http://${host_ip}:${BACKEND_PORT}/v1/health_check"
export BACKEND_SERVICE_ENDPOINT="http://${host_ip}:${BACKEND_PORT}/v1/videoqna"
export CLIP_EMBEDDING_ENDPOINT="http://${host_ip}:${MULTIMODAL_CLIP_EMBEDDER_PORT}"
export DATAPREP_GET_FILE_ENDPOINT="http://${host_ip}:${DATAPREP_PORT}/v1/dataprep/get"
export DATAPREP_GET_VIDEO_LIST_ENDPOINT="http://${host_ip}:${DATAPREP_PORT}/v1/dataprep/get_videos"
export DATAPREP_INGEST_SERVICE_ENDPOINT="http://${host_ip}:${DATAPREP_PORT}/v1/dataprep/ingest_videos"
export EMBEDDING_ENDPOINT="http://${host_ip}:${EMBEDDER_PORT}/v1/embeddings"
export FRONTEND_ENDPOINT="http://${host_ip}:${UI_PORT}/_stcore/health"
export LVM_ENDPOINT="http://${host_ip}:${VIDEO_LLAMA_PORT}"
export LVM_VIDEO_ENDPOINT="http://${host_ip}:${VIDEO_LLAMA_PORT}/generate"
export RERANKING_ENDPOINT="http://${host_ip}:${RERANKING_PORT}/v1/reranking"
export RETRIEVER_ENDPOINT="http://${host_ip}:${RETRIEVER_PORT}/v1/retrieval"
export TEI_RERANKING_ENDPOINT="http://${host_ip}:${TEI_RERANKING_PORT}"
export UI_ENDPOINT="http://${host_ip}:${UI_PORT}/_stcore/health"

export no_proxy="${NO_PROXY},${host_ip},vdms-vector-db,dataprep-vdms-server,clip-embedding-server,reranking-tei-server,retriever-vdms-server,lvm-video-llama,lvm,videoqna-xeon-backend-server,videoqna-xeon-ui-server"
