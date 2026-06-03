# Deploy CodeGen Application on Intel Arc GPU (XPU) with Docker Compose

This README provides instructions for deploying the CodeGen application using Docker Compose on a system equipped with Intel Arc Pro B-series GPUs, detailing the steps to configure, run, and validate the services. This guide uses the **vLLM** backend optimized for Intel XPU for LLM serving.

## Table of Contents

- [Overview](#overview)
- [Prerequisites](#prerequisites)
- [Quick Start](#quick-start)
- [Configuration Parameters](#configuration-parameters)
  - [Environment Variables](#environment-variables)
- [Deploy the Services Using Docker Compose](#deploy-the-services-using-docker-compose)
- [Validate Services](#validate-services)
  - [Check Container Status](#check-container-status)
  - [Test the Pipeline](#test-the-pipeline)
- [Accessing the User Interface (UI)](#accessing-the-user-interface-ui)
- [Troubleshooting](#troubleshooting)
- [Stopping the Application](#stopping-the-application)
- [Next Steps](#next-steps)

## Overview

This guide focuses on running the pre-configured CodeGen service using Docker Compose on Intel Arc Pro B-series GPU platform. It leverages containers optimized for Intel XPU architecture for LLM serving using vLLM, along with the CodeGen gateway and UI components.

## Prerequisites

- Docker and Docker Compose installed
- Intel Arc Pro B-series GPU (or compatible Intel discrete GPU)
- Intel GPU drivers installed and properly configured
- Git installed (for cloning repository)
- Hugging Face Hub API Token (for downloading models)
- Access to the internet (or a private model cache)
- Clone the `GenAIExamples` repository:

```bash
git clone https://github.com/opea-project/GenAIExamples.git
cd GenAIExamples/CodeGen/docker_compose/intel/xpu/arc/
```

Checkout a released version, such as v1.3:

```bash
git checkout v1.3
```

## Quick Start

### 1. Generate a HuggingFace Access Token

Some HuggingFace resources, such as some models, are only accessible if you have an access token. If you do not already have a HuggingFace access token, you can create one by first creating an account by following the steps provided at [HuggingFace](https://huggingface.co/) and then generating a [user access token](https://huggingface.co/docs/transformers.js/en/guides/private#step-1-generating-a-user-access-token).

### 2. Configure the Deployment Environment

Set up environment variables for deploying CodeGen services:

```bash
# Replace with your host's external IP address (do not use localhost or 127.0.0.1)
export HOST_IP=$(hostname -I | awk '{print $1}')
# Replace with your Hugging Face Hub API token
export HF_TOKEN="your_huggingface_token"

# Optional: Configure proxy if needed
# export http_proxy="your_http_proxy"
# export https_proxy="your_https_proxy"
# export no_proxy="localhost,127.0.0.1,${HOST_IP}"
source ./set_env.sh
```

### 3. Deploy the Services Using Docker Compose

```bash
docker compose up -d
```

This will start the following services:

- **codegen-vllm-service**: vLLM service optimized for Intel XPU
- **codegen-llm-server**: LLM microservice that interfaces with vLLM
- **codegen-backend-server**: CodeGen backend (MegaService)
- **codegen-ui-server**: Web UI for CodeGen

### 4. Check the Deployment Status

Monitor the logs to ensure all services start successfully:

```bash
docker compose logs -f
```

Check container status:

```bash
docker ps
```

All containers should show as healthy or running.

## Configuration Parameters

### Environment Variables

Key parameters are configured via environment variables set in `set_env.sh`:

| Environment Variable           | Description                                                                                           | Default Value                    |
| :----------------------------- | :---------------------------------------------------------------------------------------------------- | :------------------------------- |
| `HOST_IP`                      | External IP address of the host machine. **Required.** Must be exported before sourcing `set_env.sh`. | _None_                           |
| `HF_TOKEN`                     | Your Hugging Face Hub token for model access. **Required.**                                           | `${HF_TOKEN}`                    |
| `CODEGEN_LLM_MODEL_ID`         | Hugging Face model ID for the CodeGen LLM                                                             | `Qwen/Qwen2.5-Coder-7B-Instruct` |
| `CODEGEN_VLLM_SERVICE_PORT`    | Port for vLLM service                                                                                 | `8028`                           |
| `CODEGEN_LLM_SERVICE_PORT`     | Port for LLM microservice                                                                             | `9000`                           |
| `CODEGEN_BACKEND_SERVICE_PORT` | Port for CodeGen backend service                                                                      | `7778`                           |
| `CODEGEN_UI_SERVICE_PORT`      | Port for CodeGen UI                                                                                   | `5173`                           |
| `MODEL_CACHE`                  | Directory for model cache                                                                             | `./data`                         |
| `REGISTRY`                     | Docker registry for OPEA images                                                                       | `opea`                           |
| `TAG`                          | Docker image tag                                                                                      | `latest`                         |
| `http_proxy` / `https_proxy`   | Network proxy settings (if required)                                                                  | `""`                             |
| `no_proxy`                     | No proxy list                                                                                         | Includes localhost and `HOST_IP` |

### Intel XPU Specific Environment Variables

The following environment variables are set in the vLLM service for Intel XPU optimization:

- `VLLM_TARGET_DEVICE: "xpu"` - Targets Intel XPU devices
- `VLLM_LOGGING_LEVEL: "DEBUG"` - Sets logging level for debugging
- `ZE_FLAT_DEVICE_HIERARCHY: "FLAT"` - Level Zero driver configuration
- `ONEAPI_DEVICE_SELECTOR: "level_zero:gpu;opencl:gpu"` - Device selector for oneAPI

## Deploy the Services Using Docker Compose

```bash
cd GenAIExamples/CodeGen/docker_compose/intel/xpu/arc/
docker compose up -d
```

### Wait for Services to Be Ready

The vLLM service may take several minutes to download the model and initialize. Monitor progress:

```bash
docker compose logs -f codegen-vllm-service
```

Wait for a message indicating the server is ready to accept requests.

## Validate Services

### Check Container Status

```bash
docker ps
```

Expected output should show all four containers running:

- `codegen-vllm-service` (healthy)
- `codegen-llm-server` (running)
- `codegen-backend-server` (running)
- `codegen-ui-server` (running)

### Test the vLLM Service

```bash
curl http://${HOST_IP}:8028/v1/completions \
  -H "Content-Type: application/json" \
  -d '{
    "model": "Qwen/Qwen2.5-Coder-7B-Instruct",
    "prompt": "def fibonacci(n):",
    "max_tokens": 100,
    "temperature": 0.7
  }'
```

### Test the LLM Microservice

```bash
curl http://${HOST_IP}:9000/v1/chat/completions \
  -X POST \
  -H "Content-Type: application/json" \
  -d '{
    "query": "Write a Python function to calculate factorial"
  }'
```

### Test the CodeGen Backend Service

```bash
curl http://${HOST_IP}:7778/v1/codegen \
  -X POST \
  -H "Content-Type: application/json" \
  -d '{
    "messages": "Write a function to sort an array in Python"
  }'
```

## Accessing the User Interface (UI)

Once all services are running and validated, access the CodeGen UI:

```bash
http://${HOST_IP}:5173
```

Open this URL in your web browser. You should see the CodeGen interface where you can:

- Enter natural language prompts for code generation
- View generated code
- Interact with the CodeGen assistant

## Troubleshooting

### GPU Not Detected

If vLLM cannot detect the Intel GPU:

1. Verify GPU drivers are installed:

   ```bash
   clinfo
   ```

2. Check device permissions:

   ```bash
   ls -la /dev/dri
   ```

3. Verify the container has access to `/dev/dri`:
   ```bash
   docker compose exec codegen-vllm-service ls -la /dev/dri
   ```

### vLLM Service Fails to Start

1. Check logs for errors:

   ```bash
   docker compose logs codegen-vllm-service
   ```

2. Common issues:
   - Model download failed: Check HF_TOKEN and network connectivity
   - Out of memory: Reduce model size or adjust `shm_size` in compose.yaml
   - Driver issues: Update Intel GPU drivers

### Service Cannot Connect

1. Check network connectivity between containers:

   ```bash
   docker compose exec codegen-llm-server ping codegen-vllm-service
   ```

2. Verify environment variables are set correctly:
   ```bash
   docker compose config
   ```

### Performance Issues

1. Monitor GPU utilization:

   ```bash
   intel_gpu_top
   ```

2. Check container resource usage:
   ```bash
   docker stats
   ```

## Stopping the Application

To stop all services:

```bash
docker compose down
```

To also remove volumes (model cache):

```bash
docker compose down -v
```

## Next Steps

- **Customize the Model**: Change `CODEGEN_LLM_MODEL_ID` in `set_env.sh` to use a different model
- **Adjust Resources**: Modify `shm_size` and resource limits in `compose.yaml`
- **Enable Monitoring**: Add Prometheus and Grafana for monitoring (see main README)
- **Scale Services**: Deploy multiple vLLM instances for load balancing
- **Integrate with IDE**: Use the CodeGen API endpoint with your IDE or code editor

## Additional Resources

- [OPEA Project Documentation](https://opea-project.github.io/)
- [vLLM Documentation](https://docs.vllm.ai/)
- [Intel GPU Drivers](https://dgpu-docs.intel.com/)
- [GenAIComps Repository](https://github.com/opea-project/GenAIComps)

## Support

For issues and questions:

- Open an issue in the [GenAIExamples repository](https://github.com/opea-project/GenAIExamples/issues)
- Check existing documentation and examples
- Join the OPEA community discussions
