#!/usr/bin/env bash

# SPDX-License-Identifier: Apache-2.0

export SEARCH_HOST_IP='192.165.1.21'
export SEARCH_EXTERNAL_HOST_IP='direct-supercomputer1.powerml.co'
export SEARCH_EMBEDDING_MODEL_ID='BAAI/bge-base-en-v1.5'
export SEARCH_TEI_EMBEDDING_ENDPOINT=http://${SEARCH_HOST_IP}:3001
export SEARCH_RERANK_MODEL_ID='BAAI/bge-reranker-base'
export SEARCH_TEI_RERANKING_ENDPOINT=http://${SEARCH_HOST_IP}:3004
export SEARCH_HUGGINGFACEHUB_API_TOKEN='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'

export SEARCH_TGI_LLM_ENDPOINT=http://${SEARCH_HOST_IP}:3006
export SEARCH_LLM_MODEL_ID='Intel/neural-chat-7b-v3-3'

export SEARCH_MEGA_SERVICE_HOST_IP=${SEARCH_EXTERNAL_HOST_IP}
export SEARCH_EMBEDDING_SERVICE_HOST_IP=${SEARCH_HOST_IP}
export SEARCH_WEB_RETRIEVER_SERVICE_HOST_IP=${SEARCH_HOST_IP}
export SEARCH_RERANK_SERVICE_HOST_IP=${SEARCH_HOST_IP}
export SEARCH_LLM_SERVICE_HOST_IP=${SEARCH_HOST_IP}

export SEARCH_EMBEDDING_SERVICE_PORT=3002
export SEARCH_WEB_RETRIEVER_SERVICE_PORT=3003
export SEARCH_RERANK_SERVICE_PORT=3005
export SEARCH_LLM_SERVICE_PORT=3007

export SEARCH_FRONTEND_SERVICE_PORT=18143
export SEARCH_BACKEND_SERVICE_PORT=18142
export SEARCH_BACKEND_SERVICE_ENDPOINT=http://${SEARCH_EXTERNAL_HOST_IP}:${SEARCH_BACKEND_SERVICE_PORT}/v1/searchqna

export SEARCH_GOOGLE_API_KEY='AIzaSyA8elfT2YWgF8OzGOLDJNATchMPaInzdLg'
export SEARCH_GOOGLE_CSE_ID='a2f12a53bdfc04a8a'
