# Dataprep Microservice with Redis

# 🚀1. Start Microservice with Python（Option 1）

## 1.1 Install Requirements

```bash
pip install -r requirements.txt
```

## 1.2 Start Redis Stack Server

Please refer to this [readme](../../../vectorstores/langchain/redis/README.md).

## 1.3 Setup Environment Variables

```bash
export REDIS_URL="redis://${your_ip}:6379"
export INDEX_NAME=${your_index_name}
export LANGCHAIN_TRACING_V2=true
export LANGCHAIN_API_KEY=${your_langchain_api_key}
export LANGCHAIN_PROJECT="opea/gen-ai-comps:dataprep"
```

## 1.4 Start Document Preparation Microservice for Redis with Python Script

Start document preparation microservice for Redis with below command.

```bash
python prepare_doc_redis.py
```

# 🚀2. Start Microservice with Docker (Option 2)

## 2.1 Start Redis Stack Server

Please refer to this [readme](../../../vectorstores/langchain/redis/README.md).

## 2.2 Setup Environment Variables

```bash
export REDIS_URL="redis://${your_ip}:6379"
export INDEX_NAME=${your_index_name}
export LANGCHAIN_TRACING_V2=true
export LANGCHAIN_API_KEY=${your_langchain_api_key}
export LANGCHAIN_PROJECT="opea/dataprep"
```

## 2.3 Build Docker Image

```bash
cd ../../../../
docker build -t opea/dataprep-redis:latest --build-arg https_proxy=$https_proxy --build-arg http_proxy=$http_proxy -f comps/dataprep/redis/docker/Dockerfile .
```

## 2.4 Run Docker with CLI (Option A)

```bash
docker run -d --name="dataprep-redis-server" -p 6007:6007 --ipc=host -e http_proxy=$http_proxy -e https_proxy=$https_proxy -e REDIS_URL=$REDIS_URL -e INDEX_NAME=$INDEX_NAME -e TEI_ENDPOINT=$TEI_ENDPOINT opea/dataprep-redis:latest
```

## 2.5 Run with Docker Compose (Option B)

```bash
cd comps/dataprep/redis/docker
docker compose -f docker-compose-dataprep-redis.yaml up -d
```

# 🚀3. Consume Microservice

Once document preparation microservice for Redis is started, user can use below command to invoke the microservice to convert the document to embedding and save to the database.

```bash
curl -X POST \
    -H "Content-Type: application/json" \
    -d '{"path":"/path/to/document"}' \
    http://localhost:6007/v1/dataprep
```
