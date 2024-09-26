# 🗨 Feedback Management Microservice with MongoDB

This README provides setup guides and all the necessary information about the Feedback Management microservice with MongoDB database.

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
docker build -t opea/feedbackmanagement-mongo-server:latest --build-arg https_proxy=$https_proxy --build-arg http_proxy=$http_proxy -f comps/feedback_management/mongo/Dockerfile .
```

### Run Docker with CLI

- Run MongoDB image container

  ```bash
  docker run -d -p 27017:27017 --name=mongo mongo:latest
  ```

- Run Feedback Management microservice

  ```bash
  docker run -d --name="feedbackmanagement-mongo-server" -p 6016:6016 -e http_proxy=$http_proxy -e https_proxy=$https_proxy -e no_proxy=$no_proxy -e MONGO_HOST=${MONGO_HOST} -e MONGO_PORT=${MONGO_PORT} -e DB_NAME=${DB_NAME} -e COLLECTION_NAME=${COLLECTION_NAME} opea/feedbackmanagement-mongo-server:latest
  ```

---

### ✅ Invoke Microservice

The Feedback Management microservice exposes the following API endpoints:

- Save feedback data

  ```bash
  curl -X 'POST' \
    http://${host_ip}:6016/v1/feedback/create \
    -H 'accept: application/json' \
    -H 'Content-Type: application/json' \
    -d '{
    "chat_id": "66445d4f71c7eff23d44f78d",
    "chat_data": {
      "user": "test",
      "messages": [
        {
          "role": "system",
          "content": "You are helpful assistant"
        },
        {
          "role": "user",
          "content": "hi",
          "time": "1724915247"
        },
        {
          "role": "assistant",
          "content": "Hi, may I help you?",
          "time": "1724915249"
        }
      ]
    },
    "feedback_data": {
      "comment": "Moderate",
      "rating": 3,
      "is_thumbs_up": true
    }}'


  # Take note that chat_id here would be the id get from chathistory_mongo service
  # If you do not wish to maintain chat history via chathistory_mongo service, you may generate some random uuid for it or just leave it empty.
  ```

- Update feedback data by feedback_id

  ```bash
  curl -X 'POST' \
    http://${host_ip}:6016/v1/feedback/create \
    -H 'accept: application/json' \
    -H 'Content-Type: application/json' \
    -d '{
    "chat_id": "66445d4f71c7eff23d44f78d",
    "chat_data": {
      "user": "test",
      "messages": [
        {
          "role": "system",
          "content": "You are helpful assistant"
        },
        {
          "role": "user",
          "content": "hi",
          "time": "1724915247"
        },
        {
          "role": "assistant",
          "content": "Hi, may I help you?",
          "time": "1724915249"
        }
      ]
    },
    "feedback_data": {
      "comment": "Fair and Moderate answer",
      "rating": 2,
      "is_thumbs_up": true
    },
    "feedback_id": "{feedback_id of the data that wanted to update}"}'

  # Just include any feedback_data field value that you wanted to update.
  ```

- Retrieve feedback data by user

  ```bash
  curl -X 'POST' \
    http://${host_ip}:6016/v1/feedback/get \
    -H 'accept: application/json' \
    -H 'Content-Type: application/json' \
    -d '{
    "user": "test"}'
  ```

- Retrieve feedback data by feedback_id

  ```bash
  curl -X 'POST' \
    http://${host_ip}:6016/v1/feedback/get \
    -H 'accept: application/json' \
    -H 'Content-Type: application/json' \
    -d '{
    "user": "test", "feedback_id":"{feedback_id returned from save feedback route above}"}'
  ```

- Delete feedback data by feedback_id

  ```bash
  curl -X 'POST' \
    http://${host_ip}:6016/v1/feedback/delete \
    -H 'accept: application/json' \
    -H 'Content-Type: application/json' \
    -d '{
    "user": "test", "feedback_id":"{feedback_id to be deleted}"}'
  ```
