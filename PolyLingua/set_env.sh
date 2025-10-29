#!/bin/bash
# Copyright (C) 2024 Intel Corporation
# SPDX-License-Identifier: Apache-2.0

# Environment Setup Script for OPEA PolyLingua Service

echo "======================================"
echo "OPEA PolyLingua Service Setup"
echo "======================================"
echo ""

# Function to prompt for input with default value
prompt_with_default() {
    local prompt="$1"
    local default="$2"
    local var_name="$3"

    read -p "$prompt [$default]: " input
    input="${input:-$default}"
    export $var_name="$input"
    echo "export $var_name=\"$input\"" >> .env
}

# Remove existing .env file
rm -f .env

# Get host IP
host_ip=$(hostname -I | awk '{print $1}')
if [ -z "$host_ip" ]; then
    host_ip="localhost"
fi

echo "Detected host IP: $host_ip"
echo ""

# HuggingFace Configuration
echo "--- HuggingFace Configuration ---"
prompt_with_default "Enter your HuggingFace API Token (get from https://huggingface.co/settings/tokens)" "" "HF_TOKEN"

# Model Configuration
echo ""
echo "--- Model Configuration ---"
prompt_with_default "Enter LLM Model ID" "haoranxu/ALMA-13B" "LLM_MODEL_ID"
prompt_with_default "Enter Model Cache Directory" "./data" "MODEL_CACHE"

# Host Configuration
echo ""
echo "--- Host Configuration ---"
prompt_with_default "Enter Host IP" "$host_ip" "host_ip"

# Service Endpoints
echo ""
echo "--- Service Endpoints ---"
export VLLM_ENDPOINT="http://${host_ip}:8028"
echo "export VLLM_ENDPOINT=\"http://${host_ip}:8028\"" >> .env

export LLM_SERVICE_HOST_IP="${host_ip}"
echo "export LLM_SERVICE_HOST_IP=\"${host_ip}\"" >> .env

export LLM_SERVICE_PORT="9000"
echo "export LLM_SERVICE_PORT=\"9000\"" >> .env

export MEGA_SERVICE_HOST_IP="${host_ip}"
echo "export MEGA_SERVICE_HOST_IP=\"${host_ip}\"" >> .env

export BACKEND_SERVICE_ENDPOINT="http://${host_ip}:8888"
echo "export BACKEND_SERVICE_ENDPOINT=\"http://${host_ip}:8888\"" >> .env

export FRONTEND_SERVICE_IP="${host_ip}"
echo "export FRONTEND_SERVICE_IP=\"${host_ip}\"" >> .env

export FRONTEND_SERVICE_PORT="5173"
echo "export FRONTEND_SERVICE_PORT=\"5173\"" >> .env

export BACKEND_SERVICE_NAME="polylingua"
echo "export BACKEND_SERVICE_NAME=\"polylingua\"" >> .env

export BACKEND_SERVICE_IP="${host_ip}"
echo "export BACKEND_SERVICE_IP=\"${host_ip}\"" >> .env

export BACKEND_SERVICE_PORT="8888"
echo "export BACKEND_SERVICE_PORT=\"8888\"" >> .env

# Docker Configuration
echo ""
echo "--- Docker Configuration ---"
prompt_with_default "Enter Docker Registry" "opea" "REGISTRY"
prompt_with_default "Enter Docker Tag" "latest" "TAG"

# Nginx Configuration
prompt_with_default "Enter Nginx Port" "80" "NGINX_PORT"

# Proxy Settings (optional)
echo ""
echo "--- Proxy Settings (optional, press Enter to skip) ---"
prompt_with_default "Enter HTTP Proxy" "" "http_proxy"
prompt_with_default "Enter HTTPS Proxy" "" "https_proxy"
prompt_with_default "Enter No Proxy" "" "no_proxy"

echo ""
echo "======================================"
echo "Configuration saved to .env"
echo "======================================"
echo ""
echo "To load these environment variables, run:"
echo "  source .env"
echo ""
echo "To start the services, run:"
echo "  docker compose up -d"
echo ""
