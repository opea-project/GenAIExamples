#!/bin/bash
# Copyright (C) 2024 Intel Corporation
# SPDX-License-Identifier: Apache-2.0

set -e

# Calculate WORKPATH - handle both local and CI environments
# If run from tests/ directory: WORKPATH = parent directory
# If run from root: WORKPATH = current directory
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
echo "SCRIPT_DIR: $SCRIPT_DIR"

# Try multiple path detection strategies
WORKPATH=""
if [ -f "$SCRIPT_DIR/../cogniwareims.py" ]; then
    # We're in the CogniwareIms directory structure
    WORKPATH="$(cd "$SCRIPT_DIR/.." && pwd)"
    echo "Found cogniwareims.py at parent: $WORKPATH"
elif [ -f "$SCRIPT_DIR/../../CogniwareIms/cogniwareims.py" ]; then
    # We're in GenAIExamples/CogniwareIms/tests
    WORKPATH="$(cd "$SCRIPT_DIR/../.." && pwd)/CogniwareIms"
    echo "Found cogniwareims.py at grandparent/CogniwareIms: $WORKPATH"
elif [ -d "$SCRIPT_DIR/../docker_compose/intel/cpu/xeon" ]; then
    # We're in tests/, parent has docker_compose
    WORKPATH="$(cd "$SCRIPT_DIR/.." && pwd)"
    echo "Found docker_compose at parent: $WORKPATH"
elif [ -d "$SCRIPT_DIR/../../CogniwareIms/docker_compose/intel/cpu/xeon" ]; then
    # We're in GenAIExamples/CogniwareIms/tests
    WORKPATH="$(cd "$SCRIPT_DIR/../.." && pwd)/CogniwareIms"
    echo "Found docker_compose at grandparent/CogniwareIms: $WORKPATH"
else
    # Fallback: assume we're in the example directory
    WORKPATH="$(cd "$SCRIPT_DIR/.." && pwd)"
    echo "Using fallback WORKPATH: $WORKPATH"
fi

LOG_PATH="$WORKPATH/tests"

# Verify WORKPATH by checking for docker_compose directory
echo "WORKPATH: $WORKPATH"
echo "Verifying WORKPATH..."
if [ ! -d "$WORKPATH/docker_compose/intel/cpu/xeon" ] && [ ! -d "$WORKPATH/CogniwareIms/docker_compose/intel/cpu/xeon" ]; then
    echo "ERROR: docker_compose/intel/cpu/xeon not found in WORKPATH"
    echo "WORKPATH: $WORKPATH"
    echo "Looking for: $WORKPATH/docker_compose/intel/cpu/xeon"
    echo "Or: $WORKPATH/CogniwareIms/docker_compose/intel/cpu/xeon"
    echo "Available directories in WORKPATH:"
    ls -la "$WORKPATH" 2>/dev/null | head -20 || echo "Cannot list WORKPATH"
    exit 1
fi
echo "WORKPATH verified successfully"

# Get IP address with fallback to localhost
if command -v hostname >/dev/null 2>&1; then
    ip_address=$(hostname -I | awk '{print $1}' 2>/dev/null || echo "127.0.0.1")
else
    ip_address="127.0.0.1"
fi

# If IP address is empty or invalid, use localhost
if [ -z "$ip_address" ] || [ "$ip_address" = "" ]; then
    ip_address="127.0.0.1"
fi

echo "Using IP address: $ip_address"

# Helper function to wait for service with timeout
wait_for_service() {
    local url=$1
    local service_name=$2
    local max_attempts=${3:-30}
    local attempt=0

    echo "Waiting for $service_name..."
    while [ $attempt -lt $max_attempts ]; do
        if curl -s -f "$url" > /dev/null 2>&1; then
            echo "$service_name is ready!"
            return 0
        fi
        attempt=$((attempt + 1))
        echo "Waiting for $service_name... (attempt $attempt/$max_attempts)"
        sleep 10
    done

    echo "ERROR: $service_name failed to become ready after $((max_attempts * 10)) seconds"
    return 1
}

