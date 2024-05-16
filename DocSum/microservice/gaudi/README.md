# Build MegaService of Document Summarization on Gaudi

This document outlines the deployment process for a Document Summarization application utilizing the [GenAIComps](https://github.com/opea-project/GenAIComps.git) microservice pipeline on Intel Gaudi server. The steps include Docker image creation, container deployment via Docker Compose, and service execution to integrate microservices such as llm. We will publish the Docker images to Docker Hub, it will simplify the deployment process for this service.

## 🚀 Build Docker Images

First of all, you need to build Docker Images locally. This step can be ignored after the Docker images published to Docker hub.

### 1. Source Code install GenAIComps

```bash
git clone https://github.com/opea-project/GenAIComps.git
cd GenAIComps
python setup.py install
```

### 2. Build TGI Gaudi Image

```bash
docker build . -t tgi-gaudi:1.2.1 --build-arg https_proxy=$https_proxy --build-arg http_proxy=$http_proxy 
```

### 3. Build LLM Image

```bash
docker build -t opea/gen-ai-comps:llm-tgi-gaudi-server --build-arg https_proxy=$https_proxy --build-arg http_proxy=$http_proxy -f comps/llms/docsum/langchain/docker/Dockerfile .
```

Then run the command `docker images`, you will have the following four Docker Images:

1. `tgi-gaudi:1.2.1`
2. `opea/gen-ai-comps:llm-tgi-server`

## 🚀 Start Microservices

### Setup Environment Variables

Since the `docker_compose.yaml` will consume some environment variables, you need to setup them in advance as below.

```bash
export http_proxy=${your_http_proxy}
export https_proxy=${your_http_proxy}
export LLM_MODEL_ID="Intel/neural-chat-7b-v3-3"
export TGI_LLM_ENDPOINT="http://${your_ip}:8008"
export HUGGINGFACEHUB_API_TOKEN=${your_hf_api_token}
```

### Start Microservice Docker Containers

```bash
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
curl http://${your_ip}:9000/v1/chat/completions \
  -X POST \
  -d '{"text":"Text Embeddings Inference (TEI) is a toolkit for deploying and serving open source text embeddings and sequence classification models. TEI enables high-performance extraction for the most popular models, including FlagEmbedding, Ember, GTE and E5."}' \
  -H 'Content-Type: application/json'
```

Following the validation of all aforementioned microservices, we are now prepared to construct a mega-service.

## 🚀 Construct Mega Service

Modify the `initial_inputs` of line 28 in `docsum.py`, then you will get the Document Summarization result of this mega service.

All of the intermediate results will be printed for each microservice. Users can check the accuracy of the results to make targeted modifications.

```bash
python docsum.py
```