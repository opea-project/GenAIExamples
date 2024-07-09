# Retriever Microservice with Qdrant

# 🚀Start Microservice with Python

## Install Requirements

```bash
pip install -r requirements.txt
```

## Start Qdrant Server

Please refer to this [readme](../../../vectorstores/langchain/qdrant/README.md).

## Setup Environment Variables

```bash
export http_proxy=${your_http_proxy}
export https_proxy=${your_https_proxy}
export QDRANT_HOST=${your_qdrant_host_ip}
export QDRANT_PORT=6333
export EMBED_DIMENSION=${your_embedding_dimension}
export INDEX_NAME=${your_index_name}
export TEI_EMBEDDING_ENDPOINT=${your_tei_endpoint}
```

## Start Retriever Service

```bash
export TEI_EMBEDDING_ENDPOINT="http://${your_ip}:6060"
python haystack/qdrant/retriever_qdrant.py
```

# 🚀Start Microservice with Docker

## Build Docker Image

```bash
cd ../../
docker build -t opea/retriever-qdrant:latest --build-arg https_proxy=$https_proxy --build-arg http_proxy=$http_proxy -f comps/retrievers/haystack/qdrant/docker/Dockerfile .
```

## Run Docker with CLI

```bash
docker run -d --name="retriever-qdrant-server" -p 7000:7000 --ipc=host -e http_proxy=$http_proxy -e https_proxy=$https_proxy -e TEI_EMBEDDING_ENDPOINT=${your_tei_endpoint} -e QDRANT_HOST=${your_qdrant_host_ip} -e QDRANT_PORT=${your_qdrant_port} opea/retriever-qdrant:latest
```

# 🚀3. Consume Retriever Service

## 3.1 Check Service Status

```bash
curl http://${your_ip}:7000/v1/health_check \
  -X GET \
  -H 'Content-Type: application/json'
```

## 3.2 Consume Embedding Service

To consume the Retriever Microservice, you can generate a mock embedding vector of length 768 with Python.

```bash
your_embedding=$(python -c "import random; embedding = [random.uniform(-1, 1) for _ in range(768)]; print(embedding)")
curl http://${your_ip}:7000/v1/retrieval \
  -X POST \
  -d "{\"text\":\"What is the revenue of Nike in 2023?\",\"embedding\":${your_embedding}}" \
  -H 'Content-Type: application/json'
```
