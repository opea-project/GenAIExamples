#!/bin/bash
# Copyright (C) 2024
# SPDX-License-Identifier: Apache-2.0

set -e

echo "======================================"
echo "Testing OPEA PolyLingua Service"
echo "======================================"

# Source environment variables
if [ -f .env ]; then
    export $(cat .env | grep -v '^#' | xargs)
fi

HOST=${host_ip:-localhost}
PORT=${BACKEND_SERVICE_PORT:-8888}

echo ""
echo "Testing translation endpoint..."
echo "Target: http://${HOST}:${PORT}/v1/translation"
echo ""

response=$(curl -s -w "\n%{http_code}" -X POST "http://${HOST}:${PORT}/v1/translation" \
  -H "Content-Type: application/json" \
  -d '{
    "language_from": "English",
    "language_to": "Spanish",
    "source_language": "Hello, how are you today?"
  }')

http_code=$(echo "$response" | tail -n1)
body=$(echo "$response" | head -n-1)

echo "HTTP Status: $http_code"
echo ""

if [ "$http_code" -eq 200 ]; then
    echo "✓ PolyLingua service is working!"
    echo ""
    echo "Response:"
    echo "$body" | jq '.' 2>/dev/null || echo "$body"
else
    echo "✗ PolyLingua service returned an error!"
    echo ""
    echo "Response:"
    echo "$body"
    exit 1
fi

echo ""
echo "======================================"
echo "Test completed successfully!"
echo "======================================"
