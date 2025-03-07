#!/usr/bin/env bash

# Copyright (C) 2024 Intel Corporation
# SPDX-License-Identifier: Apache-2.0

# Remember to set your private variables mentioned in README

# host_ip, OPENAI_API_KEY, HUGGINGFACEHUB_API_TOKEN, proxies...
pushd "../../../../../" > /dev/null
source .set_env.sh
popd > /dev/null

export TEI_EMBEDDER_PORT=11633
export LLM_ENDPOINT_PORT=11634
export EMBEDDING_MODEL_ID="BAAI/bge-base-en-v1.5"
export OPENAI_EMBEDDING_MODEL="text-embedding-3-small"
export LLM_MODEL_ID="meta-llama/Meta-Llama-3.1-8B-Instruct"
export OPENAI_LLM_MODEL="gpt-4o"
export TEI_EMBEDDING_ENDPOINT="http://${host_ip}:${TEI_EMBEDDER_PORT}"
export LLM_MODEL_ID="meta-llama/Meta-Llama-3.1-8B-Instruct"
export TGI_LLM_ENDPOINT="http://${host_ip}:${LLM_ENDPOINT_PORT}"
export NEO4J_PORT1=11631
export NEO4J_PORT2=11632
export NEO4J_URI="bolt://${host_ip}:${NEO4J_PORT2}"
export NEO4J_URL="bolt://${host_ip}:${NEO4J_PORT2}"
export NEO4J_USERNAME="neo4j"
export NEO4J_PASSWORD="neo4jtest"
export DATAPREP_SERVICE_ENDPOINT="http://${host_ip}:5000/v1/dataprep/ingest"
export LOGFLAG=True
export MAX_INPUT_TOKENS=4096
export MAX_TOTAL_TOKENS=8192
export DATA_PATH="/mnt/nvme2n1/hf_cache"
export DATAPREP_PORT=11103
export RETRIEVER_PORT=11635
