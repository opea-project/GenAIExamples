# Deploying CodeGen with openGauss on Intel Xeon Processors

This document outlines the deployment process for a CodeGen application utilizing the [GenAIComps](https://github.com/opea-project/GenAIComps.git) microservice pipeline on Intel Xeon servers. The pipeline integrates **openGauss** as the vector database (VectorDB) and includes microservices such as `embedding`, `retriever`, and `llm`.

---

## Table of Contents

1. [Quick Start](#quick-start)
2. [Build Docker Images](#build-docker-images)
3. [Validate Microservices](#validate-microservices)
4. [Launch the UI](#launch-the-ui)

---

## Quick Start

### 1. Set up Environment Variables

To set up environment variables for deploying CodeGen services, follow these steps:

1. Set the required environment variables:

   ```bash
   # Example: host_ip="192.168.1.1"
   export host_ip="External_Public_IP"
   export HOST_IP=$host_ip
   export HF_TOKEN="Your_Huggingface_API_Token"
   export GS_USER="gaussdb"
   export GS_PASSWORD="openGauss@123"
   export GS_DB="postgres"
   export GS_CONNECTION_STRING="opengauss+psycopg2://${GS_USER}:${GS_PASSWORD}@${host_ip}:5432/${GS_DB}"
   ```

2. If you are in a proxy environment, also set the proxy-related environment variables:

   ```bash
   export http_proxy="Your_HTTP_Proxy"
   export https_proxy="Your_HTTPS_Proxy"
   # Example: no_proxy="localhost,127.0.0.1,192.168.1.1"
   export no_proxy="Your_No_Proxy",codegen-xeon-ui-server,codegen-xeon-backend-server,dataprep-opengauss-server,tei-embedding-serving,retriever-opengauss-server,vllm-server
   ```

3. Set up other environment variables:

   ```bash
   source ../set_env_opengauss.sh
   ```

### 2. Run Docker Compose

```bash
docker compose -f compose_opengauss.yaml up -d
```

It will automatically download the Docker images from Docker Hub:

```bash
docker pull opea/codegen:latest
docker pull opea/codegen-ui:latest
```

Note: You should build docker images from source yourself if:

- You are developing off the git main branch (as the container's ports in the repo may be different from the published docker image).
- You can't download the docker image.
- You want to use a specific version of Docker image.

Please refer to [Build Docker Images](#build-docker-images) below.

### 3. Consume the CodeGen Service

```bash
curl http://${host_ip}:7778/v1/codegen \
    -H "Content-Type: application/json" \
    -d '{
        "messages": "Write a Python function to calculate fibonacci numbers"
    }'
```

---

## Build Docker Images

First of all, you need to build Docker Images locally.

```bash
git clone https://github.com/opea-project/GenAIComps.git
cd GenAIComps
```

### 1. Build Retriever Image

```bash
docker build --no-cache -t opea/retriever:latest --build-arg https_proxy=$https_proxy --build-arg http_proxy=$http_proxy -f comps/retrievers/src/Dockerfile .
```

### 2. Build Dataprep Image

```bash
docker build --no-cache -t opea/dataprep:latest --build-arg https_proxy=$https_proxy --build-arg http_proxy=$http_proxy -f comps/dataprep/src/Dockerfile .
cd ..
```

### 3. Build MegaService Docker Image

```bash
git clone https://github.com/opea-project/GenAIExamples.git
cd GenAIExamples/CodeGen
docker build --no-cache -t opea/codegen:latest --build-arg https_proxy=$https_proxy --build-arg http_proxy=$http_proxy -f Dockerfile .
```

### 4. Build UI Docker Image

```bash
cd GenAIExamples/CodeGen/ui
docker build --no-cache -t opea/codegen-ui:latest --build-arg https_proxy=$https_proxy --build-arg http_proxy=$http_proxy -f docker/Dockerfile .
```

Then run the command `docker images`, you will have the following Docker Images:

1. `opea/dataprep:latest`
2. `opea/retriever:latest`
3. `opea/codegen:latest`
4. `opea/codegen-ui:latest`

---

## Required Models

By default, the embedding and LLM models are set to default values as listed below:

| Service   | Model                          |
| --------- | ------------------------------ |
| Embedding | BAAI/bge-base-en-v1.5          |
| LLM       | Qwen/Qwen2.5-Coder-7B-Instruct |

Change the `xxx_MODEL_ID` in the environment for your needs.

---

## Validate Microservices

Note: When verifying the microservices by curl or API from a remote client, please make sure the **ports** of the microservices are opened in the firewall of the cloud node.

### 1. TEI Embedding Service

```bash
curl ${host_ip}:8090/embed \
    -X POST \
    -d '{"inputs":"What is Deep Learning?"}' \
    -H 'Content-Type: application/json'
```

### 2. Retriever Microservice

To consume the retriever microservice, you need to generate a mock embedding vector by Python script. The length of the embedding vector is determined by the embedding model. Here we use the model `EMBEDDING_MODEL_ID="BAAI/bge-base-en-v1.5"`, which vector size is 768.

```bash
export your_embedding=$(python3 -c "import random; embedding = [random.uniform(-1, 1) for _ in range(768)]; print(embedding)")
curl http://${host_ip}:7000/v1/retrieval \
  -X POST \
  -d "{\"text\":\"test\",\"embedding\":${your_embedding}}" \
  -H 'Content-Type: application/json'
```

### 3. LLM Backend Service

In the first startup, this service will take more time to download, load, and warm up the model. After it's finished, the service will be ready.

Try the command below to check whether the LLM serving is ready:

```bash
docker logs vllm-server 2>&1 | grep complete
```

If the service is ready, you will get the response like below:

```text
INFO: Application startup complete.
```

Then try the `cURL` command below to validate services:

```bash
curl http://${host_ip}:8028/v1/chat/completions \
  -X POST \
  -d '{"model": "Qwen/Qwen2.5-Coder-7B-Instruct", "messages": [{"role": "user", "content": "Write a hello world in Python"}], "max_tokens":50}' \
  -H 'Content-Type: application/json'
```

### 4. MegaService

```bash
curl http://${host_ip}:7778/v1/codegen \
    -H "Content-Type: application/json" \
    -d '{
        "messages": "Write a Python function to sort a list"
    }'
```

### 5. Dataprep Microservice (Optional)

If you want to update the default knowledge base, you can use the following commands:

**Upload a file:**

```bash
curl -X POST "http://${host_ip}:6007/v1/dataprep/ingest" \
     -H "Content-Type: multipart/form-data" \
     -F "files=@./your_code_file.py"
```

**Add Knowledge Base via HTTP Links:**

```bash
curl -X POST "http://${host_ip}:6007/v1/dataprep/ingest" \
     -H "Content-Type: multipart/form-data" \
     -F 'link_list=["https://example.com/code"]'
```

**Delete uploaded files:**

```bash
curl -X POST "http://${host_ip}:6007/v1/dataprep/delete" \
     -d '{"file_path": "all"}' \
     -H "Content-Type: application/json"
```

---

## Launch the UI

To access the frontend, open the following URL in your browser: `http://{host_ip}:5173`

By default, the UI runs on port 5173 internally. If you prefer to use a different host port to access the frontend, you can modify the port mapping in the `compose_opengauss.yaml` file as shown below:

```yaml
codegen-xeon-ui-server:
  image: opea/codegen-ui:latest
  ...
  ports:
    - "80:5173"
```
