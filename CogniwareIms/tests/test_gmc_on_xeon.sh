#!/bin/bash
# Copyright (C) 2024 Intel Corporation
# SPDX-License-Identifier: Apache-2.0

set -e

WORKPATH=$(dirname "$PWD")
LOG_PATH="$WORKPATH/tests"

function setup_gmc() {
    echo "Setting up GMC..."
    kubectl apply -f https://github.com/opea-project/GenAIInfra/releases/download/v1.0/gmc.yaml

    # Wait for GMC to be ready
    kubectl wait --for=condition=Ready pod -l app=gmc-controller -n gmc-system --timeout=300s
}

function deploy_inventoryms() {
    echo "Deploying InventoryMS with GMC..."

    # Create namespace
    kubectl create namespace opea || true

    # Deploy microservices
    kubectl apply -f $WORKPATH/kubernetes/gmc/inventoryms.yaml -n opea

    # Wait for deployment
    sleep 60
    kubectl wait --for=condition=Ready pod -l app=inventoryms -n opea --timeout=600s
}

function validate_deployment() {
    echo "Validating GMC deployment..."

    # Check GMConnector status
    kubectl get gmconnector inventoryms -n opea

    # Check pods
    kubectl get pods -n opea

    # Get service endpoint
    BACKEND_POD=$(kubectl get pod -n opea -l app=inventoryms-backend -o jsonpath='{.items[0].metadata.name}')

    # Port forward for testing
    kubectl port-forward -n opea pod/$BACKEND_POD 8888:8888 &
    PF_PID=$!
    sleep 5

    # Test health endpoint
    response=$(curl -s http://localhost:8888/health)
    if echo "$response" | grep -q "healthy"; then
        echo "Health check passed!"
    else
        echo "Health check failed!"
        kill $PF_PID
        exit 1
    fi

    # Test chat completion
    response=$(curl -s -X POST http://localhost:8888/v1/chat/completions \
        -H "Content-Type: application/json" \
        -d '{
            "messages": [
                {"role": "user", "content": "What Intel processors are available?"}
            ]
        }')

    if echo "$response" | grep -q "error"; then
        echo "Chat completion test failed!"
        kill $PF_PID
        exit 1
    fi

    echo "All validations passed!"
    kill $PF_PID
}

function cleanup() {
    echo "Cleaning up..."
    kubectl delete namespace opea --grace-period=0 --force || true
}

function main() {
    echo "========================================="
    echo "InventoryMS GMC Test on Intel Xeon"
    echo "========================================="

    setup_gmc
    deploy_inventoryms
    validate_deployment
    cleanup

    echo "========================================="
    echo "InventoryMS GMC Test Passed!"
    echo "========================================="
}

main
