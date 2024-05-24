# Reranking Microservice

The Reranking Microservice, fueled by Rerank models, stands as a straightforward yet immensely potent tool for semantic search. When provided with a query and a collection of documents, Rerank swiftly indexes the documents based on their semantic relevance to the query, arranging them from most to least pertinent. This microservice significantly enhances overall accuracy. In a text retrieval system, either a dense embedding model or a sparse lexical search index is often employed to retrieve relevant text documents based on the input. However, a reranking model can further refine this process by rearranging potential candidates into a final, optimized order.

# 🚀Start Microservice with Python

To start the Reranking microservice, you need to install python packages first.

## Install Requirements

```bash
pip install -r requirements.txt
```

## Start TEI Service Manually

```bash
export HUGGINGFACEHUB_API_TOKEN=${your_hf_api_token}
export LANGCHAIN_TRACING_V2=true
export LANGCHAIN_API_KEY=${your_langchain_api_key}
export LANGCHAIN_PROJECT="opea/gen-ai-comps:reranks"
model=BAAI/bge-reranker-large
revision=refs/pr/4
volume=$PWD/data
docker run -d -p 6060:80 -v $volume:/data -e http_proxy=$http_proxy -e https_proxy=$https_proxy --pull always ghcr.io/huggingface/text-embeddings-inference:cpu-1.2 --model-id $model --revision $revision
```

## Verify the TEI Service

```bash
curl 127.0.0.1:6060/rerank \
    -X POST \
    -d '{"query":"What is Deep Learning?", "texts": ["Deep Learning is not...", "Deep learning is..."]}' \
    -H 'Content-Type: application/json'
```

## Start Reranking Service with Python Script

```bash
export TEI_RERANKING_ENDPOINT="http://${your_ip}:6060"
python reranking_tei_xeon.py
```

# 🚀Start Microservice with Docker

If you start an Reranking microservice with docker, the `docker_compose_reranking.yaml` file will automatically start a TEI service with docker.

## Setup Environment Variables

## Build Docker Image

```bash
cd ../../
docker build -t opea/gen-ai-comps:reranking-tei-xeon-server --build-arg https_proxy=$https_proxy --build-arg http_proxy=$http_proxy -f comps/reranks/langchain/docker/Dockerfile .
```

## Run Docker with CLI

```bash
docker run -d --name="reranking-tei-server" -p 8000:8000 --ipc=host -e http_proxy=$http_proxy -e https_proxy=$https_proxy -e TEI_RERANKING_ENDPOINT=$TEI_RERANKING_ENDPOINT -e HUGGINGFACEHUB_API_TOKEN=$HUGGINGFACEHUB_API_TOKEN opea/gen-ai-comps:reranking-tei-xeon-server
```

## Run Docker with Docker Compose

```bash
cd langchain/docker
docker compose -f docker_compose_reranking.yaml up -d
```

# 🚀Consume Reranking Service

## Check Service Status

```bash
curl http://localhost:8000/v1/health_check\
  -X GET \
  -H 'Content-Type: application/json'
```

## Consume Reranking Service

```bash
curl http://localhost:8000/v1/reranking\
  -X POST \
  -d '{"initial_query":"What is Deep Learning?", "retrieved_docs": [{"text":"Deep Learning is not..."}, {"text":"Deep learning is..."}]}' \
  -H 'Content-Type: application/json'
```