function build_docker_images() {
    echo "Building Docker images..."
    local build_dir=""
    if [ -d "$WORKPATH/docker_image_build" ]; then
        build_dir="$WORKPATH/docker_image_build"
    elif [ -d "$WORKPATH/CogniwareIms/docker_image_build" ]; then
        build_dir="$WORKPATH/CogniwareIms/docker_image_build"
    else
        echo "ERROR: docker_image_build directory not found"
        exit 1
    fi

    cd "$build_dir"
    echo "Building from: $(pwd)"
    echo "Verifying build context..."
    if [ ! -f "../backend/Dockerfile" ]; then
        echo "ERROR: backend/Dockerfile not found relative to build directory"
        echo "Current directory: $(pwd)"
        echo "Expected: $(pwd)/../backend/Dockerfile"
        exit 1
    fi
    if [ ! -f "../frontend/Dockerfile" ]; then
        echo "ERROR: frontend/Dockerfile not found relative to build directory"
        echo "Current directory: $(pwd)"
        echo "Expected: $(pwd)/../frontend/Dockerfile"
        exit 1
    fi
    echo "Build context verified. Starting build..."
    docker compose -f build.yaml build
}

function start_services() {
    echo "Starting Cogniware IMS services on Intel Xeon..."
    local compose_dir=""
    if [ -d "$WORKPATH/docker_compose/intel/cpu/xeon" ]; then
        compose_dir="$WORKPATH/docker_compose/intel/cpu/xeon"
    elif [ -d "$WORKPATH/CogniwareIms/docker_compose/intel/cpu/xeon" ]; then
        compose_dir="$WORKPATH/CogniwareIms/docker_compose/intel/cpu/xeon"
    else
        echo "ERROR: docker_compose/intel/cpu/xeon directory not found"
        echo "WORKPATH: $WORKPATH"
        echo "Searched for:"
        echo "  - $WORKPATH/docker_compose/intel/cpu/xeon"
        echo "  - $WORKPATH/CogniwareIms/docker_compose/intel/cpu/xeon"
        if [ -d "$WORKPATH/docker_compose" ]; then
            echo "Found docker_compose directory structure:"
            find "$WORKPATH/docker_compose" -type d -maxdepth 3 2>/dev/null | head -10
        fi
        exit 1
    fi

    echo "Changing to compose directory: $compose_dir"
    cd "$compose_dir" || {
        echo "ERROR: Failed to cd to $compose_dir"
        exit 1
    }
    echo "Current directory: $(pwd)"

    # Set environment variables
    export HUGGINGFACEHUB_API_TOKEN=${HUGGINGFACEHUB_API_TOKEN}
    export LLM_MODEL_ID=${LLM_MODEL_ID:-"Intel/neural-chat-7b-v3-3"}
    export EMBEDDING_MODEL_ID=${EMBEDDING_MODEL_ID:-"BAAI/bge-base-en-v1.5"}
    export RERANK_MODEL_ID=${RERANK_MODEL_ID:-"BAAI/bge-reranker-base"}
    export POSTGRES_PASSWORD=${POSTGRES_PASSWORD:-"postgres"}

    echo "Starting Docker Compose services..."
    docker compose up -d

    # Wait for services to be ready
    echo "Waiting for services to initialize..."
    sleep 90

    # Check if containers are running
    echo "Checking container status..."
    docker compose ps
}

