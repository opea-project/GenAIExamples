#!/usr/bin/env bash

# Copyright (C) 2025 Intel Corporation
# Copyright (C) 2025 Advanced Micro Devices, Inc.
# SPDX-License-Identifier: Apache-2.0

host_ip=$(hostname -I | awk '{print $1}')
export host_ip

export DB_NAME="opea"
export EMBEDDING_MODEL_ID="BAAI/bge-base-en-v1.5"
export RERANK_MODEL_ID="BAAI/bge-reranker-base"
export LLM_MODEL_ID="Intel/neural-chat-7b-v3-3"
export LLM_MODEL_ID_CODEGEN="Intel/neural-chat-7b-v3-3"
export INDEX_NAME="rag-redis"
export HF_TOKEN=${HF_TOKEN}

export BACKEND_SERVICE_ENDPOINT_CHATQNA="http://${host_ip}:8888/v1/chatqna"
export DATAPREP_DELETE_FILE_ENDPOINT="http://${host_ip}:6007/v1/dataprep/delete"
export BACKEND_SERVICE_ENDPOINT_CODEGEN="http://${host_ip}:7778/v1/codegen"
export BACKEND_SERVICE_ENDPOINT_DOCSUM="http://${host_ip}:8890/v1/docsum"
export DATAPREP_SERVICE_ENDPOINT="http://${host_ip}:6007/v1/dataprep/ingest"
export DATAPREP_GET_FILE_ENDPOINT="http://${host_ip}:6007/v1/dataprep/get"
export CHAT_HISTORY_CREATE_ENDPOINT="http://${host_ip}:6012/v1/chathistory/create"
export CHAT_HISTORY_DELETE_ENDPOINT="http://${host_ip}:6012/v1/chathistory/delete"
export CHAT_HISTORY_GET_ENDPOINT="http://${host_ip}:6012/v1/chathistory/get"
export PROMPT_SERVICE_GET_ENDPOINT="http://${host_ip}:6018/v1/prompt/get"
export PROMPT_SERVICE_CREATE_ENDPOINT="http://${host_ip}:6018/v1/prompt/create"
export PROMPT_SERVICE_DELETE_ENDPOINT="http://${host_ip}:6018/v1/prompt/delete"
export KEYCLOAK_SERVICE_ENDPOINT="http://${host_ip}:8080"
export DocSum_COMPONENT_NAME="OpeaDocSumTgi"
export MEGA_SERVICE_HOST_IP=${host_ip}

# Set no proxy
export no_proxy="$no_proxy,tgi_service_codegen,llm_codegen,tei-embedding-service,tei-reranking-service,chatqna-epyc-backend-server,retriever,tgi-service,redis-vector-db,whisper,llm-docsum-tgi,docsum-epyc-backend-server,mongo,codegen"
