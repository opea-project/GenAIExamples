#!/bin/bash
# Copyright (C) 2024
# SPDX-License-Identifier: Apache-2.0

set -e

echo "======================================"
echo "Building OPEA PolyLingua Service Images"
echo "======================================"

# Source environment variables
if [ -f .env ]; then
    echo "Loading environment from .env file..."
    export $(cat .env | grep -v '^#' | xargs)
else
    echo "Warning: .env file not found. Using default values."
    echo "Run './set_env.sh' to configure environment variables."
fi

# Build polylingua backend
echo ""
echo "Building polylingua backend service..."
docker build --no-cache -t ${REGISTRY:-opea}/polylingua:${TAG:-latest} -f Dockerfile .

# Build polylingua UI
echo ""
echo "Building polylingua UI service..."
docker build --no-cache \
  --build-arg BACKEND_SERVICE_ENDPOINT=${BACKEND_SERVICE_ENDPOINT} \
  -t ${REGISTRY:-opea}/polylingua-ui:${TAG:-latest} \
  -f ui/Dockerfile ./ui

echo ""
echo "======================================"
echo "Build completed successfully!"
echo "======================================"
echo ""
echo "Images built:"
echo "  - ${REGISTRY:-opea}/polylingua:${TAG:-latest}"
echo "  - ${REGISTRY:-opea}/polylingua-ui:${TAG:-latest}"
echo ""
echo "To start the services, run:"
echo "  ./deploy/start.sh"
echo ""
