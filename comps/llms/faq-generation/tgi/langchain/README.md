# TGI FAQGen LLM Microservice

This microservice interacts with the TGI LLM server to generate FAQs from Input Text.[Text Generation Inference](https://github.com/huggingface/text-generation-inference) (TGI) is a toolkit for deploying and serving Large Language Models (LLMs). TGI enables high-performance text generation for the most popular open-source LLMs, including Llama, Falcon, StarCoder, BLOOM, GPT-NeoX, and more.

## 🚀1. Start Microservice with Docker

If you start an LLM microservice with docker, the `docker_compose_llm.yaml` file will automatically start a TGI service with docker.

### 1.1 Setup Environment Variables

In order to start TGI and LLM services, you need to setup the following environment variables first.

```bash
export HF_TOKEN=${your_hf_api_token}
export TGI_LLM_ENDPOINT="http://${your_ip}:8008"
export LLM_MODEL_ID=${your_hf_llm_model}
```

### 1.2 Build Docker Image

```bash
cd ../../../../
docker build -t opea/llm-faqgen-tgi:latest --build-arg https_proxy=$https_proxy --build-arg http_proxy=$http_proxy -f comps/llms/faq-generation/tgi/langchain/Dockerfile .
```

To start a docker container, you have two options:

- A. Run Docker with CLI
- B. Run Docker with Docker Compose

You can choose one as needed.

### 1.3 Run Docker with CLI (Option A)

```bash
docker run -d -p 8008:80 -v ./data:/data --name tgi_service --shm-size 1g ghcr.io/huggingface/text-generation-inference:1.4 --model-id ${LLM_MODEL_ID}
```

```bash
docker run -d --name="llm-faqgen-server" -p 9000:9000 --ipc=host -e http_proxy=$http_proxy -e https_proxy=$https_proxy -e TGI_LLM_ENDPOINT=$TGI_LLM_ENDPOINT -e HUGGINGFACEHUB_API_TOKEN=$HF_TOKEN opea/llm-faqgen-tgi:latest
```

### 1.4 Run Docker with Docker Compose (Option B)

```bash
cd faq-generation/tgi/docker
docker compose -f docker_compose_llm.yaml up -d
```

## 🚀3. Consume LLM Service

### 3.1 Check Service Status

```bash
curl http://${your_ip}:9000/v1/health_check\
  -X GET \
  -H 'Content-Type: application/json'
```

### 3.2 Consume FAQGen LLM Service

```bash
curl http://${your_ip}:9000/v1/faqgen \
  -X POST \
  -d '{"query":"Text Embeddings Inference (TEI) is a toolkit for deploying and serving open source text embeddings and sequence classification models. TEI enables high-performance extraction for the most popular models, including FlagEmbedding, Ember, GTE and E5."}' \
  -H 'Content-Type: application/json'
```
