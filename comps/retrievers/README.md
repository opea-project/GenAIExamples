# Retriever Microservice

This retriever microservice is a highly efficient search service designed for handling and retrieving embedding vectors. It operates by receiving an embedding vector as input and conducting a similarity search against vectors stored in a VectorDB database. Users must specify the VectorDB's URL and the index name, and the service searches within that index to find documents with the highest similarity to the input vector.

The service primarily utilizes similarity measures in vector space to rapidly retrieve contentually similar documents. The vector-based retrieval approach is particularly suited for handling large datasets, offering fast and accurate search results that significantly enhance the efficiency and quality of information retrieval.

Overall, this microservice provides robust backend support for applications requiring efficient similarity searches, playing a vital role in scenarios such as recommendation systems, information retrieval, or any other context where precise measurement of document similarity is crucial.

# 🚀1. Start Microservice with Python (Option 1)

To start the retriever microservice, you must first install the required python packages.

## 1.1 Install Requirements

```bash
pip install -r requirements.txt
```

## 1.2 Start TEI Service

```bash
export LANGCHAIN_TRACING_V2=true
export LANGCHAIN_API_KEY=${your_langchain_api_key}
export LANGCHAIN_PROJECT="opea/retriever"
model=BAAI/bge-base-en-v1.5
revision=refs/pr/4
volume=$PWD/data
docker run -d -p 6060:80 -v $volume:/data -e http_proxy=$http_proxy -e https_proxy=$https_proxy --pull always ghcr.io/huggingface/text-embeddings-inference:cpu-1.2 --model-id $model --revision $revision
```

## 1.3 Verify the TEI Service

```bash
curl 127.0.0.1:6060/rerank \
    -X POST \
    -d '{"query":"What is Deep Learning?", "texts": ["Deep Learning is not...", "Deep learning is..."]}' \
    -H 'Content-Type: application/json'
```

## 1.4 Setup VectorDB Service

You need to setup your own VectorDB service (Redis in this example), and ingest your knowledge documents into the vector database.

As for Redis, you could start a docker container using the following commands.
Remember to ingest data into it manually.

```bash
docker run -d --name="redis-vector-db" -p 6379:6379 -p 8001:8001 redis/redis-stack:7.2.0-v9
```

## 1.5 Start Retriever Service

```bash
export TEI_EMBEDDING_ENDPOINT="http://${your_ip}:6060"
python langchain/retriever_redis.py
```

# 🚀2. Start Microservice with Docker (Option 2)

## 2.1 Setup Environment Variables

```bash
export RETRIEVE_MODEL_ID="BAAI/bge-base-en-v1.5"
export REDIS_URL="redis://${your_ip}:6379"
export INDEX_NAME=${your_index_name}
export TEI_EMBEDDING_ENDPOINT="http://${your_ip}:6060"
export LANGCHAIN_TRACING_V2=true
export LANGCHAIN_API_KEY=${your_langchain_api_key}
export LANGCHAIN_PROJECT="opea/retrievers"
```

## 2.2 Build Docker Image

```bash
cd ../../
docker build -t opea/retriever-redis:latest --build-arg https_proxy=$https_proxy --build-arg http_proxy=$http_proxy -f comps/retrievers/langchain/docker/Dockerfile .
```

To start a docker container, you have two options:

- A. Run Docker with CLI
- B. Run Docker with Docker Compose

You can choose one as needed.

## 2.3 Run Docker with CLI (Option A)

```bash
docker run -d --name="retriever-redis-server" -p 7000:7000 --ipc=host -e http_proxy=$http_proxy -e https_proxy=$https_proxy -e REDIS_URL=$REDIS_URL -e INDEX_NAME=$INDEX_NAME -e TEI_EMBEDDING_ENDPOINT=$TEI_EMBEDDING_ENDPOINT opea/retriever-redis:latest
```

## 2.4 Run Docker with Docker Compose (Option B)

```bash
cd langchain/docker
docker compose -f docker_compose_retriever.yaml up -d
```

# 🚀3. Consume Retriever Service

## 3.1 Check Service Status

```bash
curl http://localhost:7000/v1/health_check \
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
