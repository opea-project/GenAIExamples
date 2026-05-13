[中文版](README_zh.md)

This directory contains the deployment, startup, and image build scripts for EdgeCraftRAG.

# 1.Script Overview

The main scripts in this directory are:

- `quick_start.sh`: recommended one-click deployment script for new users, with automatic setup and interactive guidance
- `bootstrap.sh`: non-interactive deployment orchestrator that can be used directly or invoked by `quick_start.sh`
- `model_download.sh`: model preparation helper (supports `vllm` / `ov`, optional `model_id` and `model_path` arguments)
- `run_ov_baremetal.sh`: OpenVINO bare-metal startup script
- `run_ov_container.sh`: OpenVINO container startup script
- `run_vllm_baremetal.sh`: vLLM bare-metal startup script
- `run_vllm_container.sh`: vLLM container startup script
- `run_ovms_baremetal.sh`: OVMS bare-metal startup script
- `run_ovms_container.sh`: OVMS container startup script
- `build_images.sh`: container image build script

Deployment methods:

| Method | Description | Requirements | Milvus Support |
|------|------|----------|-------------|
| baremetal | Start services as Python processes | Python 3.10+ | No (in-memory only) |
| container | Start services in Docker containers | Docker / Docker Compose | Yes (enabled by default) |

Note: If you need Milvus, use the container deployment method.

# 2.Quick Deployment Script (New Users)

## 2.1 One-Command Quick Deployment

Run this from the `EdgeCraftRAG` root directory:

```bash
./tools/quick_start.sh
```

The script behaves as follows by default:

- runs in non-interactive mode
- uses OpenVINO as the default inference backend
- if `INFERENCE_BACKEND` is not set, the script resolves it to `openvino`
- uses `baremetal` as the default deployment method when `DEPLOYMENT_METHOD` is not set

In the default bare-metal flow, the script automatically:

- creates and activates `EdgeCraftRAG/ecrag_venv` if it does not exist
- validates the Python version (3.10+ required, 3.10/3.11 recommended)
- checks and installs required Python packages
- checks and installs `npm` for baremetal UI startup when needed
- validates Intel GPU driver/runtime and auto-installs missing packages on apt-based Linux
- checks and auto-downloads missing models (embedding, reranker, OpenVINO LLM)
- writes a deployment environment snapshot to `workspace/bootstrap.env` before invoking `bootstrap.sh`
- calls `bootstrap.sh` to start services

For vLLM deployments and container deployment method, the script also validates Docker and Docker Compose before deployment.
On Ubuntu 24.04, if Docker or Docker Compose is missing, the script attempts automatic installation and starts/enables Docker service.

To skip model verification/download when models are already prepared locally:

```bash
./tools/quick_start.sh --skip-model-check
```

Equivalent environment variable:

```bash
export SKIP_MODEL_CHECK=1
./tools/quick_start.sh
```

Intel GPU driver/runtime validation can be skipped when needed:

```bash
./tools/quick_start.sh --skip-gpu-driver-check
```

Equivalent environment variables:

```bash
export SKIP_INTEL_GPU_DRIVER_CHECK=1
# Or keep validation but disable auto-install:
export AUTO_INSTALL_INTEL_GPU_DRIVER=0
./tools/quick_start.sh
```

To disable automatic npm installation during baremetal preparation:

```bash
export AUTO_INSTALL_NPM=0
./tools/quick_start.sh
```

After startup succeeds, the terminal prints a UI access URL such as:

```text
UI access URL: http://${HOST_IP}:8082
```

Note: If you set `DEPLOYMENT_METHOD=container` in advance, the script skips venv and pip checks and continues with container deployment.

You can override defaults with environment variables:

```bash
export INFERENCE_BACKEND=openvino
export MODEL_PATH="${PWD}/workspace/models"
export DOC_PATH="${PWD}/workspace"
export TMPFILE_PATH="${PWD}/workspace"
export LLM_MODEL="Qwen/Qwen3-8B"
export HOST_IP="$(hostname -I | awk '{print $1}')"

./tools/quick_start.sh
```

Select the backend with `INFERENCE_BACKEND`:

