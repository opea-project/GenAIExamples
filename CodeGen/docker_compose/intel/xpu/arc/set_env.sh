#!/usr/bin/env bash

# Copyright (C) 2024 Intel Corporation
# SPDX-License-Identifier: Apache-2.0

### The IP address or domain name of the server on which the application is running
export HOST_IP=${HOST_IP}
export EXTERNAL_HOST_IP=${HOST_IP}

### The port of the vLLM service. On this port, the vLLM service will accept connections
export CODEGEN_VLLM_SERVICE_PORT=8028
export CODEGEN_VLLM_ENDPOINT="http://${HOST_IP}:${CODEGEN_VLLM_SERVICE_PORT}"

### A token for accessing repositories with models
export CODEGEN_HUGGINGFACEHUB_API_TOKEN=${HF_TOKEN}

### Model ID
export CODEGEN_LLM_MODEL_ID="Qwen/Qwen2.5-Coder-7B-Instruct"

### Model cache directory
export MODEL_CACHE=${MODEL_CACHE:-"./data"}

### The port of the LLM service. On this port, the LLM service will accept connections
export CODEGEN_LLM_SERVICE_PORT=9000

### The IP address or domain name of the server for CodeGen MegaService
export CODEGEN_MEGA_SERVICE_HOST_IP=${HOST_IP}

### The port for CodeGen backend service
export CODEGEN_BACKEND_SERVICE_PORT=7778

### The URL of CodeGen backend service, used by the frontend service
export CODEGEN_BACKEND_SERVICE_URL="http://${EXTERNAL_HOST_IP}:${CODEGEN_BACKEND_SERVICE_PORT}/v1/codegen"

### The endpoint of the LLM service to which requests to this service will be sent
export CODEGEN_LLM_SERVICE_HOST_IP=${HOST_IP}

### The CodeGen service UI port
export CODEGEN_UI_SERVICE_PORT=5173

### Docker registry and tag
export REGISTRY=${REGISTRY:-opea}
export TAG=${TAG:-latest}

### Intel GPU device group IDs, used to grant the vLLM container least-privilege
### access to /dev/dri without running in privileged mode. Auto-detected from the
### host; falls back to common defaults if the groups are not present.
export VIDEOGROUPID=$(getent group video | awk -F: '{print $3}')
export RENDERGROUPID=$(getent group render | awk -F: '{print $3}')
export VIDEOGROUPID=${VIDEOGROUPID:-44}
export RENDERGROUPID=${RENDERGROUPID:-109}
