# Build Mega Service of ChatQnA on Xeon

This document outlines the deployment process for a ChatQnA application utilizing the [GenAIComps](https://github.com/opea-project/GenAIComps.git) microservice pipeline on Intel Xeon server. The steps include Docker image creation, container deployment via Docker Compose, and service execution to integrate microservices such as `embedding`, `retriever`, `rerank`, and `llm`. We will publish the Docker images to Docker Hub soon, it will simplify the deployment process for this service.

## 🚀 Apply Xeon Server on AWS

To apply a Xeon server on AWS, start by creating an AWS account if you don't have one already. Then, head to the [EC2 Console](https://console.aws.amazon.com/ec2/v2/home) to begin the process. Within the EC2 service, select the Amazon EC2 M7i or M7i-flex instance type to leverage the power of 4th Generation Intel Xeon Scalable processors. These instances are optimized for high-performance computing and demanding workloads.

For detailed information about these instance types, you can refer to this [link](https://aws.amazon.com/ec2/instance-types/m7i/). Once you've chosen the appropriate instance type, proceed with configuring your instance settings, including network configurations, security groups, and storage options.

After launching your instance, you can connect to it using SSH (for Linux instances) or Remote Desktop Protocol (RDP) (for Windows instances). From there, you'll have full access to your Xeon server, allowing you to install, configure, and manage your applications as needed.

## 🚀 Build Docker Images

First of all, you need to build Docker Images locally and install the python package of it.

```bash
git clone https://github.com/opea-project/GenAIComps.git
cd GenAIComps
```

### 1. Build Embedding Image

```bash
docker build -t opea/gen-ai-comps:embedding-tei-server --build-arg https_proxy=$https_proxy --build-arg http_proxy=$http_proxy -f comps/embeddings/langchain/docker/Dockerfile .
```

### 2. Build Retriever Image

```bash
docker build -t opea/gen-ai-comps:retriever-redis-server --build-arg https_proxy=$https_proxy --build-arg http_proxy=$http_proxy -f comps/retrievers/langchain/docker/Dockerfile .
```

### 3. Build Rerank Image

```bash
docker build -t opea/gen-ai-comps:reranking-tei-xeon-server --build-arg https_proxy=$https_proxy --build-arg http_proxy=$http_proxy -f comps/reranks/langchain/docker/Dockerfile .
```

### 4. Build LLM Image

```bash
docker build -t opea/gen-ai-comps:llm-tgi-server --build-arg https_proxy=$https_proxy --build-arg http_proxy=$http_proxy -f comps/llms/langchain/docker/Dockerfile .
```

### 5. Build MegaService Docker Image

To construct the Mega Service, we utilize the [GenAIComps](https://github.com/opea-project/GenAIComps.git) microservice pipeline within the `chatqna.py` Python script. Build MegaService Docker image via below command:

```bash
git clone https://github.com/opea-project/GenAIExamples
cd GenAIExamples/ChatQnA/microservice/xeon/
docker build -t opea/gen-ai-comps:chatqna-megaservice-server --build-arg https_proxy=$https_proxy --build-arg http_proxy=$http_proxy -f docker/Dockerfile .
```

### 6. Build UI Docker Image

Build frontend Docker image via below command:

```bash
cd GenAIExamples/ChatQnA/ui/
docker build -t opea/gen-ai-comps:chatqna-ui-server --build-arg https_proxy=$https_proxy --build-arg http_proxy=$http_proxy -f ./docker/Dockerfile .
```

Then run the command `docker images`, you will have the following four Docker Images:

1. `opea/gen-ai-comps:embedding-tei-server`
2. `opea/gen-ai-comps:retriever-redis-server`
3. `opea/gen-ai-comps:reranking-tei-xeon-server`
4. `opea/gen-ai-comps:llm-tgi-server`
5. `opea/gen-ai-comps:chatqna-megaservice-server`
6. `opea/gen-ai-comps:chatqna-ui-server`

## 🚀 Start Microservices

### Setup Environment Variables

Since the `docker_compose.yaml` will consume some environment variables, you need to setup them in advance as below.

```bash
export http_proxy=${your_http_proxy}
export https_proxy=${your_http_proxy}
export EMBEDDING_MODEL_ID="BAAI/bge-base-en-v1.5"
export RERANK_MODEL_ID="BAAI/bge-reranker-large"
export LLM_MODEL_ID="Intel/neural-chat-7b-v3-3"
export TEI_EMBEDDING_ENDPOINT="http://${host_ip}:6006"
export TEI_RERANKING_ENDPOINT="http://${host_ip}:8808"
export TGI_LLM_ENDPOINT="http://${host_ip}:9009"
export REDIS_URL="redis://${host_ip}:6379"
export INDEX_NAME="rag-redis"
export HUGGINGFACEHUB_API_TOKEN=${your_hf_api_token}
export MEGA_SERVICE_HOST_IP=${host_ip}
export BACKEND_SERVICE_ENDPOINT="http://${host_ip}:8888/v1/chatqna"
```

Note: Please replace with `host_ip` with you external IP address, do not use localhost.

### Start all the services Docker Containers

```bash
docker compose -f docker_compose.yaml up -d
```

### Validate Microservices

1. TEI Embedding Service

```bash
curl ${host_ip}:6006/embed \
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
   To validate the retriever microservice, you need to generate a mock embedding vector of length 768 in Python script:

```Python
import random
embedding = [random.uniform(-1, 1) for _ in range(768)]
print(embedding)
```

Then substitute your mock embedding vector for the `${your_embedding}` in the following cURL command:

```bash
curl http://${host_ip}:7000/v1/retrieval\
  -X POST \
  -d '{"text":"What is the revenue of Nike in 2023?","embedding":${your_embedding}}' \
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
curl http://${host_ip}:9009/generate \
  -X POST \
  -d '{"inputs":"What is Deep Learning?","parameters":{"max_new_tokens":17, "do_sample": true}}' \
  -H 'Content-Type: application/json'
```

7. LLM Microservice

```bash
curl http://${host_ip}:9000/v1/chat/completions\
  -X POST \
  -d '{"query":"What is Deep Learning?","max_new_tokens":17,"top_k":10,"top_p":0.95,"typical_p":0.95,"temperature":0.01,"repetition_penalty":1.03,"streaming":true}' \
  -H 'Content-Type: application/json'
```

8. MegaService

```bash
curl http://${host_ip}:8888/v1/chatqna -H "Content-Type: application/json" -d '{
     "model": "Intel/neural-chat-7b-v3-3",
     "messages": "What is the revenue of Nike in 2023?"
     }'
```

## 🚀 Launch the UI

Open this URL `http://{host_ip}:5173` in your browser to access the frontend.

![project-screenshot](https://i.imgur.com/26zMnEr.png)
