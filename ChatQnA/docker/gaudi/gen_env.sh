#!/usr/bin/env bash

# Copyright (C) 2024 Intel Corporation
# SPDX-License-Identifier: Apache-2.0

# Get the public ip for the host which the UI will need to communicate with the backend.
public_ip=$(curl ifconfig.me)

# Get the users huggingface api token
hf_api_token=""
prompt="Entry your huggingface API token (hf_****): "
while IFS= read -p "$prompt" -r -s -n 1 char
do
    if [[ $char == $'\0' ]]
    then
        break
    fi
    prompt="*"
    hf_api_token+="$char"
done

tee .env <<EOF
# Model info
EMBEDDING_MODEL_ID="BAAI/bge-base-en-v1.5"
RERANK_MODEL_ID="BAAI/bge-reranker-base"
LLM_MODEL_ID="Intel/neural-chat-7b-v3-3"

# Huggingface token used to download the model if needed
HUGGINGFACEHUB_API_TOKEN=${hf_api_token}

# The internal docker endpoints addresses
# If you were running components on different nodes you may need to specify the internal IP addresses
TEI_EMBEDDING_ENDPOINT="http://tei-embedding-service:80"
TEI_RERANKING_ENDPOINT="http://tei-reranking-service:80"
TGI_LLM_ENDPOINT="http://tgi-service:80"
REDIS_URL="redis://redis-vector-db:6379"
INDEX_NAME="rag-redis"
MEGA_SERVICE_HOST_IP=localhost
EMBEDDING_SERVICE_HOST_IP=embedding
RETRIEVER_SERVICE_HOST_IP=retriever
RERANK_SERVICE_HOST_IP=reranking
LLM_SERVICE_HOST_IP=llm

# Used by the client UI to access backend services
BACKEND_SERVICE_ENDPOINT="http://${public_ip}:8888/v1/chatqna"
DATAPREP_SERVICE_ENDPOINT="http://${public_ip}:6007/v1/dataprep"
DATAPREP_GET_FILE_ENDPOINT="http://${public_ip}:6007/v1/dataprep/get_file"
DATAPREP_DELETE_FILE_ENDPOINT="http://${public_ip}:6007/v1/dataprep/delete_file"
EOF
