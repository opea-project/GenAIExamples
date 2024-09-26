# 🧾 Prompt Registry Microservice with MongoDB

This README provides setup guides and all the necessary information about the Prompt Registry microservice with MongoDB database.

---

## Setup Environment Variables

```bash
export http_proxy=${your_http_proxy}
export https_proxy=${your_http_proxy}
export MONGO_HOST=${MONGO_HOST}
export MONGO_HOST=27017
export DB_NAME=${DB_NAME}
export COLLECTION_NAME=${COLLECTION_NAME}
```

---

## 🚀Start Microservice with Docker

### Build Docker Image

```bash
cd ~/GenAIComps
docker build -t opea/promptregistry-mongo-server:latest --build-arg https_proxy=$https_proxy --build-arg http_proxy=$http_proxy -f comps/prompt_registry/mongo/Dockerfile .
```

### Run Docker with CLI

- Run MongoDB image container

  ```bash
  docker run -d -p 27017:27017 --name=mongo mongo:latest
  ```

- Run Prompt Registry microservice

  ```bash
  docker run -d --name="promptregistry-mongo-server" -p 6018:6018 -e http_proxy=$http_proxy -e https_proxy=$https_proxy -e no_proxy=$no_proxy -e MONGO_HOST=${MONGO_HOST} -e MONGO_PORT=${MONGO_PORT} -e DB_NAME=${DB_NAME} -e COLLECTION_NAME=${COLLECTION_NAME} opea/promptregistry-mongo-server:latest
  ```

---

### ✅ Invoke Microservice

The Prompt Registry microservice exposes the following API endpoints:

- Save prompt

  ```bash
  curl -X 'POST' \
    http://${host_ip}:6018/v1/prompt/create \
    -H 'accept: application/json' \
    -H 'Content-Type: application/json' \
    -d '{
      "prompt_text": "test prompt", "user": "test"
  }'
  ```

- Retrieve prompt from database by user

  ```bash
  curl -X 'POST' \
    http://${host_ip}:6018/v1/prompt/get \
    -H 'accept: application/json' \
    -H 'Content-Type: application/json' \
    -d '{
    "user": "test"}'
  ```

- Retrieve prompt from database by prompt_id

  ```bash
  curl -X 'POST' \
    http://${host_ip}:6018/v1/prompt/get \
    -H 'accept: application/json' \
    -H 'Content-Type: application/json' \
    -d '{
    "user": "test", "prompt_id":"{prompt_id returned from save prompt route above}"}'
  ```

- Retrieve relevant prompt by keyword

  ```bash
  curl -X 'POST' \
    http://${host_ip}:6018/v1/prompt/get \
    -H 'accept: application/json' \
    -H 'Content-Type: application/json' \
    -d '{
    "user": "test", "prompt_text": "{keyword to search}"}'
  ```

- Delete prompt by prompt_id

  ```bash
  curl -X 'POST' \
    http://${host_ip}:6018/v1/prompt/delete \
    -H 'accept: application/json' \
    -H 'Content-Type: application/json' \
    -d '{
    "user": "test", "prompt_id":"{prompt_id to be deleted}"}'
  ```
