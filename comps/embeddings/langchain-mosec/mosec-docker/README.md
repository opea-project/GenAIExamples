# Embedding Server

## 1. Introduction

This service has an OpenAI compatible restful API to extract text features.
It is dedicated to be used on Xeon to accelerate embedding model serving.
Currently the local model is BGE-large-zh-v1.5.

## 2. Quick Start

### 2.1 Build Docker image

```shell
docker build -t embedding:latest .
```

### 2.2 Launch server

```shell
docker run -itd -p 8000:8000 embedding:latest
```

### 2.3 Client test

- Restful API by curl

```shell
curl -X POST http://127.0.0.1:8000/v1/embeddings -H "Content-Type: application/json" -d '{ "model": "/root/bge-large-zh-v1.5/", "input": "hello world"}'
```

- generate embedding from python

```python
DEFAULT_MODEL = "/root/bge-large-zh-v1.5/"
SERVICE_URL = "http://127.0.0.1:8000"
INPUT_STR = "Hello world!"

client = Client(api_key="fake", base_url=SERVICE_URL)
emb = client.embeddings.create(
    model=DEFAULT_MODEL,
    input=INPUT_STR,
)
```
