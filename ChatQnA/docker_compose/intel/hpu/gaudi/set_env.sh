#!/usr/bin/env bash

# Copyright (C) 2024 Intel Corporation
# SPDX-License-Identifier: Apache-2.0
pushd "../../../../../" > /dev/null
source .set_env.sh
popd > /dev/null


export EMBEDDING_MODEL_ID="BAAI/bge-base-en-v1.5"
export RERANK_MODEL_ID="BAAI/bge-reranker-base"
export LLM_MODEL_ID="meta-llama/Meta-Llama-3-8B-Instruct"
export INDEX_NAME="rag-redis"
export NUM_CARDS=1
# Set it as a non-null string, such as true, if you want to enable logging facility,
# otherwise, keep it as "" to disable it.
export LOGFLAG=""
# Set OpenTelemetry Tracing Endpoint
export JAEGER_IP=$(ip route get 8.8.8.8 | grep -oP 'src \K[^ ]+')
export OTEL_EXPORTER_OTLP_TRACES_ENDPOINT=grpc://$JAEGER_IP:4317
export TELEMETRY_ENDPOINT=http://$JAEGER_IP:4318/v1/traces
export no_proxy="$no_proxy,chatqna-gaudi-ui-server,chatqna-gaudi-backend-server,dataprep-redis-service,tei-embedding-service,retriever,tei-reranking-service,tgi-gaudi-server,vllm-gaudi-server,guardrails,jaeger,prometheus,grafana,node-exporter,gaudi-exporter,$JAEGER_IP"

export LLM_ENDPOINT_PORT=8010
export LLM_SERVER_PORT=9001
export CHATQNA_BACKEND_PORT=8888
export CHATQNA_REDIS_VECTOR_PORT=6379
export CHATQNA_REDIS_VECTOR_INSIGHT_PORT=8001
export CHATQNA_FRONTEND_SERVICE_PORT=5173
export NGINX_PORT=80
export FAQGen_COMPONENT_NAME="OpeaFaqGenvLLM"
export LLM_ENDPOINT="http://${host_ip}:${LLM_ENDPOINT_PORT}"
