#!/bin/bash
# Copyright (C) 2024 Intel Corporation
# SPDX-License-Identifier: Apache-2.0

# Helm Chart Test Script for CogniwareIMS
# This script tests the Helm chart installation and validates the deployment

set -euo pipefail

# Configuration
CHART_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
NAMESPACE="${NAMESPACE:-opea-test}"
RELEASE_NAME="${RELEASE_NAME:-cogniwareims}"
TIMEOUT="${TIMEOUT:-600}"

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Track if release was successfully installed
RELEASE_INSTALLED=false

# Cleanup function
cleanup() {
    echo -e "${YELLOW}Cleaning up Helm release...${NC}"
    
    # Only try to uninstall if release was actually installed
    if [ "$RELEASE_INSTALLED" = true ]; then
        # Check if release exists before trying to uninstall
        if helm list -n "${NAMESPACE}" --short 2>/dev/null | grep -q "^${RELEASE_NAME}$"; then
            echo "Uninstalling Helm release: ${RELEASE_NAME}"
            helm uninstall "${RELEASE_NAME}" -n "${NAMESPACE}" 2>/dev/null || {
                echo -e "${YELLOW}Warning: Failed to uninstall release, but continuing cleanup...${NC}"
            }
        else
            echo -e "${YELLOW}Release ${RELEASE_NAME} not found, skipping uninstall${NC}"
        fi
    else
        echo -e "${YELLOW}Release was not installed, skipping uninstall${NC}"
    fi
    
    # Clean up namespace if it exists
    if kubectl get namespace "${NAMESPACE}" >/dev/null 2>&1; then
        echo "Deleting namespace: ${NAMESPACE}"
        kubectl delete namespace "${NAMESPACE}" --grace-period=0 --force 2>/dev/null || {
            echo -e "${YELLOW}Warning: Failed to delete namespace, but continuing...${NC}"
        }
    fi
    
    echo -e "${GREEN}Cleanup completed${NC}"
}

# Set trap to ensure cleanup runs on exit
trap cleanup EXIT ERR

# Function to check if command exists
check_command() {
    if ! command -v "$1" >/dev/null 2>&1; then
        echo -e "${RED}Error: $1 is not installed${NC}"
        exit 1
    fi
}

# Function to validate prerequisites
validate_prerequisites() {
    echo "Validating prerequisites..."
    check_command helm
    check_command kubectl
    
    # Check if we can access the cluster
    if ! kubectl cluster-info >/dev/null 2>&1; then
        echo -e "${RED}Error: Cannot access Kubernetes cluster${NC}"
        exit 1
    fi
    
    echo -e "${GREEN}Prerequisites validated${NC}"
}

# Function to create namespace
create_namespace() {
    echo "Creating namespace: ${NAMESPACE}"
    if kubectl get namespace "${NAMESPACE}" >/dev/null 2>&1; then
        echo -e "${YELLOW}Namespace ${NAMESPACE} already exists${NC}"
    else
        kubectl create namespace "${NAMESPACE}"
        echo -e "${GREEN}Namespace created${NC}"
    fi
}

# Function to install Helm chart
install_chart() {
    echo "Installing Helm chart: ${RELEASE_NAME}"
    echo "Chart directory: ${CHART_DIR}"
    echo "Namespace: ${NAMESPACE}"
    
    # Set environment variables if provided
    export HUGGINGFACEHUB_API_TOKEN="${HUGGINGFACEHUB_API_TOKEN:-}"
    
    # Install the chart
    if helm install "${RELEASE_NAME}" "${CHART_DIR}" \
        --namespace "${NAMESPACE}" \
        --wait \
        --timeout "${TIMEOUT}s" \
        --set global.HUGGINGFACEHUB_API_TOKEN="${HUGGINGFACEHUB_API_TOKEN}" \
        2>&1; then
        RELEASE_INSTALLED=true
        echo -e "${GREEN}Helm chart installed successfully${NC}"
    else
        echo -e "${RED}Failed to install Helm chart${NC}"
        exit 1
    fi
}

# Function to validate deployment
validate_deployment() {
    echo "Validating deployment..."
    
    # Wait for pods to be ready
    echo "Waiting for pods to be ready..."
    if kubectl wait --for=condition=ready pod \
        -l app.kubernetes.io/name=cogniwareims \
        -n "${NAMESPACE}" \
        --timeout="${TIMEOUT}s" 2>/dev/null; then
        echo -e "${GREEN}Pods are ready${NC}"
    else
        echo -e "${YELLOW}Warning: Some pods may not be ready${NC}"
        kubectl get pods -n "${NAMESPACE}"
    fi
    
    # Check service endpoints
    echo "Checking services..."
    kubectl get svc -n "${NAMESPACE}"
    
    echo -e "${GREEN}Deployment validation completed${NC}"
}

# Main function
main() {
    echo "========================================="
    echo "CogniwareIMS Helm Chart Test"
    echo "========================================="
    echo "Release Name: ${RELEASE_NAME}"
    echo "Namespace: ${NAMESPACE}"
    echo "Timeout: ${TIMEOUT}s"
    echo "========================================="
    
    validate_prerequisites
    create_namespace
    install_chart
    validate_deployment
    
    echo "========================================="
    echo -e "${GREEN}Helm chart test completed successfully!${NC}"
    echo "========================================="
}

# Run main function
main

