#!/usr/bin/env bash

# Copyright (C) 2025 Intel Corporation
# SPDX-License-Identifier: Apache-2.0

SCRIPT_DIR=$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" &> /dev/null && pwd)

pushd "$SCRIPT_DIR/../../../" > /dev/null
source .set_env.sh
popd > /dev/null

export HOST_IP=$(hostname -I | awk '{print $1}')
export host_ip=${HOST_IP}
export HF_TOKEN=${HF_TOKEN}
if [ -z "${HF_TOKEN}" ]; then
    echo "Error: HF_TOKEN is not set. Please set HF_TOKEN"
    exit 1
fi

if [ -z "${HOST_IP}" ]; then
    echo "Error: HOST_IP is not set. Please set HOST_IP first."
    exit 1
fi

export no_proxy=${no_proxy},${HOST_IP}
export http_proxy=${http_proxy}
export https_proxy=${https_proxy}

# LLM Configuration
export LLM_MODEL_ID="Qwen/Qwen2.5-Coder-7B-Instruct"
export LLM_SERVICE_PORT=9000
export LLM_ENDPOINT="http://${HOST_IP}:8028"
export LLM_SERVICE_HOST_IP=${HOST_IP}
export TGI_LLM_ENDPOINT="http://${HOST_IP}:8028"

# Megaservice Configuration
export MEGA_SERVICE_PORT=7778
export MEGA_SERVICE_HOST_IP=${HOST_IP}
export BACKEND_SERVICE_ENDPOINT="http://${HOST_IP}:7778/v1/codegen"

# openGauss Configuration
export GS_USER="gaussdb"
export GS_PASSWORD="openGauss@123"
export GS_DB="postgres"
export GS_PORT=5432
export GS_CONNECTION_STRING="opengauss+psycopg2://${GS_USER}:${GS_PASSWORD}@${HOST_IP}:${GS_PORT}/${GS_DB}"

# Retriever Configuration (openGauss)
export RETRIEVER_PORT=7000
export RETRIEVAL_SERVICE_HOST_IP=${HOST_IP}
export RETRIEVER_COMPONENT_NAME="OPEA_RETRIEVER_OPENGAUSS"

# Dataprep Configuration (openGauss)
export DATAPREP_OPENGAUSS_PORT=6007
export DATAPREP_ENDPOINT="http://${HOST_IP}:${DATAPREP_OPENGAUSS_PORT}/v1/dataprep"

# Embedding Configuration
export EMBEDDING_MODEL_ID="BAAI/bge-base-en-v1.5"
export EMBEDDER_PORT=6000
export TEI_EMBEDDER_PORT=8090
export TEI_EMBEDDING_HOST_IP=${HOST_IP}
export TEI_EMBEDDING_ENDPOINT="http://${HOST_IP}:${TEI_EMBEDDER_PORT}"

# General Configuration
export LOGFLAG=false
export MODEL_CACHE=${model_cache:-"./data"}
export NUM_CARDS=1

# Set network proxy settings
export no_proxy="${no_proxy},${HOST_IP},vllm-server,codegen-xeon-backend-server,codegen-xeon-ui-server,opengauss-db,dataprep-opengauss-server,tei-embedding-serving,tei-embedding-server,retriever-opengauss-server"
export http_proxy=$http_proxy
export https_proxy=$https_proxy