function validate_services() {
    echo "Validating microservices..."

    # Check Redis - wait for container to be ready first
    echo "Checking Redis..."
    max_attempts=30
    attempt=0
    while [ $attempt -lt $max_attempts ]; do
        if docker ps | grep -q "redis-vector-db"; then
            if docker logs redis-vector-db 2>&1 | grep -q "Ready to accept connections"; then
                echo "Redis is ready!"
                break
            fi
        fi
        attempt=$((attempt + 1))
        echo "Waiting for Redis container... (attempt $attempt/$max_attempts)"
        sleep 5
    done

    if [ $attempt -eq $max_attempts ]; then
        echo "ERROR: Redis failed to become ready"
        docker logs redis-vector-db || true
        exit 1
    fi

    # Check PostgreSQL
    echo "Checking PostgreSQL..."
    max_attempts=30
    attempt=0
    while [ $attempt -lt $max_attempts ]; do
        if docker ps | grep -q "postgres-db"; then
            if docker exec postgres-db pg_isready -U postgres > /dev/null 2>&1; then
                echo "PostgreSQL is ready!"
                break
            fi
        fi
        attempt=$((attempt + 1))
        echo "Waiting for PostgreSQL container... (attempt $attempt/$max_attempts)"
        sleep 5
    done

    if [ $attempt -eq $max_attempts ]; then
        echo "ERROR: PostgreSQL failed to become ready"
        docker logs postgres-db || true
        exit 1
    fi

    # Check TGI service
    wait_for_service "http://${ip_address}:8008/health" "TGI service" 30 || exit 1

    # Check LLM microservice
    wait_for_service "http://${ip_address}:9000/v1/health" "LLM microservice" 30 || exit 1

    # Check Embedding microservice
    wait_for_service "http://${ip_address}:6000/v1/health" "Embedding microservice" 30 || exit 1

    # Check Retriever microservice
    wait_for_service "http://${ip_address}:7000/v1/health" "Retriever microservice" 30 || exit 1

    # Check Reranking microservice
    wait_for_service "http://${ip_address}:8000/v1/health" "Reranking microservice" 30 || exit 1

    echo "All microservices are healthy!"
}

function validate_backend() {
    echo "Validating Cogniware IMS backend..."

    # Check backend health
    wait_for_service "http://${ip_address}:8000/api/health" "Cogniware IMS backend" 30 || exit 1

    # Test chat endpoint
    echo "Testing chat completion..."
    max_attempts=3
    attempt=0
    while [ $attempt -lt $max_attempts ]; do
        response=$(curl -s -X POST http://${ip_address}:8000/api/chat \
            -H "Content-Type: application/json" \
            -d '{
                "message": "What Intel processors are best for inventory systems?",
                "session_id": "test_session",
                "user_role": "Inventory Manager"
            }' || echo "")

        if [ -z "$response" ]; then
            echo "Empty response from chat endpoint (attempt $((attempt + 1))/$max_attempts)"
            attempt=$((attempt + 1))
            sleep 5
            continue
        fi

        if echo "$response" | grep -qi "error"; then
            echo "Chat test failed!"
            echo "Response: $response"
            attempt=$((attempt + 1))
            if [ $attempt -ge $max_attempts ]; then
                exit 1
            fi
            sleep 5
        else
            echo "Chat test successful!"
            break
        fi
    done

    # Test knowledge stats
    echo "Testing knowledge base stats..."
    wait_for_service "http://${ip_address}:8000/api/knowledge/stats" "Knowledge base stats" 10 || exit 1

    echo "Backend validation successful!"
}

function validate_frontend() {
    echo "Validating Cogniware IMS frontend..."

    # Check UI health
    wait_for_service "http://${ip_address}:3000" "Cogniware IMS UI" 30 || exit 1

    echo "Frontend validation successful!"
}

function stop_services() {
    echo "Stopping services..."
    local compose_dir=""
    if [ -d "$WORKPATH/docker_compose/intel/cpu/xeon" ]; then
        compose_dir="$WORKPATH/docker_compose/intel/cpu/xeon"
    elif [ -d "$WORKPATH/CogniwareIms/docker_compose/intel/cpu/xeon" ]; then
        compose_dir="$WORKPATH/CogniwareIms/docker_compose/intel/cpu/xeon"
    else
        echo "Warning: docker_compose/intel/cpu/xeon directory not found, attempting cleanup anyway"
        docker compose down -v 2>/dev/null || {
            echo "Warning: Some containers may not have stopped cleanly"
            docker ps -a | grep cogniware || true
        }
        return
    fi

    if [ -n "$compose_dir" ]; then
        cd "$compose_dir" || {
            echo "Warning: Failed to cd to $compose_dir, attempting cleanup from current directory"
        }
    fi
    docker compose down -v 2>/dev/null || {
        echo "Warning: Some containers may not have stopped cleanly"
        docker ps -a | grep cogniware || true
    }
}

function main() {
    echo "========================================="
    echo "Cogniware IMS E2E Test on Intel Xeon"
    echo "========================================="

    stop_services
    build_docker_images
    start_services
    validate_services
    validate_backend
    validate_frontend
    stop_services

    echo "========================================="
    echo "Cogniware IMS E2E Test Passed!"
    echo "========================================="
}

main
