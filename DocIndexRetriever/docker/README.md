# DocRetriever Application with Docker

DocRetriever are the most widely adopted use case for leveraging the different methodologies to match user query against a set of free-text records. DocRetriever is essential to RAG system, which bridges the knowledge gap by dynamically fetching relevant information from external sources, ensuring that responses generated remain factual and current. The core of this architecture are vector databases, which are instrumental in enabling efficient and semantic retrieval of information. These databases store data as vectors, allowing RAG to swiftly access the most pertinent documents or data points based on semantic similarity.

## 1. Build Images for necessary microservices. (This step will not needed after docker image released)

- Embedding TEI Image

  ```bash
  git clone https://github.com/opea-project/GenAIComps.git
  cd GenAIComps
  docker build -t opea/embedding-tei:latest --build-arg https_proxy=$https_proxy --build-arg http_proxy=$http_proxy -f comps/embeddings/langchain/docker/Dockerfile .
  ```

- Retriever Vector store Image

  ```bash
  docker build -t opea/retriever-redis:latest --build-arg https_proxy=$https_proxy --build-arg http_proxy=$http_proxy -f comps/retrievers/langchain/redis/docker/Dockerfile .
  ```

- Rerank TEI Image

  ```bash
  docker build -t opea/reranking-tei:latest --build-arg https_proxy=$https_proxy --build-arg http_proxy=$http_proxy -f comps/reranks/tei/docker/Dockerfile .
  ```

- Dataprep Image

  ```bash
  docker build -t opea/dataprep-on-ray-redis:latest --build-arg https_proxy=$https_proxy --build-arg http_proxy=$http_proxy -f comps/dataprep/redis/langchain_ray/docker/Dockerfile .
  ```

## 2. Build Images for MegaService

```bash
cd ..
git clone https://github.com/opea-project/GenAIExamples.git
docker build --no-cache -t opea/doc-index-retriever:latest --build-arg https_proxy=$https_proxy --build-arg http_proxy=$http_proxy -f GenAIExamples/DocIndexRetriever/docker/Dockerfile .
```

## 3. Start all the services Docker Containers

```bash
export host_ip="YOUR IP ADDR"
export HUGGINGFACEHUB_API_TOKEN=${your_hf_api_token}
export EMBEDDING_MODEL_ID="BAAI/bge-base-en-v1.5"
export RERANK_MODEL_ID="BAAI/bge-reranker-base"
export TEI_EMBEDDING_ENDPOINT="http://${host_ip}:8090"
export TEI_RERANKING_ENDPOINT="http://${host_ip}:8808"
export TGI_LLM_ENDPOINT="http://${host_ip}:8008"
export REDIS_URL="redis://${host_ip}:6379"
export INDEX_NAME="rag-redis"
export MEGA_SERVICE_HOST_IP=${host_ip}
export EMBEDDING_SERVICE_HOST_IP=${host_ip}
export RETRIEVER_SERVICE_HOST_IP=${host_ip}
export RERANK_SERVICE_HOST_IP=${host_ip}
export LLM_SERVICE_HOST_IP=${host_ip}
export BACKEND_SERVICE_ENDPOINT="http://${host_ip}:8000/v1/retrievaltool"
export DATAPREP_SERVICE_ENDPOINT="http://${host_ip}:6007/v1/dataprep"
export llm_hardware='xeon' #xeon, xpu, gaudi
cd GenAIExamples/DocIndexRetriever/docker/${llm_hardware}/
docker compose -f docker-compose.yaml up -d
```

## 3. Validation

Add Knowledge Base via HTTP Links:

```bash
curl -X POST "http://${host_ip}:6007/v1/dataprep" \
     -H "Content-Type: multipart/form-data" \
     -F 'link_list=["https://opea.dev"]'

# expected output
{"status":200,"message":"Data preparation succeeded"}
```

Retrieval from KnowledgeBase

```bash
curl http://${host_ip}:8889/v1/retrievaltool -X POST -H "Content-Type: application/json" -d '{
     "text": "Explain the OPEA project?"
     }'

# expected output
{"id":"354e62c703caac8c547b3061433ec5e8","reranked_docs":[{"id":"06d5a5cefc06cf9a9e0b5fa74a9f233c","text":"Close SearchsearchMenu WikiNewsCommunity Daysx-twitter linkedin github searchStreamlining implementation of enterprise-grade Generative AIEfficiently integrate secure, performant, and cost-effective Generative AI workflows into business value.TODAYOPEA..."}],"initial_query":"Explain the OPEA project?"}
```

## 4. Trouble shooting

1. check all containers are alive

   ```bash
   # redis vector store
   docker container logs redis-vector-db
   # dataprep to redis microservice, input document files
   docker container logs dataprep-redis-server

   # embedding microservice
   curl http://${host_ip}:6000/v1/embeddings \
     -X POST \
     -d '{"text":"Explain the OPEA project"}' \
     -H 'Content-Type: application/json' > query
   docker container logs embedding-tei-server

   # if you used tei-gaudi
   docker container logs tei-embedding-gaudi-server

   # retriever microservice, input embedding output docs
   curl http://${host_ip}:7000/v1/retrieval \
     -X POST \
     -d @query \
     -H 'Content-Type: application/json' > rerank_query
   docker container logs retriever-redis-server


   # reranking microservice
   curl http://${host_ip}:8000/v1/reranking \
     -X POST \
     -d @rerank_query \
     -H 'Content-Type: application/json' > output
   docker container logs reranking-tei-server

   # megaservice gateway
   docker container logs doc-index-retriever-server
   ```
