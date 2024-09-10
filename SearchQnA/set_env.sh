#!/usr/bin/env bash

# Copyright (C) 2024 Intel Corporation
# SPDX-License-Identifier: Apache-2.0


export EMBEDDING_MODEL_ID=BAAI/bge-base-en-v1.5
export TEI_EMBEDDING_ENDPOINT=http://${host_ip}:3001
export RERANK_MODEL_ID=BAAI/bge-reranker-base
export TEI_RERANKING_ENDPOINT=http://${host_ip}:3004

export TGI_LLM_ENDPOINT=http://${host_ip}:3006
export LLM_MODEL_ID=Intel/neural-chat-7b-v3-3

export MEGA_SERVICE_HOST_IP=${host_ip}
export EMBEDDING_SERVICE_HOST_IP=${host_ip}
export WEB_RETRIEVER_SERVICE_HOST_IP=${host_ip}
export RERANK_SERVICE_HOST_IP=${host_ip}
export LLM_SERVICE_HOST_IP=${host_ip}

export EMBEDDING_SERVICE_PORT=3002
export WEB_RETRIEVER_SERVICE_PORT=3003
export RERANK_SERVICE_PORT=3005
export LLM_SERVICE_PORT=3007
