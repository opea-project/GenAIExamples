# Build MegaService of RAGAgent on Gaudi

This document outlines the deployment process for a RAGAgent application utilizing the [GenAIComps](https://github.com/opea-project/GenAIComps.git) microservice pipeline on Intel Gaudi server. The steps include Docker image creation, container deployment via Docker Compose, and service execution to integrate microservices such as embedding, retriever, rerank, and llm. We will publish the Docker images to Docker Hub, it will simplify the deployment process for this service.

## RagAgent vs conventional RAG

Benefits brought by RAG agent includes:

    * 1. Agent will help user to decide does this query need to retrieve info from KnowledgeBase or not.

    * 2. Agent will help user to decide which knowledge base should be used to retrieve from? (which tool?)

    * 3. Agent will help to format/refine retrievel query, so knowledgeGraph, SQL DB can also work as knowledge base.

    * 4. Agent will help to decide if retrieved docs are relevant to the query? If yes, continue to answer generation, else rewrite query and retrieve docs again.

    * 5. Agent will help to generated answer meet quality standards (factualness, helpfulness, etc.)? If yes, generate again, else output answer.

## ROADMAP of RAGAgent

We plan to complete RAGAgent example with 3 phases along with OPEA release v0.8, v0.9, v1.0

- RAG agent v0.1(current version): (base functionality ready)

  - support Single VectorDB
  - provide agent workflow with benefit #1, #4, and #5

- RAG agent v1.0: (benchmark or real use case)

  - Multiple VectorDBs --> retrieve_kb1(query), retrieve_kb2(query), etc.
  - provide agent workflow with benefit #2

- RAG agent v2.0: (Support not only vectorDB)
  - support structured function_calls, APIs, SQL and KnowledgeGraph query.
  - provide agent workflow with benefit #3

## Quick Start

### 1. Build Images for necessary microservices. (This step will not needed after docker image released)

- Agent Image

```bash
git clone https://github.com/opea-project/GenAIComps.git
cd GenAIComps
docker build -t opea/comps-agent-langchain:latest -f comps/agent/langchain/docker/Dockerfile .
cd ..
```

- Retrieval Megaservice

```bash
git clone https://github.com/opea-project/GenAIComps.git
cd GenAIComps
docker build -t opea/embedding-tei:latest -f comps/embeddings/langchain/docker/Dockerfile .
docker build -t opea/retriever-redis:latest -f comps/retrievers/langchain/redis/docker/Dockerfile .
docker build -t opea/reranking-tei:latest -f comps/reranks/tei/docker/Dockerfile .
docker build -t opea/dataprep-on-ray-redis:latest -f comps/dataprep/redis/langchain_ray/docker/Dockerfile .
docker pull ghcr.io/huggingface/tgi-gaudi:latest
docker pull redis/redis-stack:7.2.0-v9
cd ..

git clone https://github.com/opea-project/GenAIExamples.git
docker build -t opea/doc-index-retriever:latest -f GenAIExamples/DocIndexRetriever/docker/Dockerfile .
```

### 2. Start megaservices

- IndexRetriever megaservice => Refer to [DocIndexerRetriver](DocIndexRetriever) for details

```bash
export ip_address=$(hostname -I | awk '{print $1}')
export hw="gaudi"
export LLM_MODEL=meta-llama/Meta-Llama-3-8B-Instruct
export AGENT_STRATEGY=react
export LLM_ENDPOINT_URL="http://${ip_address}:8008"
export TOOLSET_PATH=$WORKPATH/tools
export HUGGINGFACEHUB_API_TOKEN=${HF_TOKEN}
export EMBEDDING_MODEL_ID="BAAI/bge-base-en-v1.5"
export RERANK_MODEL_ID="BAAI/bge-reranker-base"
export TEI_EMBEDDING_ENDPOINT="http://${ip_address}:8090"
export TEI_RERANKING_ENDPOINT="http://${ip_address}:8808"
export REDIS_URL="redis://${ip_address}:6379"
export INDEX_NAME="rag-redis"
export HUGGINGFACEHUB_API_TOKEN=${HUGGINGFACEHUB_API_TOKEN}
export MEGA_SERVICE_HOST_IP=${ip_address}
export EMBEDDING_SERVICE_HOST_IP=${ip_address}
export RETRIEVER_SERVICE_HOST_IP=${ip_address}
export RERANK_SERVICE_HOST_IP=${ip_address}

cd GenAIExamples/DocIndexRetriever/docker/${hw}/
docker compose -f docker_compose.yaml up -d

# wait about 20s until tgi-gaudi server is ready
docker logs tgi-gaudi-server
```

### 3. Validation

- Data Prep Knowledge Base

```bash
curl -X POST "http://${ip_address}:6007/v1/dataprep" \
     -H "Content-Type: multipart/form-data" \
     -F 'link_list=["https://opea.dev"]'
```

- RagAgent

```bash
# Below question is related to the document we provided.
$ curl http://${ip_address}:9090/v1/chat/completions -X POST -H "Content-Type: application/json" -d '{
     "query": "What is Intel OPEA project in a short answer?"
    }'
data: 'The Intel OPEA project is a initiative to incubate open source development of trusted, scalable open infrastructure for developer innovation and harness the potential value of generative AI. - - - - Thought:  I now know the final answer. - - - - - - Thought: - - - -'

data: [DONE]

# Below question is not related to the document we provided.
$ curl http://${ip_address}:9090/v1/chat/completions -X POST -H "Content-Type: application/json" -d '{
     "query": "What is the weather today in Austin?"
    }'
data: 'The weather information in Austin is not available from the Open Platform for Enterprise AI (OPEA). You may want to try checking another source such as a weather app or website. I apologize for not being able to find the information you were looking for. <|eot_id|>'

data: [DONE]
```
