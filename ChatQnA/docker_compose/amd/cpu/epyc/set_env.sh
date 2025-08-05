#!/bin/bash

# Copyright (C) 2025 Advanced Micro Devices, Inc.
# Copyright (C) 2025 Intel Corporation
# SPDX-License-Identifier: Apache-2.0

export HUGGINGFACEHUB_API_TOKEN=${HUGGINGFACEHUB_API_TOKEN}
export HF_TOKEN=${HUGGINGFACEHUB_API_TOKEN}

host_ip=$(hostname -I | awk '{print $1}')
export host_ip

export EMBEDDING_MODEL_ID="BAAI/bge-base-en-v1.5"
export RERANK_MODEL_ID="BAAI/bge-reranker-base"
export LLM_MODEL_ID="meta-llama/Meta-Llama-3-8B-Instruct"
export INDEX_NAME="rag-redis"

# Set it as a non-null string, such as true, if you want to enable logging facility,
# otherwise, keep it as "" to disable it.
export LOGFLAG=""

# Set OpenTelemetry Tracing Endpoint
JAEGER_IP=$(ip route get 8.8.8.8 | grep -oP 'src \K[^ ]+')
export JAEGER_IP
export OTEL_EXPORTER_OTLP_TRACES_ENDPOINT="grpc://${JAEGER_IP}:4317"
export TELEMETRY_ENDPOINT="http://${JAEGER_IP}:4318/v1/traces"

# Set no proxy
export no_proxy="$no_proxy,chatqna-epyc-ui-server,chatqna-epyc-backend-server,dataprep-redis-service,tei-embedding-service,retriever,tei-reranking-service,tgi-service,vllm-service,jaeger,prometheus,grafana,node-exporter,${JAEGER_IP}"

export LLM_ENDPOINT_PORT=8010
export LLM_SERVER_PORT=9000
export CHATQNA_BACKEND_PORT=8888
export CHATQNA_REDIS_VECTOR_PORT=6379
export CHATQNA_REDIS_VECTOR_INSIGHT_PORT=8001
export CHATQNA_FRONTEND_SERVICE_PORT=5173
export NGINX_PORT=80
export FAQGen_COMPONENT_NAME="OpeaFaqGenvLLM"
export LLM_ENDPOINT="http://${host_ip}:${LLM_ENDPOINT_PORT}"

# shellcheck source=./ChatQnA/docker_compose/amd/cpu/epyc/grafana/dashboards/download_opea_dashboard.sh
source "grafana/dashboards/download_opea_dashboard.sh"
