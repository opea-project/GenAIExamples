# Deploy CodeGen on Kubernetes using Helm

This guide explains how to deploy the CodeGen application to a Kubernetes cluster using the official OPEA Helm chart.

## Table of Contents

- [Purpose](#purpose)
- [Prerequisites](#prerequisites)
- [Deployment Steps](#deployment-steps)
  - [1. Set Hugging Face Token](#1-set-hugging-face-token)
  - [2. Choose Hardware Configuration](#2-choose-hardware-configuration)
  - [3. Install Helm Chart](#3-install-helm-chart)
- [Verify Deployment](#verify-deployment)
- [Accessing the Service](#accessing-the-service)
- [Customization](#customization)
- [Uninstalling the Chart](#uninstalling-the-chart)

## Purpose

To provide a standardized and configurable method for deploying the CodeGen application and its microservice dependencies onto Kubernetes using Helm.

## Prerequisites

- A running Kubernetes cluster.
- `kubectl` installed and configured to interact with your cluster.
- Helm (version >= 3.15) installed. Refer to the [Helm Installation Guide](https://helm.sh/docs/intro/install/) if needed.
- Network access from your cluster nodes to download container images (from `ghcr.io/opea-project` and Hugging Face) and models.

## Deployment Steps

### 1. Set Hugging Face Token

The chart requires your Hugging Face Hub API token to download models. Set it as an environment variable:

```bash
export HFTOKEN="your-huggingface-api-token-here"
```
Replace `your-huggingface-api-token-here` with your actual token.

### 2. Choose Hardware Configuration

The CodeGen Helm chart supports different hardware configurations using values files:

-   **Intel Xeon CPU:** Use `cpu-values.yaml` (located within the chart structure, or provide your own). This is suitable for general Kubernetes clusters without specific accelerators.
-   **Intel Gaudi HPU:** Use `gaudi-values.yaml` (located within the chart structure, or provide your own). This requires nodes with Gaudi devices and the appropriate Kubernetes device plugins configured.

### 3. Install Helm Chart

Install the CodeGen chart from the OPEA OCI registry, providing your Hugging Face token and selecting the appropriate values file.

**Deploy on Xeon (CPU):**

```bash
helm install codegen oci://ghcr.io/opea-project/charts/codegen \
  --set global.HUGGINGFACEHUB_API_TOKEN=${HFTOKEN} \
  -f cpu-values.yaml \
  --namespace codegen --create-namespace
```
*Note: `-f cpu-values.yaml` assumes a file named `cpu-values.yaml` exists locally or you are referencing one within the chart structure accessible to Helm. You might need to download it first or customize parameters directly using `--set`.*

**Deploy on Gaudi (HPU):**

```bash
helm install codegen oci://ghcr.io/opea-project/charts/codegen \
  --set global.HUGGINGFACEHUB_API_TOKEN=${HFTOKEN} \
  -f gaudi-values.yaml \
  --namespace codegen --create-namespace
```
*Note: `-f gaudi-values.yaml` has the same assumption as above. Ensure your cluster meets Gaudi prerequisites.*

*The command installs the chart into the `codegen` namespace, creating it if necessary. Change `--namespace` if desired.*

## Verify Deployment

Check the status of the pods created by the Helm release:

```bash
kubectl get pods -n codegen
```
Wait for all pods (e.g., codegen-gateway, codegen-llm, codegen-embedding, redis, etc.) to reach the `Running` state. Check logs if any pods encounter issues:
```bash
kubectl logs -n codegen <pod-name>
```

## Accessing the Service

By default, the Helm chart typically exposes the CodeGen gateway service via a Kubernetes `Service` of type `ClusterIP` or `LoadBalancer`, depending on the chart's values.

-   **If `ClusterIP`:** Access is typically internal to the cluster or requires port-forwarding:
    ```bash
    # Find the service name (e.g., codegen-gateway)
    kubectl get svc -n codegen
    # Forward local port 7778 to the service port (usually 7778)
    kubectl port-forward svc/<service-name> -n codegen 7778:7778
    # Access via curl on localhost:7778
    curl http://localhost:7778/v1/codegen -H "Content-Type: application/json" -d '{"messages": "Test"}'
    ```

-   **If `LoadBalancer`:** Obtain the external IP address assigned by your cloud provider:
    ```bash
    kubectl get svc -n codegen <service-name> -o jsonpath='{.status.loadBalancer.ingress[0].ip}'
    # Access using the external IP and service port (e.g., 7778)
    export EXTERNAL_IP=$(kubectl get svc -n codegen <service-name> -o jsonpath='{.status.loadBalancer.ingress[0].ip}')
    curl http://${EXTERNAL_IP}:7778/v1/codegen -H "Content-Type: application/json" -d '{"messages": "Test"}'
    ```

Refer to the chart's documentation or `values.yaml` for specifics on service exposure. The UI service might also be exposed similarly (check for a UI-related service).

## Customization

You can customize the deployment by:

-   Modifying the `cpu-values.yaml` or `gaudi-values.yaml` file before installation.
-   Overriding parameters using the `--set` flag during `helm install`. Example:
    ```bash
    helm install codegen oci://ghcr.io/opea-project/charts/codegen \
      --set global.HUGGINGFACEHUB_API_TOKEN=${HFTOKEN} \
      --namespace codegen --create-namespace
      # Add other --set overrides or -f <your-custom-values.yaml>
    ```
-   Refer to the [OPEA Helm Charts README](https://github.com/opea-project/GenAIInfra/tree/main/helm-charts#readme) for detailed information on available configuration options within the charts.

## Uninstalling the Chart

To remove the CodeGen deployment installed by Helm:

```bash
helm uninstall codegen -n codegen
```
Optionally, delete the namespace if it's no longer needed and empty:
```bash
# kubectl delete ns codegen
```
