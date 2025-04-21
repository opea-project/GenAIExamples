# Deploy CodeGen Application on Intel Gaudi HPU with Docker Compose

This README provides instructions for deploying the CodeGen application using Docker Compose on systems equipped with Intel Gaudi HPUs.

## Table of Contents

- [Overview](#overview)
- [Prerequisites](#prerequisites)
- [Quick Start](#quick-start)
- [Available Deployment Options](#available-deployment-options)
  - [Default: vLLM-based Deployment (`--profile codegen-gaudi-vllm`)](#default-vllm-based-deployment---profile-codegen-gaudi-vllm)
  - [TGI-based Deployment (`--profile codegen-gaudi-tgi`)](#tgi-based-deployment---profile-codegen-gaudi-tgi)
- [Configuration Parameters](#configuration-parameters)
  - [Environment Variables](#environment-variables)
  - [Compose Profiles](#compose-profiles)
  - [Docker Compose Gaudi Configuration](#docker-compose-gaudi-configuration)
- [Building Custom Images (Optional)](#building-custom-images-optional)
- [Validate Services](#validate-services)
  - [Check Container Status](#check-container-status)
  - [Run Validation Script/Commands](#run-validation-scriptcommands)
- [Accessing the User Interface (UI)](#accessing-the-user-interface-ui)
  - [Gradio UI (Default)](#gradio-ui-default)
  - [Svelte UI (Optional)](#svelte-ui-optional)
  - [React UI (Optional)](#react-ui-optional)
  - [VS Code Extension (Optional)](#vs-code-extension-optional)
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
  cd GenAIExamples/CodeGen/docker_compose/intel/hpu/gaudi
  ```

## Quick Start

This uses the default vLLM-based deployment profile (`codegen-gaudi-vllm`).

1.  **Configure Environment:**
    Set required environment variables in your shell:

    ```bash
    # Replace with your host's external IP address (do not use localhost or 127.0.0.1)
    export HOST_IP="your_external_ip_address"
    # Replace with your Hugging Face Hub API token
    export HUGGINGFACEHUB_API_TOKEN="your_huggingface_token"

    # Optional: Configure proxy if needed
    # export http_proxy="your_http_proxy"
    # export https_proxy="your_https_proxy"
    # export no_proxy="localhost,127.0.0.1,${HOST_IP}" # Add other hosts if necessary
    source ../../../set_env.sh
    ```

    _Note: Ensure all required variables like ports (`LLM_SERVICE_PORT`, `MEGA_SERVICE_PORT`, etc.) are set if not using defaults from the compose file._

2.  **Start Services (vLLM Profile):**

    ```bash
    docker compose --profile codegen-gaudi-vllm up -d
    ```

3.  **Validate:**
    Wait several minutes for models to download and services to initialize (Gaudi initialization can take time). Check container logs (`docker compose logs -f <service_name>`, especially `codegen-vllm-gaudi-server` or `codegen-tgi-gaudi-server`) or proceed to the validation steps below.

## Available Deployment Options

The `compose.yaml` file uses Docker Compose profiles to select the LLM serving backend accelerated on Gaudi.

### Default: vLLM-based Deployment (`--profile codegen-gaudi-vllm`)

- **Profile:** `codegen-gaudi-vllm`
- **Description:** Uses vLLM optimized for Intel Gaudi HPUs as the LLM serving engine. This is the default profile used in the Quick Start.
- **Gaudi Service:** `codegen-vllm-gaudi-server`
- **Other Services:** `codegen-llm-server`, `codegen-tei-embedding-server` (CPU), `codegen-retriever-server` (CPU), `redis-vector-db` (CPU), `codegen-dataprep-server` (CPU), `codegen-backend-server` (CPU), `codegen-gradio-ui-server` (CPU).

### TGI-based Deployment (`--profile codegen-gaudi-tgi`)

- **Profile:** `codegen-gaudi-tgi`
- **Description:** Uses Hugging Face Text Generation Inference (TGI) optimized for Intel Gaudi HPUs as the LLM serving engine.
- **Gaudi Service:** `codegen-tgi-gaudi-server`
- **Other Services:** Same CPU-based services as the vLLM profile.
- **To Run:**
  ```bash
  # Ensure environment variables (HOST_IP, HUGGINGFACEHUB_API_TOKEN) are set
  docker compose --profile codegen-gaudi-tgi up -d
  ```

## Configuration Parameters

### Environment Variables

Key parameters are configured via environment variables set before running `docker compose up`.

| Environment Variable                    | Description                                                                                                         | Default (Set Externally)                                                                         |
| :-------------------------------------- | :------------------------------------------------------------------------------------------------------------------ | :----------------------------------------------------------------------------------------------- |
| `HOST_IP`                               | External IP address of the host machine. **Required.**                                                              | `your_external_ip_address`                                                                       |
| `HUGGINGFACEHUB_API_TOKEN`              | Your Hugging Face Hub token for model access. **Required.**                                                         | `your_huggingface_token`                                                                         |
| `LLM_MODEL_ID`                          | Hugging Face model ID for the CodeGen LLM (used by TGI/vLLM service). Configured within `compose.yaml` environment. | `Qwen/Qwen2.5-Coder-7B-Instruct`                                                                 |
| `EMBEDDING_MODEL_ID`                    | Hugging Face model ID for the embedding model (used by TEI service). Configured within `compose.yaml` environment.  | `BAAI/bge-base-en-v1.5`                                                                          |
| `LLM_ENDPOINT`                          | Internal URL for the LLM serving endpoint (used by `codegen-llm-server`). Configured in `compose.yaml`.             | `http://codegen-tgi-server:80/generate` or `http://codegen-vllm-server:8000/v1/chat/completions` |
| `TEI_EMBEDDING_ENDPOINT`                | Internal URL for the Embedding service. Configured in `compose.yaml`.                                               | `http://codegen-tei-embedding-server:80/embed`                                                   |
| `DATAPREP_ENDPOINT`                     | Internal URL for the Data Preparation service. Configured in `compose.yaml`.                                        | `http://codegen-dataprep-server:80/dataprep`                                                     |
| `BACKEND_SERVICE_ENDPOINT`              | External URL for the CodeGen Gateway (MegaService). Derived from `HOST_IP` and port `7778`.                         | `http://${HOST_IP}:7778/v1/codegen`                                                              |
| `*_PORT` (Internal)                     | Internal container ports (e.g., `80`, `6379`). Defined in `compose.yaml`.                                           | N/A                                                                                              |
| `http_proxy` / `https_proxy`/`no_proxy` | Network proxy settings (if required).                                                                               | `""`                                                                                             |

Most of these parameters are in `set_env.sh`, you can either modify this file or overwrite the env variables by setting them.

```shell
source CodeGen/docker_compose/set_env.sh
```

### Compose Profiles

Docker Compose profiles (`codegen-gaudi-vllm`, `codegen-gaudi-tgi`) select the Gaudi-accelerated LLM serving backend (vLLM or TGI). CPU-based services run under both profiles.

### Docker Compose Gaudi Configuration

The `compose.yaml` file includes specific configurations for Gaudi services (`codegen-vllm-gaudi-server`, `codegen-tgi-gaudi-server`):

```yaml
# Example snippet for codegen-vllm-gaudi-server
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
docker compose --profile <profile_name> ps
# Example: docker compose --profile codegen-gaudi-vllm ps
```

Check logs: `docker compose logs <service_name>`. Pay attention to `vllm-gaudi-server` or `tgi-gaudi-server` logs for initialization status and errors.

### Run Validation Script/Commands

Use `curl` commands targeting the main service endpoints. Ensure `HOST_IP` is correctly set.

1.  **Validate LLM Serving Endpoint (Example for vLLM on default port 8000 internally, exposed differently):**

    ```bash
    # This command structure targets the OpenAI-compatible vLLM endpoint
    curl http://${HOST_IP}:8000/v1/chat/completions \
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

### Gradio UI (Default)

Access the default Gradio UI:
`http://{HOST_IP}:8080`
_(Port `8080` is the default host mapping)_

![Gradio UI](../../../../assets/img/codegen_gradio_ui_main.png)

### Svelte UI (Optional)

1.  Modify `compose.yaml`: Swap Gradio service for Svelte (`codegen-gaudi-ui-server`), check port map (e.g., `5173:5173`).
2.  Restart: `docker compose --profile <profile_name> up -d`
3.  Access: `http://{HOST_IP}:5173`

### React UI (Optional)

1.  Modify `compose.yaml`: Swap Gradio service for React (`codegen-gaudi-react-ui-server`), check port map (e.g., `5174:80`).
2.  Restart: `docker compose --profile <profile_name> up -d`
3.  Access: `http://{HOST_IP}:5174`

### VS Code Extension (Optional)

Use the `Neural Copilot` extension configured with the CodeGen backend URL: `http://${HOST_IP}:7778/v1/codegen`. (See Xeon README for detailed setup screenshots).

## Troubleshooting

- **Gaudi Service Issues:**
  - Check logs (`codegen-vllm-gaudi-server` or `codegen-tgi-gaudi-server`) for Habana/Gaudi specific errors.
  - Ensure host drivers and Habana Docker runtime are installed and working (`habana-container-runtime`).
  - Verify `runtime: habana` and volume mounts in `compose.yaml`.
  - Gaudi initialization can take significant time and memory. Monitor resource usage.
- **Model Download Issues:** Check `HUGGINGFACEHUB_API_TOKEN`, internet access, proxy settings. Check LLM service logs.
- **Connection Errors:** Verify `HOST_IP`, ports, and proxy settings. Use `docker ps` and check service logs.

## Stopping the Application

```bash
docker compose --profile <profile_name> down
# Example: docker compose --profile codegen-gaudi-vllm down
```

## Next Steps

- Experiment with different models supported by TGI/vLLM on Gaudi.
- Consult [OPEA GenAIComps](https://github.com/opea-project/GenAIComps) for microservice details.
- Refer to the main [CodeGen README](../../../../README.md) for benchmarking and Kubernetes deployment options.

```

```
