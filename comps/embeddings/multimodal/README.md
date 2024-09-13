# Multimodal Embeddings Microservice

The Multimodal Embedding Microservice is designed to efficiently convert pairs of textual string and image into vectorized embeddings, facilitating seamless integration into various machine learning and data processing workflows. This service utilizes advanced algorithms to generate high-quality embeddings that capture the joint semantic essence of the input text-and-image pairs, making it ideal for applications in multi-modal data processing, information retrieval, and similar fields.

Key Features:

**High Performance**: Optimized for quick and reliable conversion of textual data and image inputs into vector embeddings.

**Scalability**: Built to handle high volumes of requests simultaneously, ensuring robust performance even under heavy loads.

**Ease of Integration**: Provides a simple and intuitive API, allowing for straightforward integration into existing systems and workflows.

**Customizable**: Supports configuration and customization to meet specific use case requirements, including different embedding models and preprocessing techniques.

Users are albe to configure and build embedding-related services according to their actual needs.

## 🚀1. Start Microservice with Python (Option 1)

Currently, we provide two ways to implement the multimodal embedding service:

1. Build the multimodal embedding model **locally** from the server, which is faster, but takes up memory on the local server.
2. Build it based on the multimodal embedding inference endpoint (**MMEI endpoint**), which provides more flexibility, but may bring some network latency.

For both of the implementations, you need to install requirements first.

### 1.1 Install Requirements

```bash
# run with langchain
pip install -r multimodal_langchain/requirements.txt
```

### 1.2 Start Embedding Service

You can select one of the following to start the multimodal embedding service:

**Start Multimodal Embedding Service with MMEI**

First, you need to start a MMEI service.

```bash
export your_mmei_port=8080
export EMBEDDER_PORT=$your_mmei_port
```

Currently, we employ [**BridgeTower**](https://huggingface.co/BridgeTower/bridgetower-large-itm-mlm-gaudi) model for MMEI and provide two ways to start MMEI:

1. Start MMEI on Gaudi2 HPU
2. Start MMEI on Xeon CPU (if Gaudi2 HPU is not available)

- Gaudi2 HPU

```bash
cd ../../..
docker build -t opea/embedding-multimodal-bridgetower:latest --build-arg EMBEDDER_PORT=$EMBEDDER_PORT --build-arg https_proxy=$https_proxy --build-arg http_proxy=$http_proxy -f comps/embeddings/multimodal/bridgetower/Dockerfile.intel_hpu .
cd comps/embeddings/multimodal/bridgetower/
docker compose -f docker_compose_bridgetower_embedding_endpoint.yaml up -d
```

- Xeon CPU

```bash
cd ../../..
docker build -t opea/embedding-multimodal-bridgetower:latest --build-arg EMBEDDER_PORT=$EMBEDDER_PORT --build-arg https_proxy=$https_proxy --build-arg http_proxy=$http_proxy -f comps/embeddings/multimodal/bridgetower/Dockerfile .
cd comps/embeddings/multimodal/bridgetower/
docker compose -f docker_compose_bridgetower_embedding_endpoint.yaml up -d
```

Then you need to test your MMEI service using the following commands:

```bash
curl http://localhost:$your_mmei_port/v1/encode \
     -X POST \
     -H "Content-Type:application/json" \
     -d '{"text":"This is example"}'
```

Start the embedding service with MMEI_EMBEDDING_ENDPOINT.

```bash
# run with langchain
cd multimodal_langchain
export MMEI_EMBEDDING_ENDPOINT="http://localhost:$your_mmei_port/v1/encode"
export your_embedding_port_microservice=6600
export MM_EMBEDDING_PORT_MICROSERVICE=$your_embedding_port_microservice
python mm_embedding_mmei.py
```

**Start Embedding Service with Local Model**

```bash
# run with langchain
cd multimodal_langchain
export your_embedding_port_microservice=6600
export MM_EMBEDDING_PORT_MICROSERVICE=$your_embedding_port_microservice
python local_mm_embedding.py
```

## 🚀2. Start Microservice with Docker (Option 2)

### 2.1 Start Multimodal Embedding Inference (MMEI) Service

First, you need to start a MMEI service.

```bash
export your_mmei_port=8080
export EMBEDDER_PORT=$your_mmei_port
```

Currently, we employ [**BridgeTower**](https://huggingface.co/BridgeTower/bridgetower-large-itm-mlm-gaudi) model for MMEI and provide two ways to start MMEI:

1. Start MMEI on Gaudi2 HPU
2. Start MMEI on Xeon CPU (if Gaudi2 HPU is not available)

- Gaudi2 HPU

```bash
cd ../../..
docker build -t opea/embedding-multimodal-bridgetower:latest --build-arg EMBEDDER_PORT=$EMBEDDER_PORT --build-arg https_proxy=$https_proxy --build-arg http_proxy=$http_proxy -f comps/embeddings/multimodal/bridgetower/Dockerfile.intel_hpu .
cd comps/embeddings/multimodal/bridgetower/
docker compose -f docker_compose_bridgetower_embedding_endpoint.yaml up -d
```

- Xeon CPU

```bash
cd ../../..
docker build -t opea/embedding-multimodal-bridgetower:latest --build-arg EMBEDDER_PORT=$EMBEDDER_PORT --build-arg https_proxy=$https_proxy --build-arg http_proxy=$http_proxy -f comps/embeddings/multimodal/bridgetower/Dockerfile .
cd comps/embeddings/multimodal/bridgetower/
docker compose -f docker_compose_bridgetower_embedding_endpoint.yaml up -d
```

Then you need to test your MMEI service using the following commands:

```bash
curl http://localhost:$your_mmei_port/v1/encode \
     -X POST \
     -H "Content-Type:application/json" \
     -d '{"text":"This is example"}'
```

Export the `MMEI_EMBEDDING_ENDPOINT` for later usage:

```bash
export ip_address=$(hostname -I | awk '{print $1}')
export MMEI_EMBEDDING_ENDPOINT="http://$ip_address:$your_mmei_port/v1/encode"
```

### 2.2 Build Docker Image

#### Build Langchain Docker

```bash
cd ../../..
docker build -t opea/embedding-multimodal:latest --build-arg https_proxy=$https_proxy --build-arg http_proxy=$http_proxy -f comps/embeddings/multimodal/multimodal_langchain/Dockerfile .
```

### 2.3 Run Docker with Docker Compose

```bash
cd multimodal_langchain
export your_embedding_port_microservice=6600
export MM_EMBEDDING_PORT_MICROSERVICE=$your_embedding_port_microservice
docker compose -f docker_compose_multimodal_embedding.yaml up -d
```

## 🚀3. Consume Embedding Service

### 2.2 Consume Embedding Service

**Compute a joint embedding of an image-text pair**

```bash
curl -X POST http://0.0.0.0:6600/v1/embeddings \
     -H "Content-Type: application/json" \
     -d '{"text": {"text" : "This is some sample text."}, "image" : {"url": "https://github.com/docarray/docarray/blob/main/tests/toydata/image-data/apple.png?raw=true"}}'
```

**Compute an embedding of a text**

```bash
curl -X POST http://0.0.0.0:6600/v1/embeddings \
     -H "Content-Type: application/json" \
     -d '{"text" : "This is some sample text."}'
```
