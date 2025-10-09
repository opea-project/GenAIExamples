#!/bin/bash
# Copyright (C) 2024
# SPDX-License-Identifier: Apache-2.0

set -e

echo "======================================"
echo "Starting OPEA PolyLingua Service"
echo "======================================"

# Source environment variables
if [ -f .env ]; then
    echo "Loading environment from .env file..."
    export $(cat .env | grep -v '^#' | xargs)
else
    echo "ERROR: .env file not found!"
    echo "Please run './set_env.sh' first to configure environment variables."
    exit 1
fi

# Check for HuggingFace token
if [ -z "$HF_TOKEN" ]; then
    echo "WARNING: HF_TOKEN is not set!"
    echo "You may need a HuggingFace token to download models."
    read -p "Continue anyway? (y/N): " confirm
    if [[ ! $confirm =~ ^[Yy]$ ]]; then
        exit 1
    fi
fi

# Create model cache directory if it doesn't exist
mkdir -p ${MODEL_CACHE:-./data}

echo ""
echo "Starting services with docker compose..."
docker compose up -d

echo ""
echo "Waiting for services to start..."
sleep 5

echo ""
echo "======================================"
echo "Service Status"
echo "======================================"
docker compose ps

echo ""
echo "======================================"
echo "Services started successfully!"
echo "======================================"
echo ""
echo "Access points:"
echo "  - Frontend UI: http://${host_ip:-localhost}:${NGINX_PORT:-80}"
echo "  - Backend API: http://${host_ip:-localhost}:8888"
# echo "  - LLM Service: http://${host_ip:-localhost}:9000"
echo ""
# echo "To view logs:"
# echo "  docker compose logs -f"
# echo ""
echo "To stop services:"
echo "  ./deploy/stop.sh"
echo ""
