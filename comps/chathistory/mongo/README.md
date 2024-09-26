# 📝 Chat History Microservice with MongoDB

This README provides setup guides and all the necessary information about the Chat History microservice with MongoDB database.

---

## Setup Environment Variables

```bash
export http_proxy=${your_http_proxy}
export https_proxy=${your_http_proxy}
export MONGO_HOST=${MONGO_HOST}
export MONGO_PORT=27017
export DB_NAME=${DB_NAME}
export COLLECTION_NAME=${COLLECTION_NAME}
```

---

## 🚀Start Microservice with Docker

### Build Docker Image

```bash
cd ../../../../
docker build -t opea/chathistory-mongo-server:latest --build-arg https_proxy=$https_proxy --build-arg http_proxy=$http_proxy -f comps/chathistory/mongo/Dockerfile .
```

### Run Docker with CLI

- Run MongoDB image container

  ```bash
  docker run -d -p 27017:27017 --name=mongo mongo:latest
  ```

- Run the Chat History microservice

  ```bash
  docker run -d --name="chathistory-mongo-server" -p 6012:6012 -e http_proxy=$http_proxy -e https_proxy=$https_proxy -e no_proxy=$no_proxy -e MONGO_HOST=${MONGO_HOST} -e MONGO_PORT=${MONGO_PORT} -e DB_NAME=${DB_NAME} -e COLLECTION_NAME=$ {COLLECTION_NAME} opea/chathistory-mongo-server:latest
  ```

---

## ✅ Invoke Microservice

The Chat History microservice exposes the following API endpoints:

- Create new chat conversation

  ```bash
  curl -X 'POST' \
    http://${host_ip}:6012/v1/chathistory/create \
    -H 'accept: application/json' \
    -H 'Content-Type: application/json' \
    -d '{
    "data": {
      "messages": "test Messages", "user": "test"
    }
  }'
  ```

- Get all the Conversations for a user

  ```bash
  curl -X 'POST' \
    http://${host_ip}:6012/v1/chathistory/get \
    -H 'accept: application/json' \
    -H 'Content-Type: application/json' \
    -d '{
    "user": "test"}'
  ```

- Get a specific conversation by id.

  ```bash
  curl -X 'POST' \
    http://${host_ip}:6012/v1/chathistory/get \
    -H 'accept: application/json' \
    -H 'Content-Type: application/json' \
    -d '{
    "user": "test", "id":"668620173180b591e1e0cd74"}'
  ```

- Update the conversation by id.

  ```bash
  curl -X 'POST' \
    http://${host_ip}:6012/v1/chathistory/create \
    -H 'accept: application/json' \
    -H 'Content-Type: application/json' \
    -d '{
    "data": {
      "messages": "test Messages Update", "user": "test"
    },
    "id":"668620173180b591e1e0cd74"
  }'
  ```

- Delete a stored conversation.

  ```bash
  curl -X 'POST' \
    http://${host_ip}:6012/v1/chathistory/delete \
    -H 'accept: application/json' \
    -H 'Content-Type: application/json' \
    -d '{
    "user": "test", "id":"668620173180b591e1e0cd74"}'
  ```
