#!/usr/bin/env bash

# Copyright (C) 2024 Intel Corporation
# SPDX-License-Identifier: Apache-2.0

SCRIPT_DIR=$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" &> /dev/null && pwd)

pushd "$SCRIPT_DIR/../../../../../" > /dev/null
source .set_env.sh
popd > /dev/null

export HF_TOKEN=${HF_TOKEN}
export host_ip=${ip_address}
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
export no_proxy="$no_proxy,chatqna-xeon-ui-server,chatqna-xeon-backend-server,dataprep-redis-service,tei-embedding-service,retriever,tei-reranking-service,tgi-service,vllm-service,jaeger,prometheus,grafana,node-exporter,$JAEGER_IP"

export LLM_ENDPOINT_PORT=8010
export LLM_SERVER_PORT=9000
export CHATQNA_BACKEND_PORT=8888
export CHATQNA_REDIS_VECTOR_PORT=6379
export CHATQNA_REDIS_VECTOR_INSIGHT_PORT=8001
export CHATQNA_FRONTEND_SERVICE_PORT=5173
export NGINX_PORT=80
export FAQGen_COMPONENT_NAME="OpeaFaqGenvLLM"
export LLM_ENDPOINT="http://${host_ip}:${LLM_ENDPOINT_PORT}"
pushd "grafana/dashboards" > /dev/null
source download_opea_dashboard.sh
popd > /dev/null
declare -g numa_count=$(lscpu | grep "NUMA node(s):" | awk '{print $3}')
echo $numa_count
if (( numa_count % 2 == 0 )); then
    if (( numa_count == 6 )); then
        export TP_NUM=2
        export PP_NUM=3
    else
        export TP_NUM=$numa_count
	export PP_NUM=1
    fi
else
    export PP_NUM=$numa_count
    export TP_NUM=1
fi
export MAX_BATCHED_TOKENS=2048
export MAX_SEQS=256
