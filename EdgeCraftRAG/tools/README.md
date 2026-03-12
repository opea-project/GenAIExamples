# EdgeCraftRAG tool scripts

[中文版](README_zh.md)

This directory contains helper scripts for building images and starting EC-RAG services.

## Scripts

- `quick_start.sh`: one-click startup for OpenVINO or vLLM deployment
- `build_images.sh`: build EC-RAG Docker images

---

## quick_start.sh

Run from the `EdgeCraftRAG` root directory:

```bash
./tools/quick_start.sh
```

### Default behavior

If no environment variables are provided, the script uses these defaults:

```bash
MODEL_PATH=${WORKSPACE}/workspace/models
DOC_PATH=${WORKSPACE}/workspace
TMPFILE_PATH=${WORKSPACE}/workspace
LLM_MODEL=Qwen/Qwen3-8B
```

The script will also:

- create and activate a Python virtual environment automatically
- install `python3-venv` if needed
- check whether required models exist under `MODEL_PATH`
- automatically download missing embedding, reranker, and LLM models
- print the UI access URL after startup completes

### Non-interactive mode

By default, non-interactive mode starts local OpenVINO services.

```bash
./tools/quick_start.sh
```

You can override defaults with environment variables:

```bash
export MODEL_PATH="${PWD}/workspace/models"
export DOC_PATH="${PWD}/workspace"
export TMPFILE_PATH="${PWD}/workspace"
export LLM_MODEL="Qwen/Qwen3-8B"
export HOST_IP="$(hostname -I | awk '{print $1}')"

./tools/quick_start.sh
```

### Select deployment mode with `COMPOSE_PROFILES`

#### OpenVINO on Core Ultra, B60 or A770

```bash
./tools/quick_start.sh
```

#### vLLM on Intel Arc A770

```bash
export COMPOSE_PROFILES=vLLM_A770
./tools/quick_start.sh
```

#### vLLM on Intel Arc B60

```bash
export COMPOSE_PROFILES=vLLM_B60
./tools/quick_start.sh
```

Optional B60/vLLM variables:

```bash
export VLLM_SERVICE_PORT_B60=8086
export DTYPE=float16
export TP=1
export DP=1
export ZE_AFFINITY_MASK=0
export ENFORCE_EAGER=1
export TRUST_REMOTE_CODE=1
export DISABLE_SLIDING_WINDOW=1
export GPU_MEMORY_UTIL=0.8
export NO_ENABLE_PREFIX_CACHING=1
export MAX_NUM_BATCHED_TOKENS=8192
export DISABLE_LOG_REQUESTS=1
export MAX_MODEL_LEN=49152
export BLOCK_SIZE=64
export QUANTIZATION=fp8
```

### Interactive mode

```bash
bash -i ./tools/quick_start.sh
```

In interactive mode, the script prompts for:

- deployment mode: `vLLM_A770`, `vLLM_B60`, or `ov`
- `HOST_IP`
- `DOC_PATH`
- `TMPFILE_PATH`
- `MODEL_PATH`
- `LLM_MODEL`
- optional vLLM runtime settings

### Model check and auto-download

The script checks these model locations automatically:

#### Shared models

```text
${MODEL_PATH}/BAAI/bge-small-en-v1.5
${MODEL_PATH}/BAAI/bge-reranker-large
```

#### vLLM mode

```text
${MODEL_PATH}/${LLM_MODEL}
```

#### OpenVINO mode

```text
${MODEL_PATH}/${LLM_MODEL}/INT4_compressed_weights
```

If a required model is missing, the script downloads it automatically and prints a message.

### UI access output

After startup completes, the script prints:

```text
Service launched successfully.
UI access URL: http://${HOST_IP}:8082
If you are accessing from another machine, replace ${HOST_IP} with the server's reachable IP or hostname.
```

### Cleanup

To stop and remove the deployed containers:

```bash
./tools/quick_start.sh cleanup
```

---

## build_images.sh

Build all images:

```bash
./tools/build_images.sh
```

Build selected images only:

```bash
./tools/build_images.sh mega
./tools/build_images.sh server
./tools/build_images.sh ui
./tools/build_images.sh all
```

For full deployment details, refer to [../docs/Advanced_Setup.md](../docs/Advanced_Setup.md).
