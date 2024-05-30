# Build MegaService of Document Summarization on Gaudi

This document outlines the deployment process for a Document Summarization application utilizing the [GenAIComps](https://github.com/opea-project/GenAIComps.git) microservice pipeline on Intel Gaudi server. The steps include Docker image creation, container deployment via Docker Compose, and service execution to integrate microservices such as llm. We will publish the Docker images to Docker Hub, which will simplify the deployment process for this service.

## 🚀 Build Docker Images

First of all, you need to build Docker Images locally. This step can be ignored once the Docker images are published to Docker hub.

```bash
git clone https://github.com/opea-project/GenAIComps.git
cd GenAIComps
```

### 1. Pull TGI Gaudi Image

As TGI Gaudi has been officially published as a Docker image, we simply need to pull it:

```bash
docker pull ghcr.io/huggingface/tgi-gaudi:1.2.1
```

### 2. Build LLM Image

```bash
docker build -t opea/llm-docsum-tgi:latest --build-arg https_proxy=$https_proxy --build-arg http_proxy=$http_proxy -f comps/llms/docsum/langchain/docker/Dockerfile .
```

### 3. Build MegaService Docker Image

To construct the Mega Service, we utilize the [GenAIComps](https://github.com/opea-project/GenAIComps.git) microservice pipeline within the `docsum.py` Python script. Build the MegaService Docker image using the command below:

```bash
git clone https://github.com/opea-project/GenAIExamples
cd GenAIExamples/DocSum/docker
docker build -t opea/docsum:latest --build-arg https_proxy=$https_proxy --build-arg http_proxy=$http_proxy -f Dockerfile .
```

### 4. Build UI Docker Image

Construct the frontend Docker image using the command below:

```bash
cd GenAIExamples/DocSum/ui/
docker build -t opea/docsum-ui:latest --build-arg https_proxy=$https_proxy --build-arg http_proxy=$http_proxy -f ./docker/Dockerfile .
```

Then run the command `docker images`, you will have the following Docker Images:

1. `ghcr.io/huggingface/tgi-gaudi:1.2.1`
2. `opea/llm-docsum-tgi:latest`
3. `opea/docsum:latest`
4. `opea/docsum-ui:latest`

## 🚀 Start Microservices and MegaService

### Setup Environment Variables

Since the `docker_compose.yaml` will consume some environment variables, you need to setup them in advance as below.

```bash
export http_proxy=${your_http_proxy}
export https_proxy=${your_http_proxy}
export LLM_MODEL_ID="Intel/neural-chat-7b-v3-3"
export TGI_LLM_ENDPOINT="http://${your_ip}:8008"
export HUGGINGFACEHUB_API_TOKEN=${your_hf_api_token}
export MEGA_SERVICE_HOST_IP=${host_ip}
export LLM_SERVICE_HOST_IP=${host_ip}
export BACKEND_SERVICE_ENDPOINT="http://${host_ip}:8888/v1/docsum"
```

Note: Please replace with `host_ip` with your external IP address, do not use localhost.

### Start Microservice Docker Containers

```bash
cd GenAIExamples/DocSum/docker-composer/gaudi
docker compose -f docker_compose.yaml up -d
```

### Validate Microservices

1. TGI Service

```bash
curl http://${your_ip}:8008/generate \
  -X POST \
  -d '{"inputs":"What is Deep Learning?","parameters":{"max_new_tokens":64, "do_sample": true}}' \
  -H 'Content-Type: application/json'
```

2. LLM Microservice

```bash
curl http://${your_ip}:9000/v1/chat/docsum \
  -X POST \
  -d '{"query":"Text Embeddings Inference (TEI) is a toolkit for deploying and serving open source text embeddings and sequence classification models. TEI enables high-performance extraction for the most popular models, including FlagEmbedding, Ember, GTE and E5."}' \
  -H 'Content-Type: application/json'
```

3. MegaService

```bash
curl http://${host_ip}:8888/v1/docsum -H "Content-Type: application/json" -d '{
     "messages": "Text Embeddings Inference (TEI) is a toolkit for deploying and serving open source text embeddings and sequence classification models. TEI enables high-performance extraction for the most popular models, including FlagEmbedding, Ember, GTE and E5."
     }'
```

## Enable LangSmith to Monitor an Application (Optional)

LangSmith offers a suite of tools to debug, evaluate, and monitor language models and intelligent agents. It can be used to assess benchmark data for each microservice. Before launching your services with `docker compose -f docker_compose.yaml up -d`, you need to enable LangSmith tracing by setting the `LANGCHAIN_TRACING_V2` environment variable to true and configuring your LangChain API key.

Here's how you can do it:

1. Install the latest version of LangSmith:

```bash
pip install -U langsmith
```

2. Set the necessary environment variables:

```bash
export LANGCHAIN_TRACING_V2=true
export LANGCHAIN_API_KEY=ls_...
```

## 🚀 Launch the UI

Open this URL `http://{host_ip}:5173` in your browser to access the frontend.

![project-screenshot](https://i.imgur.com/26zMnEr.png)
