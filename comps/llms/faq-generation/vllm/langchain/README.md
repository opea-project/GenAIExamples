# vLLM FAQGen LLM Microservice

This microservice interacts with the vLLM server to generate FAQs from Input Text.[vLLM](https://github.com/vllm-project/vllm) is a fast and easy-to-use library for LLM inference and serving, it delivers state-of-the-art serving throughput with a set of advanced features such as PagedAttention, Continuous batching and etc.. Besides GPUs, vLLM already supported [Intel CPUs](https://www.intel.com/content/www/us/en/products/overview.html) and [Gaudi accelerators](https://habana.ai/products).

## 🚀1. Start Microservice with Docker

If you start an LLM microservice with docker, the `docker_compose_llm.yaml` file will automatically start a VLLM service with docker.

To setup or build the vLLM image follow the instructions provided in [vLLM Gaudi](https://github.com/opea-project/GenAIComps/tree/main/comps/llms/text-generation/vllm/langchain#22-vllm-on-gaudi)

### 1.1 Setup Environment Variables

In order to start vLLM and LLM services, you need to setup the following environment variables first.

```bash
export HF_TOKEN=${your_hf_api_token}
export vLLM_ENDPOINT="http://${your_ip}:8008"
export LLM_MODEL_ID=${your_hf_llm_model}
```

### 1.3 Build Docker Image

```bash
cd ../../../../../
docker build -t opea/llm-faqgen-vllm:latest --build-arg https_proxy=$https_proxy --build-arg http_proxy=$http_proxy -f comps/llms/faq-generation/vllm/langchain/Dockerfile .
```

To start a docker container, you have two options:

- A. Run Docker with CLI
- B. Run Docker with Docker Compose

You can choose one as needed.

### 1.3 Run Docker with CLI (Option A)

```bash
docker run -d -p 8008:80 -v ./data:/data --name vllm-service --shm-size 1g opea/vllm-gaudi:latest --model-id ${LLM_MODEL_ID}
```

```bash
docker run -d --name="llm-faqgen-server" -p 9000:9000 --ipc=host -e http_proxy=$http_proxy -e https_proxy=$https_proxy -e vLLM_ENDPOINT=$vLLM_ENDPOINT -e HUGGINGFACEHUB_API_TOKEN=$HF_TOKEN opea/llm-faqgen-vllm:latest
```

### 1.4 Run Docker with Docker Compose (Option B)

```bash
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
# Streaming Response
# Set streaming to True. Default will be True.
curl http://${your_ip}:9000/v1/faqgen \
  -X POST \
  -d '{"query":"Text Embeddings Inference (TEI) is a toolkit for deploying and serving open source text embeddings and sequence classification models. TEI enables high-performance extraction for the most popular models, including FlagEmbedding, Ember, GTE and E5."}' \
  -H 'Content-Type: application/json'

# Non-Streaming Response
# Set streaming to False.
curl http://${your_ip}:9000/v1/faqgen \
  -X POST \
  -d '{"query":"Text Embeddings Inference (TEI) is a toolkit for deploying and serving open source text embeddings and sequence classification models. TEI enables high-performance extraction for the most popular models, including FlagEmbedding, Ember, GTE and E5.", "streaming":false}' \
  -H 'Content-Type: application/json'
```
