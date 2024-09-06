# Prompt Registry Microservice

The Prompt Registry microservice facilitates the storage and retrieval of users'preferred prompts by establishing a connection with the database.

## Setup Environment Variables

```bash
export http_proxy=${your_http_proxy}
export https_proxy=${your_http_proxy}
export MONGO_HOST=${MONGO_HOST}
export MONGO_HOST=27017
export DB_NAME=${DB_NAME}
export COLLECTION_NAME=${COLLECTION_NAME}
```

## Start Prompt Registry microservice for MongoDB with Python script

Start document preparation microservice for Milvus with below command.

```bash
python prompt.py
```

## 🚀Start Microservice with Docker

### Build Docker Image

```bash
cd ~/GenAIComps
docker build -t opea/promptregistry-mongo-server:latest --build-arg https_proxy=$https_proxy --build-arg http_proxy=$http_proxy -f comps/prompt_registry/mongo/docker/Dockerfile .
```

### Run Docker with CLI

1. Run mongoDB image

   ```bash
   docker run -d -p 27017:27017 --name=mongo mongo:latest
   ```

2. Run prompt_registry service

   ```bash
   docker run -d --name="promptregistry-mongo-server" -p 6012:6012 -e http_proxy=$http_proxy -e https_proxy=$https_proxy -e no_proxy=$no_proxy -e MONGO_HOST=${MONGO_HOST} -e MONGO_PORT=${MONGO_PORT} -e DB_NAME=${DB_NAME} -e COLLECTION_NAME=${COLLECTION_NAME} opea/promptregistry-mongo-server:latest
   ```

### Invoke Microservice

Once prompt_registry service is up and running, users can access the database by using API endpoint below. Each API serves different purpose and return appropriate response.

- Save prompt into database.

```bash
curl -X 'POST' \
  http://{host_ip}:6012/v1/prompt/create \
  -H 'accept: application/json' \
  -H 'Content-Type: application/json' \
  -d '{
    "prompt_text": "test prompt", "user": "test"
}'
```

- Retrieve prompt from database based on user or prompt_id

```bash
curl -X 'POST' \
  http://{host_ip}:6012/v1/prompt/get \
  -H 'accept: application/json' \
  -H 'Content-Type: application/json' \
  -d '{
  "user": "test"}'
```

```bash
curl -X 'POST' \
  http://{host_ip}:6012/v1/prompt/get \
  -H 'accept: application/json' \
  -H 'Content-Type: application/json' \
  -d '{
  "user": "test", "prompt_id":"{prompt_id returned from save prompt route above}"}'
```

- Retrieve relevant prompt based on provided keyword

```bash
curl -X 'POST' \
  http://{host_ip}:6012/v1/prompt/get \
  -H 'accept: application/json' \
  -H 'Content-Type: application/json' \
  -d '{
  "user": "test", "prompt_text": "{keyword to search}"}'
```

- Delete prompt from database based on prompt_id provided

```bash
curl -X 'POST' \
  http://{host_ip}:6012/v1/prompt/delete \
  -H 'accept: application/json' \
  -H 'Content-Type: application/json' \
  -d '{
  "user": "test", "prompt_id":"{prompt_id to be deleted}"}'
```
