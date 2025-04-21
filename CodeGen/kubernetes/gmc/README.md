# Deploy CodeGen using Kubernetes Microservices Connector (GMC)

This document guides you through deploying the CodeGen application on a Kubernetes cluster using the OPEA Microservices Connector (GMC).

## Table of Contents

- [Purpose](#purpose)
- [Prerequisites](#prerequisites)
- [Deployment Steps](#deployment-steps)
  - [1. Choose Configuration](#1-choose-configuration)
  - [2. Prepare Namespace and Deploy](#2-prepare-namespace-and-deploy)
  - [3. Verify Pod Status](#3-verify-pod-status)
- [Validation Steps](#validation-steps)
  - [1. Deploy Test Client](#1-deploy-test-client)
  - [2. Get Service URL](#2-get-service-url)
  - [3. Send Test Request](#3-send-test-request)
- [Cleanup](#cleanup)

## Purpose

To deploy the multi-component CodeGen application on Kubernetes, leveraging GMC to manage the connections and routing between microservices based on a declarative configuration file.

## Prerequisites

- A running Kubernetes cluster.
- `kubectl` installed and configured to interact with your cluster.
- [GenAI Microservice Connector (GMC)](https://github.com/opea-project/GenAIInfra/tree/main/microservices-connector/README.md) installed in your cluster. Follow the GMC installation guide if you haven't already.
- Access to the container images specified in the GMC configuration files (`codegen_xeon.yaml` or `codegen_gaudi.yaml`). These may be on Docker Hub or a private registry.

## Deployment Steps

### 1. Choose Configuration

Two GMC configuration files are provided based on the target hardware for the LLM serving component:

-   `codegen_xeon.yaml`: Deploys CodeGen using CPU-optimized components (suitable for Intel Xeon clusters).
-   `codegen_gaudi.yaml`: Deploys CodeGen using Gaudi-optimized LLM serving components (suitable for clusters with Intel Gaudi nodes).

Select the file appropriate for your cluster hardware. The following steps use `codegen_xeon.yaml` as an example.

### 2. Prepare Namespace and Deploy

Choose a namespace for the deployment (e.g., `codegen-app`).

```bash
# Set the desired namespace
export APP_NAMESPACE=codegen-app

# Create the namespace if it doesn't exist
kubectl create ns $APP_NAMESPACE || true

# (Optional) Update the namespace within the chosen YAML file if it's not parameterized
# sed -i "s|namespace: codegen|namespace: $APP_NAMESPACE|g" ./codegen_xeon.yaml

# Apply the GMC configuration file to the chosen namespace
kubectl apply -f ./codegen_xeon.yaml -n $APP_NAMESPACE
```
*Note: If the YAML file uses a hardcoded namespace, ensure you either modify the file or deploy to that specific namespace.*

### 3. Verify Pod Status

Check that all the pods defined in the GMC configuration are successfully created and running.

```bash
kubectl get pods -n $APP_NAMESPACE
```
Wait until all pods are in the `Running` state. This might take some time for image pulling and initialization.

## Validation Steps

### 1. Deploy Test Client

Deploy a simple pod within the same namespace to use as a client for sending requests.

```bash
kubectl create deployment client-test -n $APP_NAMESPACE --image=curlimages/curl -- sleep infinity
```
Verify the client pod is running:
```bash
kubectl get pods -n $APP_NAMESPACE -l app=client-test
```

### 2. Get Service URL

Retrieve the access URL exposed by the GMC for the CodeGen application.

```bash
# Get the client pod name
export CLIENT_POD=$(kubectl get pod -n $APP_NAMESPACE -l app=client-test -o jsonpath='{.items[0].metadata.name}')

# Get the access URL provided by the 'codegen' GMC resource
# Adjust 'codegen' if the metadata.name in your YAML is different
export ACCESS_URL=$(kubectl get gmc codegen -n $APP_NAMESPACE -o jsonpath='{.status.accessUrl}')

# Display the URL (optional)
echo "Access URL: $ACCESS_URL"
```
*Note: The `accessUrl` typically points to the internal Kubernetes service endpoint for the gateway service defined in the GMC configuration.*

### 3. Send Test Request

Use the test client pod to send a `curl` request to the CodeGen service endpoint.

```bash
# Define the payload
PAYLOAD='{"messages": "def print_hello_world():"}'

# Execute curl from the client pod
kubectl exec "$CLIENT_POD" -n $APP_NAMESPACE -- curl -s --no-buffer "$ACCESS_URL" \
  -X POST \
  -d "$PAYLOAD" \
  -H 'Content-Type: application/json'
```

**Expected Output:** A stream of JSON data containing the generated code, similar to the Docker Compose validation, ending with a `[DONE]` marker if streaming is enabled.

## Cleanup

To remove the deployed application and the test client:

```bash
# Delete the GMC deployment
kubectl delete -f ./codegen_xeon.yaml -n $APP_NAMESPACE

# Delete the test client deployment
kubectl delete deployment client-test -n $APP_NAMESPACE

# Optionally delete the namespace if no longer needed
# kubectl delete ns $APP_NAMESPACE
```
