#!/bin/bash
# Copyright (C) 2024 Intel Corporation
# SPDX-License-Identifier: Apache-2.0

set -e

echo "========================================"
echo "CodeGen XPU Deployment Test"
echo "========================================"
echo ""

# Check prerequisites
echo "1. Checking prerequisites..."
echo "   - Docker version:"
docker --version

echo "   - Intel GPU devices:"
if [ -d "/dev/dri" ] && ls -la /dev/dri/ | grep -qE "card|render"; then
    ls -la /dev/dri/ | grep -E "card|render"
    echo "   ✓ Intel GPU devices found"
else
    echo "   ✗ /dev/dri not found - Intel GPU may not be available"
    exit 1
fi

echo ""
echo "2. Checking environment variables..."
if [ -z "$HOST_IP" ]; then
    echo "   ✗ HOST_IP not set"
    exit 1
else
    echo "   ✓ HOST_IP: $HOST_IP"
fi

if [ -z "$HF_TOKEN" ]; then
    echo "   ✗ HF_TOKEN not set"
    exit 1
else
    echo "   ✓ HF_TOKEN is set (${#HF_TOKEN} characters)"
fi

if [ -z "$CODEGEN_LLM_MODEL_ID" ]; then
    echo "   ✗ CODEGEN_LLM_MODEL_ID not set"
    exit 1
else
    echo "   ✓ Model: $CODEGEN_LLM_MODEL_ID"
fi

echo ""
echo "3. Validating Docker Compose configuration..."
if command -v docker-compose &> /dev/null; then
    COMPOSE_CMD="docker-compose"
elif docker compose version &> /dev/null; then
    COMPOSE_CMD="docker compose"
else
    echo "   ✗ Neither 'docker-compose' nor 'docker compose' found"
    exit 1
fi

echo "   Using: $COMPOSE_CMD"
if $COMPOSE_CMD config > /dev/null 2>&1; then
    echo "   ✓ Docker Compose configuration is valid"
else
    echo "   ✗ Docker Compose configuration has errors"
    exit 1
fi

echo ""
echo "4. Checking Docker Compose services..."
$COMPOSE_CMD config --services
echo ""

echo "5. Summary of configuration:"
echo "   - vLLM Service Port: $CODEGEN_VLLM_SERVICE_PORT"
echo "   - LLM Service Port: $CODEGEN_LLM_SERVICE_PORT"
echo "   - Backend Service Port: $CODEGEN_BACKEND_SERVICE_PORT"
echo "   - UI Service Port: $CODEGEN_UI_SERVICE_PORT"
echo "   - Model Cache: $MODEL_CACHE"
echo ""

echo "========================================"
echo "Deployment configuration is valid!"
echo "========================================"
echo ""
echo "To deploy, run:"
echo "  $COMPOSE_CMD up -d"
echo ""
echo "To monitor logs:"
echo "  $COMPOSE_CMD logs -f"
echo ""
echo "To test vLLM service after deployment:"
echo "  curl http://\${HOST_IP}:8028/health"
echo ""
