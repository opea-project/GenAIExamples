#!/bin/bash
# Copyright (C) 2024 Intel Corporation
# SPDX-License-Identifier: Apache-2.0

set -e

WORKPATH=$(dirname "$PWD")
LOG_PATH="$WORKPATH/tests"

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
    cd $WORKPATH/docker_image_build
    docker compose -f build.yaml build
}

function start_services() {
    echo "Starting Cogniware IMS services on Intel Xeon..."
    cd $WORKPATH/docker_compose/intel/cpu/xeon

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
    cd $WORKPATH/docker_compose/intel/cpu/xeon
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

