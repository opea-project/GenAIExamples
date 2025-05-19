#!/usr/bin/env bash

# Copyright (c) 2025 Advanced Micro Devices, Inc.
# SPDX-License-Identifier: Apache-2.0

### The IP address or domain name of the server on which the application is running
# If your server is located behind a firewall or proxy, you will need to specify its external address,
# which can be used to connect to the server from the Internet. It must be specified in the EXTERNAL_HOST_IP variable.
# If the server is used only on the internal network or has a direct external address,
# specify it in HOST_IP and in EXTERNAL_HOST_IP.
export HOST_IP=${ip_address}
export EXTERNAL_HOST_IP=${ip_address}

### Model ID
export CODETRANS_LLM_MODEL_ID="Qwen/Qwen2.5-Coder-7B-Instruct"

### The port of the TGI service. On this port, the TGI service will accept connections
export CODETRANS_VLLM_SERVICE_PORT=8008

### The endpoint of the TGI service to which requests to this service will be sent (formed from previously set variables)
export CODETRANS_LLM_ENDPOINT="http://${HOST_IP}:${CODETRANS_VLLM_SERVICE_PORT}"

### A token for accessing repositories with models
export CODETRANS_HUGGINGFACEHUB_API_TOKEN=${HUGGINGFACEHUB_API_TOKEN}

### The port of the LLM service. On this port, the LLM service will accept connections
export CODETRANS_LLM_SERVICE_PORT=9000

### The IP address or domain name of the server for CodeTrans MegaService
export CODETRANS_MEGA_SERVICE_HOST_IP=${HOST_IP}

### The endpoint of the LLM service to which requests to this service will be sent
export CODETRANS_LLM_SERVICE_HOST_IP=${HOST_IP}

### The ip address of the host on which the container with the frontend service is running
export CODETRANS_FRONTEND_SERVICE_IP=${HOST_IP}

### The port of the frontend service
export CODETRANS_FRONTEND_SERVICE_PORT=5173

### Name of GenAI service for route requests to application
export CODETRANS_BACKEND_SERVICE_NAME=codetrans

### The ip address of the host on which the container with the backend service is running
export CODETRANS_BACKEND_SERVICE_IP=${HOST_IP}

### The port of the backend service
export CODETRANS_BACKEND_SERVICE_PORT=7777

### The port of the Nginx reverse proxy for application
export CODETRANS_NGINX_PORT=8088

### Endpoint of the backend service
export CODETRANS_BACKEND_SERVICE_URL="http://${EXTERNAL_HOST_IP}:${CODETRANS_BACKEND_SERVICE_PORT}/v1/codetrans"
