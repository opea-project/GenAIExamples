Copyright (C) 2024 Advanced Micro Devices, Inc.

# Build and deploy DocSum Application on AMD GPU (ROCm)

## Build images

## 🚀 Build Docker Images

First of all, you need to build Docker Images locally and install the python package of it.

### 1. Build LLM Image

```bash
git clone https://github.com/opea-project/GenAIComps.git
cd GenAIComps
docker build -t opea/llm-docsum:latest --build-arg https_proxy=$https_proxy --build-arg http_proxy=$http_proxy -f comps/llms/src/doc-summarization/Dockerfile .
```

### 2. Build Whisper Image

```bash
cd GenAIComps
docker build -t opea/whisper:latest --build-arg https_proxy=$https_proxy --build-arg http_proxy=$http_proxy -f comps/asr/src/integrations/dependency/whisper/Dockerfile .
```

### 3. Build MegaService Docker Image

To construct the Mega Service, we utilize the [GenAIComps](https://github.com/opea-project/GenAIComps.git) microservice pipeline within the `docsum.py` Python script. Build the MegaService Docker image via below command:

```bash
git clone https://github.com/opea-project/GenAIExamples
cd GenAIExamples/DocSum/
docker build -t opea/docsum:latest --build-arg https_proxy=$https_proxy --build-arg http_proxy=$http_proxy -f Dockerfile .
```

### 4. Build Gradio UI Docker Image

Build the frontend Docker image via below command:

```bash
cd GenAIExamples/DocSum/ui
docker build -t opea/docsum-gradio-ui:latest --build-arg https_proxy=$https_proxy --build-arg http_proxy=$http_proxy -f docker/Dockerfile.gradio .
```

Then run the command `docker images`, you will have the following Docker Images:

1. `opea/llm-docsum:latest`
2. `opea/docsum:latest`
3. `opea/docsum-gradio-ui:latest`
4. `opea/llm-vllm-rocm:latest`
5. `opea/whisper:latest`

## 🚀 Start Microservices and MegaService

### Required Models

Default model is "Intel/neural-chat-7b-v3-3". Change "DOCSUM_LLM_MODEL_ID" in environment variables below if you want to use another model.
For gated models, you also need to provide [HuggingFace token](https://huggingface.co/docs/hub/security-tokens) in "HUGGINGFACEHUB_API_TOKEN" environment variable.

### Setup Environment Variables

```bash
export HUGGINGFACEHUB_API_TOKEN='your huggingfacehub token'
```

Edit the file set_env_vllm.sh - set the desired values of the variables in it
Note: Please replace value HOST_IP with your server IP address, do not use localhost.

Set values:
```bash
cd GenAiExamples/DocSum/docker_compose/amd/gpu/rocm
. set_env_vllm.sh
```

#### Set GPU settings in compose_vllm.yaml:
Note: In order to limit access to a subset of GPUs, please pass each device individually using one or more -device /dev/dri/rendered<node>, where <node> is the card index, starting from 128. (https://rocm.docs.amd.com/projects/install-on-linux/en/latest/how-to/docker.html#docker-restrict-gpus)
Example for set isolation for 1 GPU

```
      - /dev/dri/card0:/dev/dri/card0
      - /dev/dri/renderD128:/dev/dri/renderD128
```

Example for set isolation for 2 GPUs

```
      - /dev/dri/card0:/dev/dri/card0
      - /dev/dri/renderD128:/dev/dri/renderD128
      - /dev/dri/card1:/dev/dri/card1
      - /dev/dri/renderD129:/dev/dri/renderD129
```

Please find more information about accessing and restricting AMD GPUs in the link (https://rocm.docs.amd.com/projects/install-on-linux/en/latest/how-to/docker.html#docker-restrict-gpus)

### Start Microservice Docker Containers

```bash
cd GenAIExamples/DocSum/docker_compose/amd/gpu/rocm
docker compose -f compose_vllm.yaml up -d
```

### Validate Microservices

1. vLLM Service

   ```bash
   curl http://${host_ip}:${DOCSUM_VLLM_SERVICE_PORT}/v1/chat/completions \
     -X POST \
     -d '{"model": "Intel/neural-chat-7b-v3-3", "messages": [{"role": "user", "content": "What is Deep Learning?"}], "max_tokens": 17}' \
     -H 'Content-Type: application/json'
   ```

2. LLM Microservice

   ```bash
   curl http://${host_ip}:${DOCSUM_LLM_SERVER_PORT}/v1/docsum \
     -X POST \
     -d '{"messages":"What is Deep Learning?"}' \
     -H 'Content-Type: application/json'
   ```

3. MegaService

   ```bash
   curl http://${host_ip}:${DOCSUM_BACKEND_SERVER_PORT}/v1/docsum -H "Content-Type: application/json" -d '{"type": "text", "messages": "Text Embeddings Inference (TEI) is a toolkit for deploying and serving open source text embeddings and sequence classification models. TEI enables high-performance extraction for the most popular models, including FlagEmbedding, Ember, GTE and E5."}'
   ```
