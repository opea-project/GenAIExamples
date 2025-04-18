#!/usr/bin/env bash

# Copyright (C) 2024 Intel Corporation
# Copyright (c) 2024 Advanced Micro Devices, Inc.
# SPDX-License-Identifier: Apache-2.0

### The IP address or domain name of the server on which the application is running
export HOST_IP=''
export EXTERNAL_HOST_IP=''

### The port of the TGI service. On this port, the TGI service will accept connections
export CODEGEN_TGI_SERVICE_PORT=8028

### A token for accessing repositories with models
export CODEGEN_HUGGINGFACEHUB_API_TOKEN=${HUGGINGFACEHUB_API_TOKEN}

### Model ID
export CODEGEN_LLM_MODEL_ID="Qwen/Qwen2.5-Coder-7B-Instruct"

### The port of the LLM service. On this port, the LLM service will accept connections
export CODEGEN_LLM_SERVICE_PORT=9000

### The endpoint of the TGI service to which requests to this service will be sent (formed from previously set variables)
export CODEGEN_TGI_LLM_ENDPOINT="http://${HOST_IP}:${CODEGEN_TGI_SERVICE_PORT}"

### The IP address or domain name of the server for CodeGen MegaService
export CODEGEN_MEGA_SERVICE_HOST_IP=${HOST_IP}

### The port for CodeGen backend service
export CODEGEN_BACKEND_SERVICE_PORT=18150

### The URL of CodeGen backend service, used by the frontend service
export CODEGEN_BACKEND_SERVICE_URL="http://${EXTERNAL_HOST_IP}:${CODEGEN_BACKEND_SERVICE_PORT}/v1/codegen"

### The endpoint of the LLM service to which requests to this service will be sent
export CODEGEN_LLM_SERVICE_HOST_IP=${HOST_IP}

### The CodeGen service UI port
export CODEGEN_UI_SERVICE_PORT=18151


export REDIS_DB_PORT=6379
export REDIS_INSIGHTS_PORT=8001
export REDIS_RETRIEVER_PORT=7000
export REDIS_URL="redis://${host_ip}:${REDIS_DB_PORT}"
export RETRIEVAL_SERVICE_HOST_IP=${host_ip}
export RETRIEVER_COMPONENT_NAME="OPEA_RETRIEVER_REDIS"
export INDEX_NAME="CodeGen"

export EMBEDDING_MODEL_ID="BAAI/bge-base-en-v1.5"
export EMBEDDER_PORT=6000
export TEI_EMBEDDER_PORT=8090
export TEI_EMBEDDING_HOST_IP=${host_ip}
export TEI_EMBEDDING_ENDPOINT="http://${host_ip}:${TEI_EMBEDDER_PORT}"

export DATAPREP_REDIS_PORT=6007
export DATAPREP_ENDPOINT="http://${host_ip}:${DATAPREP_REDIS_PORT}/v1/dataprep"
export LOGFLAG=false
export MODEL_CACHE="./data"
export NUM_CARDS=1