```bash
# OpenVINO (default)
./tools/quick_start.sh

# vLLM_A770
export INFERENCE_BACKEND=vllm_a770
./tools/quick_start.sh

# vLLM_B60
export INFERENCE_BACKEND=vllm_b60
./tools/quick_start.sh

# OVMS
export INFERENCE_BACKEND=ovms
export OVMS_SOURCE_MODEL=OpenVINO/Qwen3-8B-int4-ov
export OVMS_MODEL_NAME=OpenVINO/Qwen3-8B-int4-ov
export OVMS_TARGET_DEVICE=GPU.0
./tools/quick_start.sh
```

For OVMS deployments, the tooling now exports the compose-facing variables directly. The most commonly overridden ones are `OVMS_SOURCE_MODEL`, `OVMS_MODEL_NAME`, `OVMS_TARGET_DEVICE`, `OVMS_TOOL_PARSER`, and `OVMS_MAX_NUM_BATCHED_TOKENS`.

Important OVMS behavior:

- `OVMS_SOURCE_MODEL` keeps your original model ID as-is (for example `Qwen/Qwen3-8B`).
- `quick_start.sh` and `bootstrap.sh` both persist OVMS variables into `workspace/bootstrap.env` for reuse.
- You can replay the exact OVMS configuration with `source workspace/bootstrap.env && ./tools/bootstrap.sh`.

Compatibility note: the legacy environment variable `COMPOSE_PROFILES` is still accepted, but new configurations should use `INFERENCE_BACKEND`.

Supported `INFERENCE_BACKEND` values:

- `openvino`
- `vllm_a770`
- `vllm_b60`
- `ovms`

## 2.2 Interactive Mode

```bash
./tools/quick_start.sh -i
```

Interactive mode is suitable for first-time deployment or when you are not sure about the parameters. After you run `./tools/quick_start.sh -i`, the script prompts step by step and generates the deployment configuration for the current run.

The interactive flow typically includes:

- choosing the inference backend: OpenVINO / vLLM_A770 / vLLM_B60 / OVMS
- choosing the deployment method: baremetal / container
- configuring key parameters: `HOST_IP`, `MODEL_PATH`, `DOC_PATH`, `TMPFILE_PATH`, `LLM_MODEL`
- confirming the configuration and starting deployment, then printing the access URL at the end

Interactive mode is recommended when:

- this is your first installation and you are not familiar with the environment variables or defaults
- you need to switch quickly between different hardware targets or inference backends
- you want to review parameters before deployment to reduce configuration mistakes

Example:

```bash
cd EdgeCraftRAG
./tools/quick_start.sh -i
```

## 2.3 Common Interactive Input Examples

The following examples show common inputs during the interactive flow. Actual prompt text may vary slightly based on the script.

### Example A: OpenVINO + baremetal (single-machine quick experience)

```text
Inference backend: OpenVINO
Deployment method: baremetal
HOST_IP: 192.168.1.20
MODEL_PATH: /home/scale/edgeai/applications.edge.ai.rag/EdgeCraftRAG/workspace/models
DOC_PATH: /home/scale/edgeai/applications.edge.ai.rag/EdgeCraftRAG/workspace
TMPFILE_PATH: /home/scale/edgeai/applications.edge.ai.rag/EdgeCraftRAG/workspace
LLM_MODEL: Qwen/Qwen3-8B
Confirm deployment: y
```

### Example B: vLLM_B60 + container (Milvus required)

```text
Inference backend: vLLM_B60
Deployment method: container
HOST_IP: 192.168.1.20
MODEL_PATH: /home/scale/edgeai/applications.edge.ai.rag/EdgeCraftRAG/workspace/models
DOC_PATH: /home/scale/edgeai/applications.edge.ai.rag/EdgeCraftRAG/workspace
TMPFILE_PATH: /home/scale/edgeai/applications.edge.ai.rag/EdgeCraftRAG/workspace
LLM_MODEL: Qwen/Qwen3-8B
Confirm deployment: y
```

### Example C: vLLM_A770 + container (recommended for A770)

