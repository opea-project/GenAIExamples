# Reranking Microservice with fastRAG

`fastRAG` is a research framework for efficient and optimized retrieval augmented generative pipelines, incorporating state-of-the-art LLMs and Information Retrieval.

Please refer to [Official fastRAG repo](https://github.com/IntelLabs/fastRAG/tree/main)
for more information.

This README provides set-up instructions and comprehensive details regarding the reranking microservice via fastRAG.

---

## 🚀1. Start Microservice with Python (Option 1)

To start the Reranking microservice, you must first install the required python packages.

### 1.1 Install Requirements

```bash
pip install -r requirements.txt
```

### 1.2 Install fastRAG

```bash
git clone https://github.com/IntelLabs/fastRAG.git
cd fastRag
pip install .
pip install .[intel]
```

### 1.3 Start Reranking Service with Python Script

```bash
export EMBED_MODEL="Intel/bge-small-en-v1.5-rag-int8-static"
python local_reranking.py
```

---

## 🚀2. Start Microservice with Docker (Option 2)

### 2.1 Setup Environment Variables

```bash
export EMBED_MODEL="Intel/bge-small-en-v1.5-rag-int8-static"
```

### 2.2 Build Docker Image

```bash
cd ../../../
docker build -t opea/reranking-fastrag:latest --build-arg https_proxy=$https_proxy --build-arg http_proxy=$http_proxy -f comps/reranks/fastrag/Dockerfile .
```

### 2.3 Run Docker

```bash
docker run -d --name="reranking-fastrag-server" -p 8000:8000 --ipc=host -e http_proxy=$http_proxy -e https_proxy=$https_proxy -e EMBED_MODEL=$EMBED_MODEL opea/reranking-fastrag:latest
```

---

## ✅ 3. Invoke Reranking Microservice

The Reranking microservice exposes following API endpoints:

- Check Service Status

  ```bash
  curl http://localhost:8000/v1/health_check \
    -X GET \
    -H 'Content-Type: application/json'
  ```

- Execute reranking process by providing query and documents

  ```bash
  curl http://localhost:8000/v1/reranking \
    -X POST \
    -d '{"initial_query":"What is Deep Learning?", "retrieved_docs": [{"text":"Deep Learning is not..."}, {"text":"Deep learning is..."}]}' \
    -H 'Content-Type: application/json'
  ```
