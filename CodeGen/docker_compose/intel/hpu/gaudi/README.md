# Deploy CodeGen Application on Intel Gaudi HPU with Docker Compose

This README provides instructions for deploying the CodeGen application using Docker Compose on systems equipped with Intel Gaudi HPUs.

## Table of Contents

- [Overview](#overview)
- [Prerequisites](#prerequisites)
- [Quick Start Deployment](#quick-start-deployment)
- [Building Custom Images (Optional)](#building-custom-images-optional)
- [Validate Services](#validate-services)
- [Accessing the User Interface (UI)](#accessing-the-user-interface-ui)
- [Troubleshooting](#troubleshooting)
- [Stopping the Application](#stopping-the-application)
- [Next Steps](#next-steps)

## Overview

This guide focuses on running the pre-configured CodeGen service using Docker Compose on Intel Gaudi HPUs. It leverages containers optimized for Gaudi for the LLM serving component (vLLM or TGI), along with CPU-based containers for other microservices like embedding, retrieval, data preparation, the main gateway, and the UI.

## Prerequisites

- Docker and Docker Compose installed.
- Intel Gaudi HPU(s) with the necessary drivers and software stack installed on the host system. (Refer to [Intel Gaudi Documentation](https://docs.habana.ai/en/latest/)).
- Git installed (for cloning repository).
- Hugging Face Hub API Token (for downloading models).
- Access to the internet (or a private model cache).
- Clone the `GenAIExamples` repository:
  ```bash
  git clone https://github.com/opea-project/GenAIExamples.git
  cd GenAIExamples/CodeGen/docker_compose
  ```

## Quick Start Deployment

This uses the default vLLM-based deployment using `compose.yaml`.

1.  **Configure Environment:**
    Set required environment variables in your shell:

    ```bash
    # Replace with your host's external IP address (do not use localhost or 127.0.0.1)
    export HOST_IP="your_external_ip_address"
    # Replace with your Hugging Face Hub API token
    export HF_TOKEN="your_huggingface_token"

    # Optional: Configure proxy if needed
    # export http_proxy="your_http_proxy"
    # export https_proxy="your_https_proxy"
    # export no_proxy="localhost,127.0.0.1,${HOST_IP}" # Add other hosts if necessary
    source intel/set_env.sh
    cd intel/hpu/gaudi
    cd grafana/dashboards
    bash download_opea_dashboard.sh
    cd ../..
    ```

    _Note: The compose file might read additional variables from set_env.sh. Ensure all required variables like ports (`LLM_SERVICE_PORT`, `MEGA_SERVICE_PORT`, etc.) are set if not using defaults from the compose file._
    For instance, edit the set_env.sh to change the LLM model

    ```bash
    export LLM_MODEL_ID="Qwen/Qwen2.5-Coder-7B-Instruct"
    ```

    can be changed to other model if needed

    ```bash
    export LLM_MODEL_ID="Qwen/Qwen2.5-Coder-32B-Instruct"
    ```

2.  **Start Services (vLLM using compose.yaml):**

    ```bash
    docker compose up -d
    ```

3.  **Validate:**
    Wait several minutes for models to download and services to initialize (Gaudi initialization can take time). Check container logs (`docker compose logs -f <service_name>`, especially `codegen-vllm-gaudi-server` for vLLM or `codegen-tgi-gaudi-server` for TGI) or proceed to the validation steps below.

## Available Deployment Options

There are two separate Docker Compose files to select the LLM serving backend accelerated on Gaudi.

### Default: vLLM-based Deployment (`compose.yaml`)

- **Compose File:** `compose.yaml`
- **Description:** Uses vLLM optimized for Intel Gaudi HPUs as the LLM serving engine. This is the default deployment used in the Quick Start.
- **Gaudi Service:** `codegen-vllm-gaudi-server`
- **Other Services:** `codegen-llm-server`, `codegen-tei-embedding-server` (CPU), `codegen-retriever-server` (CPU), `redis-vector-db` (CPU), `codegen-dataprep-server` (CPU), `codegen-backend-server` (CPU), `codegen-ui-server` (CPU).

### TGI-based Deployment (`compose_tgi.yaml`)

- **Compose File:** `compose_tgi.yaml`
- **Description:** Uses Hugging Face Text Generation Inference (TGI) optimized for Intel Gaudi HPUs as the LLM serving engine.
- **Gaudi Service:** `codegen-tgi-gaudi-server`
- **Other Services:** Same CPU-based services as the vLLM configuration.
- **To Run:**
  ```bash
  # Ensure environment variables (HOST_IP, HF_TOKEN) are set
  docker compose -f compose_tgi.yaml up -d
  ```

## Configuration Parameters

### Environment Variables

Key parameters are configured via environment variables set before running `docker compose up`.

| Environment Variable                    | Description                                                                                                       | Default (Set Externally)                                  |
| :-------------------------------------- | :---------------------------------------------------------------------------------------------------------------- | :-------------------------------------------------------- |
| `HOST_IP`                               | External IP address of the host machine. **Required.**                                                            | `your_external_ip_address`                                |
| `HF_TOKEN`                              | Your Hugging Face Hub token for model access. **Required.**                                                       | `your_huggingface_token`                                  |
| `LLM_MODEL_ID`                          | Hugging Face model ID for the CodeGen LLM (used by TGI/vLLM service). Configured within compose file environment. | `Qwen/Qwen2.5-Coder-7B-Instruct`                          |
| `EMBEDDING_MODEL_ID`                    | Hugging Face model ID for the embedding model (used by TEI service). Configured within compose file environment.  | `BAAI/bge-base-en-v1.5`                                   |
| `LLM_ENDPOINT`                          | Internal URL for the LLM serving endpoint (used by LLM service). Configured in compose files.                     | `http://codegen-vllm-gaudi-server:80/v1/chat/completions` |
| `TEI_EMBEDDING_ENDPOINT`                | Internal URL for the Embedding service. Configured in compose files.                                              | `http://tei-embedding-serving:80/embed`                   |
| `DATAPREP_ENDPOINT`                     | Internal URL for the Data Preparation service. Configured in compose files.                                       | `http://dataprep-redis-server:5000/dataprep`              |
| `BACKEND_SERVICE_ENDPOINT`              | External URL for the CodeGen Gateway (MegaService). Derived from `HOST_IP` and port `7778`.                       | `http://${HOST_IP}:7778/v1/codegen`                       |
| `*_PORT` (Internal)                     | Internal container ports (e.g., `80`, `6379`). Defined in compose files.                                          | N/A                                                       |
| `http_proxy` / `https_proxy`/`no_proxy` | Network proxy settings (if required).                                                                             | `""`                                                      |

Most of these parameters are in `set_env.sh`, you can either modify this file or overwrite the env variables by setting them.

```shell
source CodeGen/docker_compose/set_env.sh
```

### Compose Files

Different Docker Compose files (`compose.yaml`, `compose_tgi.yaml`) control which Gaudi-accelerated LLM serving backend (vLLM or TGI) is used. CPU-based services run under both configurations.

### Docker Compose Gaudi Configuration

Both `compose.yaml` and `compose_tgi.yaml` files include specific configurations for their respective Gaudi services:

```yaml
# Example snippet for Gaudi service configuration
runtime: habana # Specifies the Habana runtime for Docker
volumes:
  - /dev/vfio:/dev/vfio # Mount necessary device files
cap_add:
  - SYS_NICE # Add capabilities needed by Gaudi drivers/runtime
ipc: host # Use host IPC namespace
environment:
  HABANA_VISIBLE_DEVICES: all # Make all Gaudi devices visible
  # Other model/service specific env vars
```

This setup grants the container access to Gaudi devices. Ensure the host system has the Habana Docker runtime correctly installed and configured.

## Building Custom Images (Optional)

If you need to modify microservices:

1.  **For Gaudi Services (TGI/vLLM):** Refer to specific build instructions for TGI-Gaudi or vLLM-Gaudi within [OPEA GenAIComps](https://github.com/opea-project/GenAIComps) or their respective upstream projects. Building Gaudi-optimized images often requires a specific build environment.
2.  **For CPU Services:** Follow instructions in `GenAIComps` component directories (e.g., `comps/codegen`, `comps/ui/gradio`). Use the provided Dockerfiles.
3.  Tag your custom images.
4.  Update the `image:` fields in the `compose.yaml` file.

## Validate Services

### Check Container Status

Ensure all containers are running, especially the Gaudi-accelerated LLM service:

```bash
docker compose ps  # for vLLM (compose.yaml)
# or
docker compose -f compose_tgi.yaml ps  # for TGI
```

Check logs: `docker compose logs <service_name>`. Pay attention to `codegen-vllm-gaudi-server` (for vLLM) or `codegen-tgi-gaudi-server` (for TGI) logs for initialization status and errors.

### Run Validation Script/Commands

Use `curl` commands targeting the main service endpoints. Ensure `HOST_IP` is correctly set.

1.  **Validate LLM Serving Endpoint (Example for vLLM deployment):**

    ```bash
    # This command structure targets the OpenAI-compatible vLLM endpoint
    curl http://${HOST_IP}:9000/v1/chat/completions \
       -X POST \
       -H 'Content-Type: application/json' \
       -d '{"model": "Qwen/Qwen2.5-Coder-7B-Instruct", "messages": [{"role": "user", "content": "Implement a basic Python class"}], "max_tokens":32}'
    ```

2.  **Validate CodeGen Gateway (MegaService, default host port 7778):**
    ```bash
    curl http://${HOST_IP}:7778/v1/codegen \
      -H "Content-Type: application/json" \
      -d '{"messages": "Implement a sorting algorithm in Python."}'
    ```
    - **Expected Output:** Stream of JSON data chunks with generated code, ending in `data: [DONE]`.

## Accessing the User Interface (UI)

UI options are similar to the Xeon deployment.

### Svelte UI (Default)

Access the default Svelte UI:
`http://{HOST_IP}:5173`
_(Port `5173` is the default host mapping)_

![Svelte UI](../../../../assets/img/codeGen_ui_init.jpg)

### Gradio UI (Optional)

1.  Modify the compose file (either `compose.yaml` or `compose_tgi.yaml`): Swap Svelte service for Gradio (`codegen-gradio-ui-server`), check port map (e.g., `5173:5173`).
2.  Restart: `docker compose up -d` or `docker compose -f compose_tgi.yaml up -d`
3.  Access: `http://{HOST_IP}:5173`

### React UI (Optional)

1.  Modify the compose file (either `compose.yaml` or `compose_tgi.yaml`): Swap Svelte service for React (`codegen-gaudi-react-ui-server`), check port map (e.g., `5174:80`).
2.  Restart: `docker compose up -d` or `docker compose -f compose_tgi.yaml up -d`
3.  Access: `http://{HOST_IP}:5174`

### VS Code Extension (Optional)

Use the `Neural Copilot` extension configured with the CodeGen backend URL: `http://${HOST_IP}:7778/v1/codegen`. (See Xeon README for detailed setup screenshots).

## Troubleshooting

- **Gaudi Service Issues:**
  - Check logs of the active service: `codegen-vllm-gaudi-server` for vLLM deployment or `codegen-tgi-gaudi-server` for TGI deployment.
  - Ensure host drivers and Habana Docker runtime are installed and working (`habana-container-runtime`).
  - Verify `runtime: habana` and volume mounts in the compose files.
  - Gaudi initialization can take significant time and memory. Monitor resource usage.
- **Model Download Issues:** Check `HF_TOKEN`, internet access, proxy settings. Check LLM service logs.
- **Connection Errors:** Verify `HOST_IP`, ports, and proxy settings. Use `docker ps` and check service logs.

## Monitoring Deployment

To enable monitoring for the CodeGen application on Gaudi, you can use the monitoring Docker Compose file along with the main deployment.

### Option #1: Default Deployment (without monitoring)

To deploy the CodeGen services without monitoring, execute:

```bash
docker compose up -d
```

### Option #2: Deployment with Monitoring

> NOTE: To enable monitoring, `compose.monitoring.yaml` file need to be merged along with default `compose.yaml` file.

To deploy with monitoring:

```bash
docker compose -f compose.yaml -f compose.monitoring.yaml up -d
```

### Accessing Monitoring Services

Once deployed with monitoring, you can access:

- **Prometheus**: `http://${HOST_IP}:9090`
- **Grafana**: `http://${HOST_IP}:3000` (username: `admin`, password: `admin`)
- **Node Exporter**: `http://${HOST_IP}:9100`

### Monitoring Components

The monitoring stack includes:

- **Prometheus**: For metrics collection and querying
- **Grafana**: For visualization and dashboards
- **Node Exporter**: For system metrics collection

### Monitoring Dashboards

The following dashboards are automatically downloaded and configured:

- vLLM Dashboard
- TGI Dashboard
- CodeGen MegaService Dashboard
- Node Exporter Dashboard

### Stopping the Application

If monitoring is enabled, execute the following command:

```bash
docker compose -f compose.yaml -f compose.monitoring.yaml down
```

If monitoring is not enabled, execute:

```bash
docker compose down  # for vLLM (compose.yaml)
# or
docker compose -f compose_tgi.yaml down  # for TGI
```

## Next Steps

- Experiment with different models supported by TGI/vLLM on Gaudi.
- Consult [OPEA GenAIComps](https://github.com/opea-project/GenAIComps) for microservice details.
- Refer to the main [CodeGen README](../../../../README.md) for benchmarking and Kubernetes deployment options.
