# Embeddings Microservice

The Embedding Microservice is designed to efficiently convert textual strings into vectorized embeddings, facilitating seamless integration into various machine learning and data processing workflows. This service utilizes advanced algorithms to generate high-quality embeddings that capture the semantic essence of the input text, making it ideal for applications in natural language processing, information retrieval, and similar fields.

Key Features:

**High Performance**: Optimized for quick and reliable conversion of textual data into vector embeddings.

**Scalability**: Built to handle high volumes of requests simultaneously, ensuring robust performance even under heavy loads.

**Ease of Integration**: Provides a simple and intuitive API, allowing for straightforward integration into existing systems and workflows.

**Customizable**: Supports configuration and customization to meet specific use case requirements, including different embedding models and preprocessing techniques.

Users are albe to configure and build embedding-related services according to their actual needs.

# 🚀Start Microservice with Python

Currently, we provide two ways to implement the embedding service:

1. Build the embedding model **_locally_** from the server, which is faster, but takes up memory on the local server.

2. Build it based on the **_TEI endpoint_**, which provides more flexibility, but may bring some network latency.

For both of the implementations, you need to install requirements first.

## Install Requirements

```bash
pip install -r langchain/requirements.txt
```

## Start Embedding Service with Local Model

```bash
python local_embedding.py
```

## Start Embedding Service with TEI

First, you need to start a TEI service.

```bash
your_port=8090
model="BAAI/bge-large-en-v1.5"
revision="refs/pr/5"
docker run -p $your_port:80 -v ./data:/data --name tei_server -e http_proxy=$http_proxy -e https_proxy=$https_proxy --pull always ghcr.io/huggingface/text-embeddings-inference:cpu-1.2 --model-id $model --revision $revision
```

Then you need to test your TEI service using the following commands:

```bash
curl localhost:$your_port/embed \
    -X POST \
    -d '{"inputs":"What is Deep Learning?"}' \
    -H 'Content-Type: application/json'
```

Start the embedding service with the TEI_EMBEDDING_ENDPOINT.

```bash
cd langchain
export TEI_EMBEDDING_ENDPOINT="http://localhost:$yourport"
python embedding_tei_gaudi.py
```

# 🚀Start Microservice with Docker

## Build Docker Image

```bash
cd ../../
docker build -t opea/gen-ai-comps:embedding-tei-server --build-arg https_proxy=$https_proxy --build-arg http_proxy=$http_proxy -f comps/embeddings/docker/Dockerfile .
```

## Run Docker with CLI

```bash
docker run -d --name="embedding-tei-server" -p 6000:6000 --ipc=host -e http_proxy=$http_proxy -e https_proxy=$https_proxy -e TEI_EMBEDDING_ENDPOINT=$TEI_EMBEDDING_ENDPOINT  opea/gen-ai-comps:embedding-tei-server
```

## Run Docker with Docker Compose

```bash
cd docker
docker compose -f docker_compose.yaml up -d
```

# 🚀Consume Embedding Service

## Check Service Status

```bash
curl http://localhost:6000/v1/health_check\
  -X GET \
  -H 'Content-Type: application/json'
```

## Consume Embedding Service

```bash
curl http://localhost:6000/v1/embeddings\
  -X POST \
  -d '{"text":"Hello, world!"}' \
  -H 'Content-Type: application/json'
```
