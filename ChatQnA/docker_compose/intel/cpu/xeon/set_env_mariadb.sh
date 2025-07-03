#!/usr/bin/env bash

# Copyright (C) 2025 MariaDB Foundation
# SPDX-License-Identifier: Apache-2.0

SCRIPT_DIR=$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" &> /dev/null && pwd)

pushd "$SCRIPT_DIR/../../../../../" > /dev/null
source .set_env.sh
popd > /dev/null

if [ -z "${HF_TOKEN}" ]; then
    echo "Error: HF_TOKEN is not set. Please set HF_TOKEN."
fi

export host_ip=$(hostname -I | awk '{print $1}')
export MARIADB_DATABASE="vectordb"
export MARIADB_USER="chatqna"
export MARIADB_PASSWORD="password"
export HF_TOKEN=${HF_TOKEN}
export EMBEDDING_MODEL_ID="BAAI/bge-base-en-v1.5"
export RERANK_MODEL_ID="BAAI/bge-reranker-base"
export LLM_MODEL_ID="meta-llama/Meta-Llama-3-8B-Instruct"
export LOGFLAG=""
export no_proxy="$no_proxy,chatqna-xeon-ui-server,chatqna-xeon-backend-server,dataprep-redis-service,tei-embedding-service,retriever,tei-reranking-service,tgi-service,vllm-service,jaeger,prometheus,grafana,node-exporter"
export LLM_SERVER_PORT=9000
export NGINX_PORT=80
