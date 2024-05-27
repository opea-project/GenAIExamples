# Build Mega Service of CodeTrans on Gaudi

This document outlines the deployment process for a CodeTrans application utilizing the [GenAIComps](https://github.com/opea-project/GenAIComps.git) microservice pipeline on Intel Gaudi server. The steps include Docker image creation, container deployment via Docker Compose, and service execution using microservices `llm`. We will publish the Docker images to Docker Hub soon, it will simplify the deployment process for this service.

## 🚀 Build Docker Images

First of all, you need to build Docker Images locally and install the python package of it. This step can be ignored after the Docker images published to Docker hub.

### 1. Source Code install GenAIComps

```bash
git clone https://github.com/opea-project/GenAIComps.git
cd GenAIComps
```

### 2. Build the LLM Docker Image with the following command

```bash
docker build -t opea/gen-ai-comps:llm-tgi-gaudi-server --no-cache --build-arg https_proxy=$https_proxy --build-arg http_proxy=$http_proxy -f comps/llms/text-generation/tgi/Dockerfile .
```

### 3. Build MegaService Docker Image

```bash
git clone https://github.com/opea-project/GenAIExamples.git
cd GenAIExamples/CodeTrans
docker build -t opea/gen-ai-comps:codetrans-megaservice-server --build-arg https_proxy=$https_proxy --build-arg http_proxy=$http_proxy -f Dockerfile .
```

### 4. Build UI Docker Image

```bash
cd GenAIExamples/CodeTrans/ui
docker build -t opea/gen-ai-comps:codetrans-ui-server --build-arg https_proxy=$https_proxy --build-arg http_proxy=$http_proxy -f ./docker/Dockerfile .
```

Then run the command `docker images`, you will have the following Docker Images:

- `opea/gen-ai-comps:llm-tgi-gaudi-server`
- `opea/gen-ai-comps:codetrans-megaservice-server`
- `opea/gen-ai-comps:codetrans-ui-server`

## 🚀 Start Microservices

### Setup Environment Variables

Since the `docker_compose.yaml` will consume some environment variables, you need to setup them in advance as below. Notice that the `LLM_MODEL_ID` indicates the LLM model used for TGI service.

```bash
export http_proxy=${your_http_proxy}
export https_proxy=${your_http_proxy}
export LLM_MODEL_ID="HuggingFaceH4/mistral-7b-grok"
export TGI_LLM_ENDPOINT="http://${host_ip}:8008"
export HUGGINGFACEHUB_API_TOKEN=${your_hf_api_token}
export MEGA_SERVICE_HOST_IP=${host_ip}
export LLM_SERVICE_HOST_IP=${host_ip}
export BACKEND_SERVICE_ENDPOINT="http://${host_ip}:7777/v1/codetrans"
```

### Start Microservice Docker Containers

```bash
cd GenAIExamples/CodeTrans/docker-composer/gaudi
docker compose -f docker_compose.yaml up -d
```

### Validate Microservices

1. TGI Service

```bash
curl http://${host_ip}:8008/generate \
  -X POST \
  -d '{"inputs":"    ### System: Please translate the following Golang codes into  Python codes.    ### Original codes:    '\'''\'''\''Golang    \npackage main\n\nimport \"fmt\"\nfunc main() {\n    fmt.Println(\"Hello, World!\");\n    '\'''\'''\''    ### Translated codes:","parameters":{"max_new_tokens":17, "do_sample": true}}' \
  -H 'Content-Type: application/json'
```

2. LLM Microservice

```bash
curl http://${host_ip}:9000/v1/chat/completions\
  -X POST \
  -d '{"text":"    ### System: Please translate the following Golang codes into  Python codes.    ### Original codes:    '\'''\'''\''Golang    \npackage main\n\nimport \"fmt\"\nfunc main() {\n    fmt.Println(\"Hello, World!\");\n    '\'''\'''\''    ### Translated codes:"}' \
  -H 'Content-Type: application/json'
```

3. MegaService

```bash
curl http://${host_ip}:7777/v1/codetrans \
    -H "Content-Type: application/json" \
    -d '{"language_from": "Golang","language_to": "Python","source_code": "package main\n\nimport \"fmt\"\nfunc main() {\n    fmt.Println(\"Hello, World!\");\n}"}'
```
