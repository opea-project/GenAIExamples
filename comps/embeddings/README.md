# Embeddings Microservice

The Embedding Microservice is designed to efficiently convert textual strings into vectorized embeddings, facilitating seamless integration into various machine learning and data processing workflows. This service utilizes advanced algorithms to generate high-quality embeddings that capture the semantic essence of the input text, making it ideal for applications in natural language processing, information retrieval, and similar fields.

Key Features:

**High Performance**: Optimized for quick and reliable conversion of textual data into vector embeddings.

**Scalability**: Built to handle high volumes of requests simultaneously, ensuring robust performance even under heavy loads.

**Ease of Integration**: Provides a simple and intuitive API, allowing for straightforward integration into existing systems and workflows.

**Customizable**: Supports configuration and customization to meet specific use case requirements, including different embedding models and preprocessing techniques.

Users are albe to configure and build embedding-related services according to their actual needs.

# 🚀1. Start Microservice with Python (Option 1)

Currently, we provide two ways to implement the embedding service:

1. Build the embedding model **_locally_** from the server, which is faster, but takes up memory on the local server.

2. Build it based on the **_TEI endpoint_**, which provides more flexibility, but may bring some network latency.

For both of the implementations, you need to install requirements first.

## 1.1 Install Requirements

```bash
# run with langchain
pip install -r langchain/requirements.txt
# run with llama_index
pip install -r llama_index/requirements.txt
```

## 1.2 Start Embedding Service

You can select one of following ways to start the embedding service:

### Start Embedding Service with TEI

First, you need to start a TEI service.

```bash
your_port=8090
model="BAAI/bge-large-en-v1.5"
revision="refs/pr/5"
docker run -p $your_port:80 -v ./data:/data --name tei_server -e http_proxy=$http_proxy -e https_proxy=$https_proxy --pull always ghcr.io/huggingface/text-embeddings-inference:cpu-1.5 --model-id $model --revision $revision
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
# run with langchain
cd langchain
# run with llama_index
cd llama_index
export TEI_EMBEDDING_ENDPOINT="http://localhost:$yourport"
export TEI_EMBEDDING_MODEL_NAME="BAAI/bge-large-en-v1.5"
python embedding_tei.py
```

### Start Embedding Service with Local Model

```bash
# run with langchain
cd langchain
# run with llama_index
cd llama_index
python local_embedding.py
```

# 🚀2. Start Microservice with Docker (Optional 2)

## 2.1 Start Embedding Service with TEI

First, you need to start a TEI service.

```bash
your_port=8090
model="BAAI/bge-large-en-v1.5"
revision="refs/pr/5"
docker run -p $your_port:80 -v ./data:/data --name tei_server -e http_proxy=$http_proxy -e https_proxy=$https_proxy --pull always ghcr.io/huggingface/text-embeddings-inference:cpu-1.5 --model-id $model --revision $revision
```

Then you need to test your TEI service using the following commands:

```bash
curl localhost:$your_port/embed \
    -X POST \
    -d '{"inputs":"What is Deep Learning?"}' \
    -H 'Content-Type: application/json'
```

Export the `TEI_EMBEDDING_ENDPOINT` for later usage:

```bash
export TEI_EMBEDDING_ENDPOINT="http://localhost:$yourport"
export TEI_EMBEDDING_MODEL_NAME="BAAI/bge-large-en-v1.5"
```

## 2.2 Build Docker Image

### Build Langchain Docker (Option a)

```bash
cd ../../
docker build -t opea/embedding-tei:latest --build-arg https_proxy=$https_proxy --build-arg http_proxy=$http_proxy -f comps/embeddings/langchain/docker/Dockerfile .
```

### Build LlamaIndex Docker (Option b)

```bash
cd ../../
docker build -t opea/embedding-tei-llama-index:latest --build-arg https_proxy=$https_proxy --build-arg http_proxy=$http_proxy -f comps/embeddings/llama_index/docker/Dockerfile .
```

## 2.3 Run Docker with CLI

```bash
# run with langchain docker
docker run -d --name="embedding-tei-server" -p 6000:6000 --ipc=host -e http_proxy=$http_proxy -e https_proxy=$https_proxy -e TEI_EMBEDDING_ENDPOINT=$TEI_EMBEDDING_ENDPOINT -e TEI_EMBEDDING_MODEL_NAME=$TEI_EMBEDDING_MODEL_NAME opea/embedding-tei:latest
# run with llama-index docker
docker run -d --name="embedding-tei-llama-index-server" -p 6000:6000 --ipc=host -e http_proxy=$http_proxy -e https_proxy=$https_proxy -e TEI_EMBEDDING_ENDPOINT=$TEI_EMBEDDING_ENDPOINT -e TEI_EMBEDDING_MODEL_NAME=$TEI_EMBEDDING_MODEL_NAME opea/embedding-tei-llama-index:latest
```

## 2.4 Run Docker with Docker Compose

```bash
cd docker
docker compose -f docker_compose_embedding.yaml up -d
```

# 🚀3. Consume Embedding Service

## 3.1 Check Service Status

```bash
curl http://localhost:6000/v1/health_check\
  -X GET \
  -H 'Content-Type: application/json'
```

## 3.2 Consume Embedding Service

```bash
curl http://localhost:6000/v1/embeddings\
  -X POST \
  -d '{"text":"Hello, world!"}' \
  -H 'Content-Type: application/json'
```
