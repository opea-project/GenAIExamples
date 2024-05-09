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

In order to run the microservices above, you need to prepare these service endpoints below:

- TEI service for Embedding
- TEI service for Reranking
- TGI service for LLM
- Redis service for Retriever

### 1. Start TEI service for Embedding

```bash
tei_embed_port=8090
model="BAAI/bge-large-en-v1.5"
revision="refs/pr/5"
docker run -p ${tei_embed_port}:80 --name tei_embedding_server -v ./data:/data -e http_proxy=$http_proxy -e https_proxy=$https_proxy --pull always ghcr.io/huggingface/text-embeddings-inference:cpu-1.2 --model-id ${model} --revision ${revision}
```

Validate with:

```bash
curl localhost:${tei_embed_port}/embed \
    -X POST \
    -d '{"inputs":"What is Deep Learning?"}' \
    -H 'Content-Type: application/json'
```

### 2. Start TEI service for Reranking

```bash
tei_rerank_port=6060
model="BAAI/bge-reranker-large"
revision="refs/pr/4"
docker run -d -p ${tei_rerank_port}:80 --name tei_rerank_server -v ./data:/data -e http_proxy=$http_proxy -e https_proxy=$https_proxy --pull always ghcr.io/huggingface/text-embeddings-inference:cpu-1.2 --model-id ${model} --revision ${revision}
```

Validate with:

```bash
curl localhost:${tei_rerank_port}/rerank \
    -X POST \
    -d '{"query":"What is Deep Learning?", "texts": ["Deep Learning is not...", "Deep learning is..."]}' \
    -H 'Content-Type: application/json'
```

### 3. Start TGI service for LLM

```bash
export HUGGINGFACEHUB_API_TOKEN=${your_hf_api_token}
tgi_port=8008
model="m-a-p/OpenCodeInterpreter-DS-6.7B"
docker run -p ${tgi_port}:80 -v ./data:/data --name tgi_service --shm-size 1g ghcr.io/huggingface/text-generation-inference:1.4 --model-id ${model}
```

Validate with:

```bash
curl http://localhost:${tgi_port}/generate \
  -X POST \
  -d '{"inputs":"What is Deep Learning?","parameters":{"max_new_tokens":17, "do_sample": true}}' \
  -H 'Content-Type: application/json'
```

### 4. Start Redis service for Retriever

```bash
docker run -d --name="redis-vector-db" -p 6379:6379 -p 8001:8001 redis/redis-stack:7.2.0-v9
```

## 🚀 Start Microservices

### Setup Environment Variables

Since the `docker_compose_xeon.yaml` will consume some environment variables, you need to setup them in advance as below.

```bash
export http_proxy=${your_http_proxy}
export https_proxy=${your_http_proxy}
export TEI_EMBEDDING_ENDPOINT="http://${your_ip}:${tei_embed_port}"
export TEI_RERANKING_ENDPOINT="http://${your_ip}:${tei_rerank_port}"
export TGI_LLM_ENDPOINT="http://${your_ip}:${tgi_port}"
export REDIS_URL="redis://${your_ip}:6379"
export INDEX_NAME=${your_index_name}
export HUGGINGFACEHUB_API_TOKEN=${your_hf_api_token}
```

### Start Microservice Docker Containers

```bash
docker compose -f docker_compose_xeon.yaml up -d
```

### Validate Microservices

1. Embedding Microservice

```bash
curl http://${your_ip}:6000/v1/embeddings\
  -X POST \
  -d '{"text":"hello"}' \
  -H 'Content-Type: application/json'
```

2. Retriever Microservice

```bash
curl http://${your_ip}:7000/v1/retrieval\
  -X POST \
  -d '{"text":"test","embedding":[1,1,...1]}' \
  -H 'Content-Type: application/json'
```

3. Reranking Microservice

```bash
curl http://${your_ip}:8000/v1/reranking\
  -X POST \
  -d '{"initial_query":"What is Deep Learning?", "retrieved_docs": [{"text":"Deep Learning is not..."}, {"text":"Deep learning is..."}]}' \
  -H 'Content-Type: application/json'
```

4. LLM Microservice

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
