# Multimodal CLIP Embeddings Microservice

The Multimodal CLIP Embedding Microservice is designed to efficiently convert textual strings and images into vectorized embeddings, facilitating seamless integration into various machine learning and data processing workflows. This service utilizes advanced algorithms to generate high-quality embeddings that capture the semantic essence of the input text and images, making it ideal for applications in multi-modal data processing, information retrieval, and similar fields.

Key Features:

**High Performance**: Optimized for quick and reliable conversion of textual data and image inputs into vector embeddings.

**Scalability**: Built to handle high volumes of requests simultaneously, ensuring robust performance even under heavy loads.

**Ease of Integration**: Provides a simple and intuitive API, allowing for straightforward integration into existing systems and workflows.

**Customizable**: Supports configuration and customization to meet specific use case requirements, including different embedding models and preprocessing techniques.

Users are albe to configure and build embedding-related services according to their actual needs.

## 🚀1. Start Microservice with Docker

### 1.1 Build Docker Image

#### Build Langchain Docker

```bash
cd ../../..
docker build -t opea/embedding-multimodal:latest --build-arg https_proxy=$https_proxy --build-arg http_proxy=$http_proxy -f comps/embeddings/multimodal_clip/Dockerfile .
```

### 1.2 Run Docker with Docker Compose

```bash
cd comps/embeddings/multimodal_clip
docker compose -f docker_compose_embedding.yaml up -d
```

## 🚀2. Consume Embedding Service

### 2.1 Check Service Status

```bash
curl http://localhost:6000/v1/health_check\
  -X GET \
  -H 'Content-Type: application/json'
```

### 2.2 Consume Embedding Service

Use our basic API.

```bash
## query with single text
curl http://localhost:6000/v1/embeddings\
  -X POST \
  -d '{"text":"Hello, world!"}' \
  -H 'Content-Type: application/json'

## query with multiple texts
curl http://localhost:6000/v1/embeddings\
  -X POST \
  -d '{"text":["Hello, world!","How are you?"]}' \
  -H 'Content-Type: application/json'
```

We are also compatible with [OpenAI API](https://platform.openai.com/docs/api-reference/embeddings).

```bash
## Input single text
curl http://localhost:6000/v1/embeddings\
  -X POST \
  -d '{"input":"Hello, world!"}' \
  -H 'Content-Type: application/json'

## Input multiple texts with parameters
curl http://localhost:6000/v1/embeddings\
  -X POST \
  -d '{"input":["Hello, world!","How are you?"], "dimensions":100}' \
  -H 'Content-Type: application/json'
```
