# DocRetriever Application with Docker

DocRetriever are the most widely adopted use case for leveraging the different methodologies to match user query against a set of free-text records. DocRetriever is essential to RAG system, which bridges the knowledge gap by dynamically fetching relevant information from external sources, ensuring that responses generated remain factual and current. The core of this architecture are vector databases, which are instrumental in enabling efficient and semantic retrieval of information. These databases store data as vectors, allowing RAG to swiftly access the most pertinent documents or data points based on semantic similarity.

\_Note:

As the related docker images were published to Docker Hub, you can ignore the below step 1 and 2， quick start from step 3.

## 1. Build Images for necessary microservices. (Optional)

- Embedding TEI Image

  ```bash
  git clone https://github.com/opea-project/GenAIComps.git
  cd GenAIComps
  docker build -t opea/embedding:latest --build-arg https_proxy=$https_proxy --build-arg http_proxy=$http_proxy -f comps/embeddings/src/Dockerfile .
  ```

- Retriever Vector store Image

  ```bash
  docker build -t opea/retriever:latest --build-arg https_proxy=$https_proxy --build-arg http_proxy=$http_proxy -f comps/retrievers/src/Dockerfile .
  ```

- Rerank TEI Image

  ```bash
  docker build -t opea/reranking:latest --build-arg https_proxy=$https_proxy --build-arg http_proxy=$http_proxy -f comps/rerankings/src/Dockerfile .
  ```

- Dataprep Image

  ```bash
  docker build -t opea/dataprep:latest --build-arg https_proxy=$https_proxy --build-arg http_proxy=$http_proxy -f comps/dataprep/src/Dockerfile .
  ```

## 2. Build Images for MegaService (Optional)

```bash
cd ..
git clone https://github.com/opea-project/GenAIExamples.git
cd GenAIExamples/DocIndexRetriever
docker build --no-cache -t opea/doc-index-retriever:latest --build-arg https_proxy=$https_proxy --build-arg http_proxy=$http_proxy -f ./Dockerfile .
```

## 3. Start all the services Docker Containers

```bash
export host_ip="YOUR IP ADDR"
export HF_TOKEN=${your_hf_api_token}
```

Set environment variables by

```
cd GenAIExamples/DocIndexRetriever/docker_compose/intel/cpu/xeon
source set_env.sh
```

Note: set_env.sh will help to set all required variables. Please ensure all required variables like ports (LLM_SERVICE_PORT, MEGA_SERVICE_PORT, etc.) are set if not using defaults from the compose file.
or Set environment variables manually

```
export EMBEDDING_MODEL_ID="BAAI/bge-base-en-v1.5"
export RERANK_MODEL_ID="BAAI/bge-reranker-base"
export TEI_EMBEDDING_ENDPOINT="http://${host_ip}:6006"
export TEI_RERANKING_ENDPOINT="http://${host_ip}:8808"
export REDIS_URL="redis://${host_ip}:6379"
export INDEX_NAME="rag-redis"
export EMBEDDING_SERVICE_HOST_IP=${host_ip}
export RETRIEVER_SERVICE_HOST_IP=${host_ip}
export RERANK_SERVICE_HOST_IP=${host_ip}
export BACKEND_SERVICE_ENDPOINT="http://${host_ip}:8000/v1/retrievaltool"
export DATAPREP_SERVICE_ENDPOINT="http://${host_ip}:6007/v1/dataprep/ingest"
cd GenAIExamples/DocIndexRetriever/docker_compose/intel/cpu/xeon
docker compose up -d
```

Two types of DocRetriever pipeline are supported now: `DocRetriever with/without Rerank`. And the `DocRetriever without Rerank` pipeline (including Embedding and Retrieval) is offered for customers who expect to handle all retrieved documents by LLM, and require high performance of DocRetriever.
In that case, start Docker Containers with compose_without_rerank.yaml

```bash
export host_ip="YOUR IP ADDR"
export HF_TOKEN=${your_hf_api_token}
export EMBEDDING_MODEL_ID="BAAI/bge-base-en-v1.5"
cd GenAIExamples/DocIndexRetriever/docker_compose/intel/cpu/xeon
docker compose -f compose_without_rerank.yaml up -d
```

To run the DocRetriever with Rerank pipeline using the Milvus vector database, use the compose_milvus.yaml configuration file and set the MILVUS_HOST environment variable.

```bash
export MILVUS_HOST=${host_ip}
cd GenAIExamples/DocIndexRetriever/docker_compose/intel/cpu/xeon
docker compose -f compose_milvus.yaml up -d
```

## 4. Validation

Add Knowledge Base via HTTP Links:

```bash
curl -X POST "http://${host_ip}:6007/v1/dataprep/ingest" \
     -H "Content-Type: multipart/form-data" \
     -F 'link_list=["https://opea.dev"]'

# expected output
{"status":200,"message":"Data preparation succeeded"}
```

Retrieval from KnowledgeBase

```bash
curl http://${host_ip}:8889/v1/retrievaltool -X POST -H "Content-Type: application/json" -d '{
     "messages": "Explain the OPEA project?"
     }'
```

**Note**: `messages` is the required field. You can also pass in parameters for the retriever and reranker in the request. The parameters that can changed are listed below.

    1. retriever
    * search_type: str = "similarity"
    * k: int = 4
    * distance_threshold: Optional[float] = None
    * fetch_k: int = 20
    * lambda_mult: float = 0.5
    * score_threshold: float = 0.2

    2. reranker
    * top_n: int = 1

## 5. Trouble shooting

1. check all containers are alive

   ```bash
   # redis vector store
   docker container logs redis-vector-db
   # dataprep to redis microservice, input document files
   docker container logs dataprep-redis-server

   # embedding microservice
   curl http://${host_ip}:6000/v1/embeddings \
     -X POST \
     -d '{"messages":"Explain the OPEA project"}' \
     -H 'Content-Type: application/json' > query
   docker container logs embedding-server

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
