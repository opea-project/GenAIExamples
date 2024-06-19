# Reranking Microservice

The Reranking Microservice, fueled by reranking models, stands as a straightforward yet immensely potent tool for semantic search. When provided with a query and a collection of documents, reranking swiftly indexes the documents based on their semantic relevance to the query, arranging them from most to least pertinent. This microservice significantly enhances overall accuracy. In a text retrieval system, either a dense embedding model or a sparse lexical search index is often employed to retrieve relevant text documents based on the input. However, a reranking model can further refine this process by rearranging potential candidates into a final, optimized order.

# 🚀1. Start Microservice with Python (Option 1)

To start the Reranking microservice, you must first install the required python packages.

## 1.1 Install Requirements

```bash
pip install -r requirements.txt
```

## 1.2 Start TEI Service

```bash
export HF_TOKEN=${your_hf_api_token}
export LANGCHAIN_TRACING_V2=true
export LANGCHAIN_API_KEY=${your_langchain_api_key}
export LANGCHAIN_PROJECT="opea/reranks"
export RERANK_MODEL_ID="BAAI/bge-reranker-large"
revision=refs/pr/4
volume=$PWD/data
docker run -d -p 6060:80 -v $volume:/data -e http_proxy=$http_proxy -e https_proxy=$https_proxy --pull always ghcr.io/huggingface/text-embeddings-inference:cpu-1.2 --model-id $RERANK_MODEL_ID --revision $revision --hf-api-token $HF_TOKEN
```

## 1.3 Verify the TEI Service

```bash
curl 127.0.0.1:6060/rerank \
    -X POST \
    -d '{"query":"What is Deep Learning?", "texts": ["Deep Learning is not...", "Deep learning is..."]}' \
    -H 'Content-Type: application/json'
```

## 1.4 Start Reranking Service with Python Script

```bash
export TEI_RERANKING_ENDPOINT="http://${your_ip}:6060"
python reranking_tei_xeon.py
```

# 🚀2. Start Microservice with Docker (Option 2)

If you start an Reranking microservice with docker, the `docker_compose_reranking.yaml` file will automatically start a TEI service with docker.

## 2.1 Setup Environment Variables

```bash
export HF_TOKEN=${your_hf_api_token}
export LANGCHAIN_TRACING_V2=true
export LANGCHAIN_API_KEY=${your_langchain_api_key}
export LANGCHAIN_PROJECT="opea/reranks"
export TEI_RERANKING_ENDPOINT="http://${your_ip}:8808"
```

## 2.2 Build Docker Image

```bash
cd ../../
docker build -t opea/reranking-tei:latest --build-arg https_proxy=$https_proxy --build-arg http_proxy=$http_proxy -f comps/reranks/langchain/docker/Dockerfile .
```

To start a docker container, you have two options:

- A. Run Docker with CLI
- B. Run Docker with Docker Compose

You can choose one as needed.

## 2.3 Run Docker with CLI (Option A)

```bash
docker run -d --name="reranking-tei-server" -p 8000:8000 --ipc=host -e http_proxy=$http_proxy -e https_proxy=$https_proxy -e TEI_RERANKING_ENDPOINT=$TEI_RERANKING_ENDPOINT -e HF_TOKEN=$HF_TOKEN -e LANGCHAIN_API_KEY=$LANGCHAIN_API_KEY opea/reranking-tei:latest
```

## 2.4 Run Docker with Docker Compose (Option B)

```bash
cd langchain/docker
docker compose -f docker_compose_reranking.yaml up -d
```

# 🚀3. Consume Reranking Service

## 3.1 Check Service Status

```bash
curl http://localhost:8000/v1/health_check \
  -X GET \
  -H 'Content-Type: application/json'
```

## 3.2 Consume Reranking Service

```bash
curl http://localhost:8000/v1/reranking \
  -X POST \
  -d '{"initial_query":"What is Deep Learning?", "retrieved_docs": [{"text":"Deep Learning is not..."}, {"text":"Deep learning is..."}]}' \
  -H 'Content-Type: application/json'
```

You can add the parameter `top_n` to specify the return number of the reranker model, default value is 1.

```bash
curl http://localhost:8000/v1/reranking \
  -X POST \
  -d '{"initial_query":"What is Deep Learning?", "retrieved_docs": [{"text":"Deep Learning is not..."}, {"text":"Deep learning is..."}], "top_n":2}' \
  -H 'Content-Type: application/json'
```
