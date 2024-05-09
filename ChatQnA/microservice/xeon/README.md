# Build Mega Service of ChatQnA on Xeon

This document describes how to deploy a ChatQnA megaservice using Large Language Models (LLM) on an Intel Xeon server. The process involves building Docker images, deploying containers with Docker Compose, and running the service to integrate various microservices like `embedding`, `retriever`, `rerank`, and `llm`.

## 🚀 Build Docker Images

First of all, you need to build Docker Images locally and install the python package of it.

```bash
git clone https://github.com/opea-project/GenAIComps.git
cd GenAIComps
pip install -r requirements.txt
pip install .
```

### 1. Build Embedding Image

```bash
docker build -t intel/gen-ai-comps:embedding-tei-server --build-arg https_proxy=$https_proxy --build-arg http_proxy=$http_proxy -f comps/embeddings/docker/Dockerfile .
```

### 2. Build Retriever Image

```bash
docker build -t intel/gen-ai-comps:retriever-redis-server --build-arg https_proxy=$https_proxy --build-arg http_proxy=$http_proxy -f comps/retrievers/langchain/docker/Dockerfile .
```

### 3. Build Rerank Image

```bash
docker build -t intel/gen-ai-comps:reranking-tei-xeon-server --build-arg https_proxy=$https_proxy --build-arg http_proxy=$http_proxy -f comps/reranks/docker/Dockerfile .
```

### 4. Build LLM Image

```bash
docker build -t intel/gen-ai-comps:llm-tgi-server --build-arg https_proxy=$https_proxy --build-arg http_proxy=$http_proxy -f comps/llm/langchain/docker/Dockerfile .
```

Then run the command `docker images`, you will have the following four Docker Images:

1. `intel/gen-ai-comps:embedding-tei-server`
2. `intel/gen-ai-comps:retriever-redis-server`
3. `intel/gen-ai-comps:reranking-tei-xeon-server`
4. `intel/gen-ai-comps:llm-tgi-server`

## 🚀 Prepare Related Service Endpoints

In order to run the microservices above, you need to prepare the Redis service for Retriever.

```bash
docker run -d --name="redis-vector-db" -p 6379:6379 -p 8001:8001 redis/redis-stack:7.2.0-v9
```

## 🚀 Start Microservices

### Setup Environment Variables

Since the `docker_compose_xeon.yaml` will consume some environment variables, you need to setup them in advance as below.

```bash
export http_proxy=${your_http_proxy}
export https_proxy=${your_http_proxy}
export EMBEDDING_MODEL_ID="BAAI/bge-large-en-v1.5"
export RERANK_MODEL_ID="BAAI/bge-reranker-large"
export LLM_MODEL_ID="m-a-p/OpenCodeInterpreter-DS-6.7B"
export TEI_EMBEDDING_ENDPOINT="http://${your_ip}:8090"
export TEI_RERANKING_ENDPOINT="http://${your_ip}:6060"
export TGI_LLM_ENDPOINT="http://${your_ip}:8008"
export REDIS_URL="redis://${your_ip}:6379"
export INDEX_NAME=${your_index_name}
export HUGGINGFACEHUB_API_TOKEN=${your_hf_api_token}
```

### Start Microservice Docker Containers

```bash
docker compose -f docker_compose_xeon.yaml up -d
```

### Validate Microservices

1. TEI Embedding Service

```bash
curl ${your_ip}:8090/embed \
    -X POST \
    -d '{"inputs":"What is Deep Learning?"}' \
    -H 'Content-Type: application/json'
```

2. Embedding Microservice

```bash
curl http://${your_ip}:6000/v1/embeddings\
  -X POST \
  -d '{"text":"hello"}' \
  -H 'Content-Type: application/json'
```

3. Retriever Microservice

```bash
curl http://${your_ip}:7000/v1/retrieval\
  -X POST \
  -d '{"text":"test","embedding":[1,1,...1]}' \
  -H 'Content-Type: application/json'
```

4. TEI Reranking Service

```bash
curl http://${your_ip}:6060/rerank \
    -X POST \
    -d '{"query":"What is Deep Learning?", "texts": ["Deep Learning is not...", "Deep learning is..."]}' \
    -H 'Content-Type: application/json'
```

5. Reranking Microservice

```bash
curl http://${your_ip}:8000/v1/reranking\
  -X POST \
  -d '{"initial_query":"What is Deep Learning?", "retrieved_docs": [{"text":"Deep Learning is not..."}, {"text":"Deep learning is..."}]}' \
  -H 'Content-Type: application/json'
```

6. TGI Service

```bash
curl http://${your_ip}:8008/generate \
  -X POST \
  -d '{"inputs":"What is Deep Learning?","parameters":{"max_new_tokens":17, "do_sample": true}}' \
  -H 'Content-Type: application/json'
```

7. LLM Microservice

```bash
curl http://${your_ip}:9000/v1/chat/completions\
  -X POST \
  -d '{"text":"What is Deep Learning?"}' \
  -H 'Content-Type: application/json'
```

After validating all of the microservices above, you are able to construct a mega service now.

## 🚀 Construct Mega Service

Modify the `initial_inputs` of line 34 in `mega_service_xeon.py`, then you will get the ChatQnA result of this mega service.

All of the intermediate results will be printed for each microservices. Users can check the accuracy of the results to make targeted modifications.

```bash
python mega_service_xeon.py
```
