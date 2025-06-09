#!/usr/bin/env bash

# Copyright (C) 2024 Intel Corporation
# SPDX-License-Identifier: Apache-2.0

export host_ip=$(hostname -I | awk '{print $1}')
export HF_TOKEN=${HF_TOKEN}

export EMBEDDING_MODEL_ID="BAAI/bge-base-en-v1.5"
export RERANK_MODEL_ID="BAAI/bge-reranker-base"
export LLM_MODEL_ID="meta-llama/Meta-Llama-3-8B-Instruct"
export INDEX_NAME="rag-redis"
# Set it as a non-null string, such as true, if you want to enable logging facility,
# otherwise, keep it as "" to disable it.
export LOGFLAG=""
# Set OpenTelemetry Tracing Endpoint
export JAEGER_IP=$(ip route get 8.8.8.8 | grep -oP 'src \K[^ ]+')
export OTEL_EXPORTER_OTLP_TRACES_ENDPOINT=grpc://$JAEGER_IP:4317
export TELEMETRY_ENDPOINT=http://$JAEGER_IP:4318/v1/traces
# Set no proxy
export no_proxy="$no_proxy,hybridrag-gaudi-ui-server,hybridrag-gaudi-backend-server,dataprep-redis-service,tei-embedding-service,retriever,tei-reranking-service,tgi-service,vllm-service,jaeger,prometheus,grafana,node-exporter,localhost,127.0.0.1,$JAEGER_IP,${host_ip}"


export MEGA_SERVICE_HOST_IP=${host_ip}
export EMBEDDING_SERVER_HOST_IP=${host_ip}
export RETRIEVER_SERVER_HOST_IP=${host_ip}
export RERANK_SERVER_HOST_IP=${host_ip}
export LLM_SERVER_HOST_IP=${host_ip}
export TEXT2CYPHER_SERVER_HOST_IP=${host_ip}
export REDIS_SERVER_HOST_IP=${host_ip}

export MEGA_SERVICE_PORT=8888
export EMBEDDING_SERVER_PORT=6006
export RETRIEVER_SERVER_PORT=7000
export RERANK_SERVER_PORT=8808
export LLM_SERVER_PORT=9009
export TEXT2CYPHER_SERVER_PORT=11801
export REDIS_SERVER_PORT=6379

export LLM_ENDPOINT_PORT=8010
export LLM_ENDPOINT="http://${host_ip}:${LLM_ENDPOINT_PORT}"
export HYBRIDRAG_REDIS_VECTOR_PORT=6379
export HYBRIDRAG_REDIS_VECTOR_INSIGHT_PORT=8001
export HYBRIDRAG_FRONTEND_SERVICE_PORT=5173
export HYBRIDRAG_BACKEND_SERVICE_ENDPOINT=http://${host_ip}:8888/v1/hybridrag
export NGINX_PORT=80
export FAQGen_COMPONENT_NAME="OpeaFaqGenvLLM"

export NEO4J_PORT1=7474
export NEO4J_PORT2=7687
export NEO4J_URI="bolt://${host_ip}:${NEO4J_PORT2}"
export NEO4J_URL="bolt://${host_ip}:${NEO4J_PORT2}"
export NEO4J_USERNAME="neo4j"
export NEO4J_PASSWORD="neo4jtest"
export LOGFLAG=True