```text
Inference backend: vLLM_A770
Deployment method: container
HOST_IP: 192.168.1.20
MODEL_PATH: /home/scale/edgeai/applications.edge.ai.rag/EdgeCraftRAG/workspace/models
DOC_PATH: /home/scale/edgeai/applications.edge.ai.rag/EdgeCraftRAG/workspace
TMPFILE_PATH: /home/scale/edgeai/applications.edge.ai.rag/EdgeCraftRAG/workspace
LLM_MODEL: Qwen/Qwen3-8B
Confirm deployment: y
```

### Example D: OVMS + container

```text
Inference backend: OVMS
Deployment method: container
HOST_IP: 192.168.1.20
MODEL_PATH: /home/scale/edgeai/applications.edge.ai.rag/EdgeCraftRAG/workspace/models
DOC_PATH: /home/scale/edgeai/applications.edge.ai.rag/EdgeCraftRAG/workspace
TMPFILE_PATH: /home/scale/edgeai/applications.edge.ai.rag/EdgeCraftRAG/workspace
LLM_MODEL: Qwen/Qwen3-8B
Confirm deployment: y
```

Notes:

- for a remote server, set `HOST_IP` to an address reachable by the client machine
- if you need persistent vector retrieval data, use the container deployment method
- if the device is Intel Arc A770, prefer the `vllm_a770` configuration

Cleanup:

```bash
./tools/quick_start.sh cleanup
```

# 3.Startup Scripts

## 3.1 bootstrap.sh (Non-Interactive Orchestration)

Run with environment variables defined in advance:

```bash
export INFERENCE_BACKEND=openvino
export DEPLOYMENT_METHOD=baremetal
./tools/bootstrap.sh
```

Use defaults (`openvino` + `baremetal`):

```bash
./tools/bootstrap.sh
```

Configuration reuse:

- `quick_start.sh` writes `workspace/bootstrap.env` before real deployment starts.
- `bootstrap.sh` also persists configuration for reuse.
- For OVMS, this includes `OVMS_SOURCE_MODEL`, `OVMS_MODEL_NAME`, `OVMS_TARGET_DEVICE`, `OVMS_TOOL_PARSER`, and related `OVMS_*` runtime variables.

```bash
source workspace/bootstrap.env
./tools/bootstrap.sh
```

## 3.3 model_download.sh (Model Preparation)

Basic usage:

```bash
./tools/model_download.sh <mode> [model_id] [model_path]
```

Modes:

- `vllm`: prepare embedding/reranker OpenVINO models + vLLM LLM model
- `ov`: prepare embedding/reranker OpenVINO models + OpenVINO INT4 LLM model

Optional arguments:

- `model_id`: overrides `LLM_MODEL` for current run
- `model_path`: overrides `MODEL_PATH` for current run

Examples:

```bash
./tools/model_download.sh vllm
./tools/model_download.sh ov Qwen/Qwen3-8B /data/models
```

Environment behavior:

- if a virtual environment is already active, it is reused
- otherwise, the script creates/activates `ecrag_venv` automatically (same style as `quick_start.sh`)
- missing `python3-venv` / `pip` prerequisites are installed automatically when supported by the system package manager

## 3.2 Direct Startup Scripts

You can also call the following scripts directly based on inference backend and deployment method:

- OpenVINO baremetal: `./tools/run_ov_baremetal.sh`
- OpenVINO container: `./tools/run_ov_container.sh`
- vLLM baremetal: `./tools/run_vllm_baremetal.sh`
- vLLM container: `./tools/run_vllm_container.sh`
- OVMS baremetal: `./tools/run_ovms_baremetal.sh`
- OVMS container: `./tools/run_ovms_container.sh`

This is useful when you already know your parameters and want to skip the one-click onboarding flow.

# 4.Container Image Build Script

Build all images:

```bash
./tools/build_images.sh
```

Build by component:

```bash
./tools/build_images.sh mega
./tools/build_images.sh server
./tools/build_images.sh ui
./tools/build_images.sh all
```

For complete deployment guidance, see [../docs/Advanced_Setup.md](../docs/Advanced_Setup.md).
