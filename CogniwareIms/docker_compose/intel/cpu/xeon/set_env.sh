#!/bin/bash
# Copyright (C) 2024 Intel Corporation
# SPDX-License-Identifier: Apache-2.0

# Environment setup script for Cogniware IMS on Intel Xeon

# HuggingFace Configuration
export HUGGINGFACEHUB_API_TOKEN=${HUGGINGFACEHUB_API_TOKEN:-""}

# Model Configuration
export LLM_MODEL_ID=${LLM_MODEL_ID:-"Intel/neural-chat-7b-v3-3"}
export EMBEDDING_MODEL_ID=${EMBEDDING_MODEL_ID:-"BAAI/bge-base-en-v1.5"}
export RERANK_MODEL_ID=${RERANK_MODEL_ID:-"BAAI/bge-reranker-base"}

# Database
export POSTGRES_PASSWORD=${POSTGRES_PASSWORD:-"postgres"}

# Proxy Settings
export http_proxy=${http_proxy:-""}
export https_proxy=${https_proxy:-""}
export no_proxy=${no_proxy:-"localhost,127.0.0.1"}

echo "Environment variables set for Cogniware IMS deployment on Intel Xeon"
