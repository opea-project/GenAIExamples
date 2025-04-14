# Copyright (C) 2025 Intel Corporation
# SPDX-License-Identifier: Apache-2.0

export host_ip=${ip_address}
export DATAPREP_PORT="6007"
export TEI_EMBEDDER_PORT="10221"
export REDIS_URL_VECTOR="redis://${ip_address}:6379"
export REDIS_URL_KV="redis://${ip_address}:6380"
export LLM_MODEL=$model
export LLM_ENDPOINT="http://${ip_address}:${vllm_port}"
export DATAPREP_COMPONENT_NAME="OPEA_DATAPREP_REDIS_FINANCE"
export EMBEDDING_MODEL_ID="BAAI/bge-base-en-v1.5"
export TEI_EMBEDDING_ENDPOINT="http://${ip_address}:${TEI_EMBEDDER_PORT}"

docker compose -f dataprep_compose.yaml up -d
