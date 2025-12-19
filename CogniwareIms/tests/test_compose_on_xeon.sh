#!/bin/bash
# Copyright (C) 2024 Intel Corporation
# SPDX-License-Identifier: Apache-2.0

set -e

WORKPATH=$(dirname "$PWD")
LOG_PATH="$WORKPATH/tests"
ip_address=$(hostname -I | awk '{print $1}')

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

    docker compose up -d

    # Wait for services to be ready
    sleep 90
}

function validate_services() {
    echo "Validating microservices..."

    # Check Redis
    echo "Checking Redis..."
    docker logs redis-vector-db | grep -q "Ready to accept connections" || exit 1

    # Check PostgreSQL
    echo "Checking PostgreSQL..."
    docker exec postgres-db pg_isready -U postgres || exit 1

    # Check TGI service
    echo "Checking TGI service..."
    until curl -s http://${ip_address}:8008/health > /dev/null; do
        echo "Waiting for TGI service..."
        sleep 10
    done

    # Check LLM microservice
    echo "Checking LLM microservice..."
    until curl -s http://${ip_address}:9000/v1/health > /dev/null; do
        echo "Waiting for LLM microservice..."
        sleep 10
    done

    # Check Embedding microservice
    echo "Checking Embedding microservice..."
    until curl -s http://${ip_address}:6000/v1/health > /dev/null; do
        echo "Waiting for Embedding microservice..."
        sleep 10
    done

    # Check Retriever microservice
    echo "Checking Retriever microservice..."
    until curl -s http://${ip_address}:7000/v1/health > /dev/null; do
        echo "Waiting for Retriever microservice..."
        sleep 10
    done

    # Check Reranking microservice
    echo "Checking Reranking microservice..."
    until curl -s http://${ip_address}:8000/v1/health > /dev/null; do
        echo "Waiting for Reranking microservice..."
        sleep 10
    done

    echo "All microservices are healthy!"
}

function validate_backend() {
    echo "Validating Cogniware IMS backend..."

    # Check backend health
    until curl -s http://${ip_address}:8000/api/health > /dev/null; do
        echo "Waiting for Cogniware IMS backend..."
        sleep 10
    done

    # Test chat endpoint
    echo "Testing chat completion..."
    response=$(curl -s -X POST http://${ip_address}:8000/api/chat \
        -H "Content-Type: application/json" \
        -d '{
            "message": "What Intel processors are best for inventory systems?",
            "session_id": "test_session",
            "user_role": "Inventory Manager"
        }')

    if echo "$response" | grep -q "error"; then
        echo "Chat test failed!"
        echo "$response"
        exit 1
    fi

    # Test knowledge stats
    echo "Testing knowledge base stats..."
    curl -s http://${ip_address}:8000/api/knowledge/stats > /dev/null || exit 1

    echo "Backend validation successful!"
}

function validate_frontend() {
    echo "Validating Cogniware IMS frontend..."

    # Check UI health
    until curl -s http://${ip_address}:3000 > /dev/null; do
        echo "Waiting for Cogniware IMS UI..."
        sleep 10
    done

    echo "Frontend validation successful!"
}

function stop_services() {
    echo "Stopping services..."
    cd $WORKPATH/docker_compose/intel/cpu/xeon

    # Stop containers first
    docker compose stop 2>/dev/null || true

    # Wait for containers to stop
    sleep 5

    # Remove containers
    docker compose rm -f 2>/dev/null || true

    # Remove volumes and networks (with retry)
    for i in {1..3}; do
        if docker compose down -v 2>/dev/null; then
            break
        else
            echo "Attempt $i: Some containers still running, waiting..."
            sleep 5
            # Force stop any remaining containers
            docker compose ps -q | xargs -r docker stop 2>/dev/null || true
            docker compose ps -q | xargs -r docker rm -f 2>/dev/null || true
        fi
    done

    # Final cleanup - remove any orphaned containers
    docker ps -a --filter "label=com.docker.compose.project" --format "{{.ID}}" | xargs -r docker rm -f 2>/dev/null || true

    # Remove networks that might be orphaned
    docker network ls --filter "name=opea\|cogniware\|xeon" --format "{{.ID}}" | xargs -r docker network rm 2>/dev/null || true

    echo "Services stopped and cleaned up"
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
