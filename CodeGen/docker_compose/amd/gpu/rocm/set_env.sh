#!/usr/bin/env bash

# Copyright (C) 2024 Intel Corporation
# SPDX-License-Identifier: Apache-2.0

### The IP address or domain name of the server on which the application is running
export HOST_IP=direct-supercomputer1.powerml.co

### The port of the TGI service. On this port, the TGI service will accept connections
export CODEGEN_TGI_SERVICE_PORT=8028

### A token for accessing repositories with models
export CODEGEN_HUGGINGFACEHUB_API_TOKEN=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

### Model ID
export CODEGEN_LLM_MODEL_ID="Qwen/Qwen2.5-Coder-7B-Instruct"

### The port of the LLM service. On this port, the LLM service will accept connections
export CODEGEN_LLM_SERVICE_PORT=9000

### The endpoint of the TGI service to which requests to this service will be sent (formed from previously set variables)
export CODEGEN_TGI_LLM_ENDPOINT="http://${HOST_IP}:${CODEGEN_TGI_SERVICE_PORT}"

### The IP address or domain name of the server for CodeGen MegaService
export CODEGEN_MEGA_SERVICE_HOST_IP=${HOST_IP}

### The port for CodeGen backend service
export CODEGEN_BACKEND_SERVICE_PORT=18150

### The URL of CodeGen backend service, used by the frontend service
export CODEGEN_BACKEND_SERVICE_URL="http://${HOST_IP}:${CODEGEN_BACKEND_SERVICE_PORT}/v1/codegen"

### The endpoint of the LLM service to which requests to this service will be sent
export CODEGEN_LLM_SERVICE_HOST_IP=${HOST_IP}

### The CodeGen service UI port
export CODEGEN_UI_SERVICE_PORT=18151
