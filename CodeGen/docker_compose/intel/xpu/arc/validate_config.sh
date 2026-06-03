#!/bin/bash
# Copyright (C) 2024 Intel Corporation
# SPDX-License-Identifier: Apache-2.0

set -e

echo "========================================"
echo "CodeGen XPU Configuration Validation"
echo "========================================"
echo ""

# Check prerequisites
echo "1. Checking prerequisites..."
echo "   - Docker version:"
docker --version || { echo "   ✗ Docker not installed"; exit 1; }

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
echo "3. Validating compose.yaml syntax..."
if command -v python3 &> /dev/null; then
    if python3 -c "import yaml; yaml.safe_load(open('compose.yaml'))" 2>&1; then
        echo "   ✓ compose.yaml syntax is valid"
    else
        echo "   ✗ compose.yaml has syntax errors"
        exit 1
    fi
else
    echo "   ⚠ Python3 not available, skipping YAML validation"
fi

echo ""
echo "4. Configuration summary:"
echo "   Services defined in compose.yaml:"
if command -v python3 &> /dev/null; then
    python3 -c "
import yaml
with open('compose.yaml') as f:
    config = yaml.safe_load(f)
    for service in config.get('services', {}).keys():
        print(f'     - {service}')
"
fi

echo ""
echo "   Port mappings:"
echo "     - vLLM Service: $CODEGEN_VLLM_SERVICE_PORT -> 80"
echo "     - LLM Service: $CODEGEN_LLM_SERVICE_PORT -> 9000"
echo "     - Backend Service: $CODEGEN_BACKEND_SERVICE_PORT -> 7778"
echo "     - UI Service: $CODEGEN_UI_SERVICE_PORT -> 5173"

echo ""
echo "   Environment endpoints:"
echo "     - vLLM Endpoint: $CODEGEN_VLLM_ENDPOINT"
echo "     - Backend URL: $CODEGEN_BACKEND_SERVICE_URL"

echo ""
echo "   Docker images to be used:"
echo "     - vLLM: intel/vllm:0.14.1-xpu"
echo "     - LLM Server: ${REGISTRY:-opea}/llm-textgen:${TAG:-latest}"
echo "     - Backend: ${REGISTRY:-opea}/codegen:${TAG:-latest}"
echo "     - UI: ${REGISTRY:-opea}/codegen-ui:${TAG:-latest}"

echo ""
echo "   Model configuration:"
echo "     - Model ID: $CODEGEN_LLM_MODEL_ID"
echo "     - Model Cache: $MODEL_CACHE"

echo ""
echo "5. XPU-specific settings:"
echo "   - VLLM_TARGET_DEVICE: xpu"
echo "   - ZE_FLAT_DEVICE_HIERARCHY: FLAT"
echo "   - ONEAPI_DEVICE_SELECTOR: level_zero:gpu;opencl:gpu"
echo "   - Device mount: /dev/dri:/dev/dri"
echo "   - GPU access: group_add (video: ${VIDEOGROUPID:-44}, render: ${RENDERGROUPID:-109})"
echo "   - Shared memory: 10g"

echo ""
echo "========================================"
echo "✓ Configuration validation passed!"
echo "========================================"
echo ""
echo "Next steps:"
echo "1. Install Docker Compose if not already installed:"
echo "   sudo apt-get update && sudo apt-get install docker-compose-plugin"
echo ""
echo "2. Ensure you have access to Intel GPU:"
echo "   sudo usermod -aG video,render \$USER"
echo "   (logout and login again)"
echo ""
echo "3. Deploy the services:"
echo "   docker compose up -d"
echo ""
echo "4. Monitor deployment:"
echo "   docker compose logs -f"
echo ""
echo "5. Test the deployment:"
echo "   curl http://\${HOST_IP}:8028/health"
echo ""
