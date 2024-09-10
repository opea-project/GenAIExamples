# Retriever Microservice with Milvus

## 🚀Start Microservice with Python

### Install Requirements

```bash
pip install -r requirements.txt
```

### Start Milvus Server

Please refer to this [readme](../../../vectorstores/milvus/README.md).

### Setup Environment Variables

```bash
export no_proxy=${your_no_proxy}
export http_proxy=${your_http_proxy}
export https_proxy=${your_http_proxy}
export MILVUS=${your_milvus_host_ip}
export MILVUS_PORT=19530
export COLLECTION_NAME=${your_collection_name}
export MOSEC_EMBEDDING_ENDPOINT=${your_emdding_endpoint}
```

### Start Retriever Service

```bash
export MOSEC_EMBEDDING_ENDPOINT="http://${your_ip}:6060"
python retriever_redis.py
```

## 🚀Start Microservice with Docker

### Build Docker Image

```bash
cd ../../
docker build -t opea/retriever-milvus:latest --build-arg https_proxy=$https_proxy --build-arg http_proxy=$http_proxy -f comps/retrievers/milvus/langchain/Dockerfile .
```

### Run Docker with CLI

```bash
docker run -d --name="retriever-milvus-server" -p 7000:7000 --ipc=host -e http_proxy=$http_proxy -e https_proxy=$https_proxy -e MOSEC_EMBEDDING_ENDPOINT=${your_emdding_endpoint} -e MILVUS=${your_milvus_host_ip}  opea/retriever-milvus:latest
```

## 🚀3. Consume Retriever Service

### 3.1 Check Service Status

```bash
curl http://${your_ip}:7000/v1/health_check \
  -X GET \
  -H 'Content-Type: application/json'
```

### 3.2 Consume Embedding Service

To consume the Retriever Microservice, you can generate a mock embedding vector of length 768 with Python.

```bash
your_embedding=$(python -c "import random; embedding = [random.uniform(-1, 1) for _ in range(768)]; print(embedding)")
curl http://${your_ip}:7000/v1/retrieval \
  -X POST \
  -d "{\"text\":\"What is the revenue of Nike in 2023?\",\"embedding\":${your_embedding}}" \
  -H 'Content-Type: application/json'
```

You can set the parameters for the retriever.

```bash
your_embedding=$(python -c "import random; embedding = [random.uniform(-1, 1) for _ in range(768)]; print(embedding)")
curl http://localhost:7000/v1/retrieval \
  -X POST \
  -d "{\"text\":\"What is the revenue of Nike in 2023?\",\"embedding\":${your_embedding},\"search_type\":\"similarity\", \"k\":4}" \
  -H 'Content-Type: application/json'
```

```bash
your_embedding=$(python -c "import random; embedding = [random.uniform(-1, 1) for _ in range(768)]; print(embedding)")
curl http://localhost:7000/v1/retrieval \
  -X POST \
  -d "{\"text\":\"What is the revenue of Nike in 2023?\",\"embedding\":${your_embedding},\"search_type\":\"similarity_distance_threshold\", \"k\":4, \"distance_threshold\":1.0}" \
  -H 'Content-Type: application/json'
```

```bash
your_embedding=$(python -c "import random; embedding = [random.uniform(-1, 1) for _ in range(768)]; print(embedding)")
curl http://localhost:7000/v1/retrieval \
  -X POST \
  -d "{\"text\":\"What is the revenue of Nike in 2023?\",\"embedding\":${your_embedding},\"search_type\":\"similarity_score_threshold\", \"k\":4, \"score_threshold\":0.2}" \
  -H 'Content-Type: application/json'
```

```bash
your_embedding=$(python -c "import random; embedding = [random.uniform(-1, 1) for _ in range(768)]; print(embedding)")
curl http://localhost:7000/v1/retrieval \
  -X POST \
  -d "{\"text\":\"What is the revenue of Nike in 2023?\",\"embedding\":${your_embedding},\"search_type\":\"mmr\", \"k\":4, \"fetch_k\":20, \"lambda_mult\":0.5}" \
  -H 'Content-Type: application/json'
```
