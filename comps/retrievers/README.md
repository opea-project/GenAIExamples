# Retriever Microservice

This retriever microservice is a highly efficient search service designed for handling and retrieving embedding vectors. It operates by receiving an embedding vector as input and conducting a similarity search against vectors stored in a vectordb database. Users must specify the vectordb's URL and the index name, and the service searches within that index to find documents with the highest similarity to the input vector.

The service primarily utilizes measures of similarity in vector space to rapidly retrieve documents that are contentually similar. This vector-based retrieval approach is particularly suited for handling large datasets, offering fast and accurate search results that significantly enhance the efficiency and quality of information retrieval.

Overall, this microservice provides robust backend support for applications requiring efficient similarity searches, playing a vital role in scenarios such as recommendation systems, information retrieval, or any other context where precise measurement of document similarity is crucial.

# 🚀Start Microservice with Python

To start the retriever microservice, you need to install python packages first.

## Install Requirements

```bash
pip install -r requirements.txt
```

## Setup Vectordb Service

You need to setup your own vectordb service (Redis in this example), and ingest your knowledge documents into the vector database.

As for Redis, you could start a docker container using the following commands. Remember to ingest data into it manually.

```bash
docker run -d --name="redis-vector-db" -p 6379:6379 -p 8001:8001 redis/redis-stack:7.2.0-v9
```

## Setup Environment Variables

```bash
export REDIS_URL="redis://${your_ip}:6379"
export INDEX_NAME=${your_index_name}
```

## Start Retriever Service with Local Model

```bash
python langchain/retriever_redis.py
```

# 🚀Start Microservice with Docker

## Build Docker Image

```bash
cd ../../
docker build -t opea/gen-ai-comps:retriever-redis-server --build-arg https_proxy=$https_proxy --build-arg http_proxy=$http_proxy -f comps/retrievers/langchain/docker/Dockerfile .
```

## Run Docker with CLI

```bash
docker run -d --name="retriever-redis-server" -p 7000:7000 --ipc=host -e http_proxy=$http_proxy -e https_proxy=$https_proxy -e REDIS_URL=$REDIS_URL -e INDEX_NAME=$INDEX_NAME opea/gen-ai-comps:retriever-redis-server
```

## Run Docker with Docker Compose

```bash
cd langchain/docker
docker compose -f docker_compose_retriever.yaml up -d
```

# 🚀Consume Retriever Service

## Check Service Status

```bash
curl http://localhost:7000/v1/health_check\
  -X GET \
  -H 'Content-Type: application/json'
```

## Consume Embedding Service

```bash
curl http://localhost:7000/v1/retrieval\
  -X POST \
  -d '{"text":"Hello, world!", "embedding": [1,1,...,1]}' \
  -H 'Content-Type: application/json'
```
