# Build MegaService of CodeGen on Gaudi

This document outlines the deployment process for a CodeGen application utilizing the [GenAIComps](https://github.com/opea-project/GenAIComps.git) microservice pipeline on Intel Gaudi server. The steps include Docker image creation, container deployment via Docker Compose, and service execution to integrate microservices such as `llm`. We will publish the Docker images to Docker Hub, it will simplify the deployment process for this service.

## 🚀 Build Docker Images

First of all, you need to build Docker Images locally. This step can be ignored after the Docker images published to Docker hub.

### 1. Git clone GenAIComps

```bash
git clone https://github.com/opea-project/GenAIComps.git
cd GenAIComps
```

### 2. Build LLM Image

```bash
docker build -t opea/gen-ai-comps:llm-tgi-gaudi-server --build-arg https_proxy=$https_proxy --build-arg http_proxy=$http_proxy -f comps/llms/langchain/docker/Dockerfile .
```

### 3. Build MegaService Docker Image

To construct the Mega Service, we utilize the [GenAIComps](https://github.com/opea-project/GenAIComps.git) microservice pipeline within the `codegen.py` Python script. Build the MegaService Docker image using the command below:

```bash
git clone https://github.com/opea-project/GenAIExamples
cd GenAIExamples/CodeGen/microservice/gaudi/
docker build -t opea/gen-ai-comps:codegen-megaservice-server --build-arg https_proxy=$https_proxy --build-arg http_proxy=$http_proxy -f docker/Dockerfile .
```

### 4. Build UI Docker Image

Construct the frontend Docker image using the command below:

```bash
cd GenAIExamples/CodeGen/ui/
docker build -t opea/gen-ai-comps:codegen-ui-server --build-arg https_proxy=$https_proxy --build-arg http_proxy=$http_proxy -f ./docker/Dockerfile .
```

Then run the command `docker images`, you will have the following 7 Docker Images:

1. `opea/gen-ai-comps:llm-tgi-server`
2. `opea/gen-ai-comps:codegen-megaservice-server`
3. `opea/gen-ai-comps:codegen-ui-server`

## 🚀 Start MicroServices and MegaService

### Setup Environment Variables

Since the `docker_compose.yaml` will consume some environment variables, you need to setup them in advance as below.

```bash
export http_proxy=${your_http_proxy}
export https_proxy=${your_http_proxy}
export LLM_MODEL_ID="ise-uiuc/Magicoder-S-DS-6.7B"
export TGI_LLM_ENDPOINT="http://${host_ip}:8008"
export HUGGINGFACEHUB_API_TOKEN=${your_hf_api_token}
export MEGA_SERVICE_HOST_IP=${host_ip}
export BACKEND_SERVICE_ENDPOINT="http://${host_ip}:6666/v1/codegen"
```

Note: Please replace with `host_ip` with you external IP address, do not use localhost.

### Start all the services Docker Containers

```bash
docker compose -f docker_compose.yaml up -d
```

### Validate MicroServices and MegaService

1. TGI Service

```bash
curl http://${host_ip}:8008/generate \
  -X POST \
  -d '{"inputs":"Write a function that checks if a year is a leap year in Python.","parameters":{"max_new_tokens":128, "do_sample": true}}' \
  -H 'Content-Type: application/json'
```

2. LLM Microservice

```bash
curl http://${host_ip}:9000/v1/chat/completions\
  -X POST \
  -d '{"query":"Write a function that checks if a year is a leap year in Python.","max_new_tokens":128,"top_k":10,"top_p":0.95,"typical_p":0.95,"temperature":0.01,"repetition_penalty":1.03,"streaming":true}' \
  -H 'Content-Type: application/json'
```

3. MegaService

```bash
curl http://${host_ip}:6666/v1/codegen -H "Content-Type: application/json" -d '{
     "model": "ise-uiuc/Magicoder-S-DS-6.7B",
     "messages": "Write a function that checks if a year is a leap year in Python."
     }'
```

## 🚀 Launch the UI

To access the frontend, open the following URL in your browser: http://{host_ip}:5173. By default, the UI runs on port 5173 internally. If you prefer to use a different host port to access the frontend, you can modify the port mapping in the `docker_compose.yaml` file as shown below:

```yaml
  chaqna-gaudi-ui-server:
    image: opea/gen-ai-comps:codegen-ui-server
    ...
    ports:
      - "80:5173"
```

![project-screenshot](https://imgur.com/d1SmaRb.png)
