#!/bin/bash
# Copyright (C) 2024
# SPDX-License-Identifier: Apache-2.0

set -e

echo "======================================"
echo "Building OPEA Translation Service Images"
echo "======================================"

# Source environment variables
if [ -f .env ]; then
    echo "Loading environment from .env file..."
    export $(cat .env | grep -v '^#' | xargs)
else
    echo "Warning: .env file not found. Using default values."
    echo "Run './set_env.sh' to configure environment variables."
fi

# Build translation backend
echo ""
echo "Building translation backend service..."
docker build --no-cache -t ${REGISTRY:-opea}/translation:${TAG:-latest} -f Dockerfile .

# Build translation UI
echo ""
echo "Building translation UI service..."
docker build --no-cache \
  --build-arg BACKEND_SERVICE_ENDPOINT=${BACKEND_SERVICE_ENDPOINT} \
  -t ${REGISTRY:-opea}/translation-ui:${TAG:-latest} \
  -f ui/Dockerfile ./ui

echo ""
echo "======================================"
echo "Build completed successfully!"
echo "======================================"
echo ""
echo "Images built:"
echo "  - ${REGISTRY:-opea}/translation:${TAG:-latest}"
echo "  - ${REGISTRY:-opea}/translation-ui:${TAG:-latest}"
echo ""
echo "To start the services, run:"
echo "  ./deploy/start.sh"
echo ""
