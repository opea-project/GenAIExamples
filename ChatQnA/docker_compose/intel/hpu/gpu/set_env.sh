#!/usr/bin/env bash

# Copyright (C) 2024 Intel Corporation
# SPDX-License-Identifier: Apache-2.0

# use OPEA v1.2 release
export TAG="1.2"

# set the name of model used for serving
export LLM_MODEL_ID=deepseek-ai/DeepSeek-R1-Distill-Qwen-32B
# set the path where locates the pre-downloaded model corresponding to the LLM_MODEL_ID
export LLM_MODEL_LOCAL_PATH=/llm/models/DeepSeek-R1-Distill-Qwen-32B

export SHM_SIZE="8g"

export DTYPE=float16
export QUANTIZATION=fp8
export MAX_MODEL_LEN=2048
export MAX_NUM_BATCHED_TOKENS=4000
export MAX_NUM_SEQS=256
export TENSOR_PARALLEL_SIZE=1

# set teh path where locates the pre-downloaded models
export EMBEDDING_MODEL_ID="/data/BAAI-bge-base-en-v1.5"
export RERANK_MODEL_ID="/data/BAAI-bge-reranker-base"
export INDEX_NAME="rag-redis"
# Set it as a non-null string, such as true, if you want to enable logging facility,
# otherwise, keep it as "" to disable it.
export LOGFLAG=""
# Set OpenTelemetry Tracing Endpoint
export JAEGER_IP=$(ip route get 8.8.8.8 | grep -oP 'src \K[^ ]+')
export OTEL_EXPORTER_OTLP_TRACES_ENDPOINT=""
export TELEMETRY_ENDPOINT=""

# Set proxy if necessary
export http_proxy=$http_proxy
export https_proxy=$https_proxy
export no_proxy=$no_proxy,chatqna-xeon-ui-server,chatqna-xeon-backend-server,dataprep-redis-service,tei-embedding-service,retriever,tei-reranking-service,vllm-service