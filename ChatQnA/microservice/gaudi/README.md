# Build MegaService of ChatQnA on Gaudi

This document outlines the deployment process for a ChatQnA application utilizing the [GenAIComps](https://github.com/opea-project/GenAIComps.git) microservice pipeline on Intel Gaudi server. The steps include Docker image creation, container deployment via Docker Compose, and service execution to integrate microservices such as embedding, retriever, rerank, and llm. We will publish the Docker images to Docker Hub, it will simplify the deployment process for this service.

## 🚀 Build Docker Images

First of all, you need to build Docker Images locally. This step can be ignored after the Docker images published to Docker hub.

### 1. Source Code install GenAIComps

```bash
git clone https://github.com/opea-project/GenAIComps.git
cd GenAIComps
python setup.py install
```

### 2. Build Embedding Image

```bash
docker build -t opea/gen-ai-comps:embedding-tei-server --build-arg https_proxy=$https_proxy --build-arg http_proxy=$http_proxy -f comps/embeddings/langchain/docker/Dockerfile .
```

### 3. Build Retriever Image

```bash
docker build -t opea/gen-ai-comps:retriever-redis-server --build-arg https_proxy=$https_proxy --build-arg http_proxy=$http_proxy -f comps/retrievers/langchain/docker/Dockerfile .
```

### 4. Build Rerank Image

```bash
docker build -t opea/gen-ai-comps:reranking-tei-server --build-arg https_proxy=$https_proxy --build-arg http_proxy=$http_proxy -f comps/reranks/docker/Dockerfile .
```

### 5. Build LLM Image

```bash
docker build -t opea/gen-ai-comps:llm-tgi-gaudi-server --build-arg https_proxy=$https_proxy --build-arg http_proxy=$http_proxy -f comps/llms/langchain/docker/Dockerfile .
```

### 6. Build TEI Gaudi Image

Since a TEI Gaudi Docker image hasn't been published, we'll need to build it from the [tei-guadi](https://github.com/huggingface/tei-gaudi) repository.

```bash
cd ..
git clone https://github.com/huggingface/tei-gaudi
cd tei-gaudi/
docker build -f Dockerfile-hpu -t opea/tei-gaudi .
```

### 7. Pull TGI Gaudi Image

As TGI Gaudi has been officially published as a Docker image, we simply need to pull it.

```bash
docker pull ghcr.io/huggingface/tgi-gaudi:1.2.1
```

### 8. Pull TEI Xeon Image

Since TEI Gaudi doesn't support reranking models, we'll deploy TEI CPU serving instead. TEI CPU has been officially released as a Docker image, so we can easily pull it.

```bash
docker pull ghcr.io/huggingface/text-embeddings-inference:cpu-1.2
```

Then run the command `docker images`, you will have the following 7 Docker Images:

1. `opea/gen-ai-comps:embedding-tei-server`
2. `opea/gen-ai-comps:retriever-redis-server`
3. `opea/gen-ai-comps:reranking-tei-server`
4. `opea/gen-ai-comps:llm-tgi-server`
5. `opea/tei-gaudi`
6. `ghcr.io/huggingface/tgi-gaudi:1.2.1`
7. `ghcr.io/huggingface/text-embeddings-inference:cpu-1.2`

## 🚀 Start Microservices

### Setup Environment Variables

Since the `docker_compose.yaml` will consume some environment variables, you need to setup them in advance as below.

```bash
export http_proxy=${your_http_proxy}
export https_proxy=${your_http_proxy}
export EMBEDDING_MODEL_ID="BAAI/bge-base-en-v1.5"
export RERANK_MODEL_ID="BAAI/bge-reranker-large"
export LLM_MODEL_ID="Intel/neural-chat-7b-v3-3"
export TEI_EMBEDDING_ENDPOINT="http://${host_ip}:8090"
export TEI_RERANKING_ENDPOINT="http://${host_ip}:8808"
export TGI_LLM_ENDPOINT="http://${host_ip}:8008"
export REDIS_URL="redis://${host_ip}:6379"
export INDEX_NAME="rag-redis"
export HUGGINGFACEHUB_API_TOKEN=${your_hf_api_token}
```

Note: Please replace with `your_ip` with you external IP address, do not use localhost.

Note: Please replace with `host_ip` with you external IP address, do not use localhost.

### Start Microservice Docker Containers

```bash
docker compose -f docker_compose.yaml up -d
```

### Validate Microservices

1. TEI Embedding Service

```bash
curl ${host_ip}:8090/embed \
    -X POST \
    -d '{"inputs":"What is Deep Learning?"}' \
    -H 'Content-Type: application/json'
```

2. Embedding Microservice

```bash
curl http://${host_ip}:6000/v1/embeddings\
  -X POST \
  -d '{"text":"hello"}' \
  -H 'Content-Type: application/json'
```

3. Retriever Microservice

To consume the retriever microservice, you need to generate a mock embedding vector of length 768 in Python script:

```python
import random

embedding = [random.uniform(-1, 1) for _ in range(768)]
print(embedding)
```

Then substitute your mock embedding vector for the `${your_embedding}` in the following cURL command:

```bash
curl http://${host_ip}:7000/v1/retrieval\
  -X POST \
  -d '{"text":"test", "embedding":${your_embedding}}' \
  -H 'Content-Type: application/json'
```

4. TEI Reranking Service

```bash
curl http://${host_ip}:8808/rerank \
    -X POST \
    -d '{"query":"What is Deep Learning?", "texts": ["Deep Learning is not...", "Deep learning is..."]}' \
    -H 'Content-Type: application/json'
```

5. Reranking Microservice

```bash
curl http://${host_ip}:8000/v1/reranking\
  -X POST \
  -d '{"initial_query":"What is Deep Learning?", "retrieved_docs": [{"text":"Deep Learning is not..."}, {"text":"Deep learning is..."}]}' \
  -H 'Content-Type: application/json'
```

6. TGI Service

```bash
curl http://${host_ip}:8008/generate \
  -X POST \
  -d '{"inputs":"What is Deep Learning?","parameters":{"max_new_tokens":64, "do_sample": true}}' \
  -H 'Content-Type: application/json'
```

7. LLM Microservice

```bash
curl http://${host_ip}:9000/v1/chat/completions\
  -X POST \
  -d '{"text":"What is Deep Learning?"}' \
  -H 'Content-Type: application/json'
```

Following the validation of all aforementioned microservices, we are now prepared to construct a mega-service.

## 🚀 Construct Mega Service

Modify the `initial_inputs` of line 34 in `chatqna.py`, then you will get the ChatQnA result of this mega service.

All of the intermediate results will be printed for each microservice. Users can check the accuracy of the results to make targeted modifications.

```bash
python chatqna.py
```
