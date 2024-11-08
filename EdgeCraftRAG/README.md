# Edge Craft Retrieval-Augmented Generation

Edge Craft RAG (EC-RAG) is a customizable, tunable and production-ready
Retrieval-Augmented Generation system for edge solutions. It is designed to
curate the RAG pipeline to meet hardware requirements at edge with guaranteed
quality and performance.

## Quick Start Guide

### Run Containers with Docker Compose

```bash
cd GenAIExamples/EdgeCraftRAG/docker_compose/intel/gpu/arc

export MODEL_PATH="your model path for all your models"
export DOC_PATH="your doc path for uploading a dir of files"
export HOST_IP="your host ip"
export UI_SERVICE_PORT="port for UI service"

# Optional for vllm endpoint
export vLLM_ENDPOINT="http://${HOST_IP}:8008"

# If you have a proxy configured, uncomment below line
# export no_proxy=$no_proxy,${HOST_IP},edgecraftrag,edgecraftrag-server
# If you have a HF mirror configured, it will be imported to the container
# export HF_ENDPOINT="your HF mirror endpoint"

# By default, the ports of the containers are set, uncomment if you want to change
# export MEGA_SERVICE_PORT=16011
# export PIPELINE_SERVICE_PORT=16011

docker compose up -d
```

### (Optional) Build Docker Images for Mega Service, Server and UI by your own

```bash
cd GenAIExamples/EdgeCraftRAG

docker build --build-arg http_proxy=$HTTP_PROXY --build-arg https_proxy=$HTTPS_PROXY --build-arg no_proxy=$NO_PROXY -t opea/edgecraftrag:latest -f Dockerfile .
docker build --build-arg http_proxy=$HTTP_PROXY --build-arg https_proxy=$HTTPS_PROXY --build-arg no_proxy=$NO_PROXY -t opea/edgecraftrag-server:latest -f Dockerfile.server .
docker build --build-arg http_proxy=$HTTP_PROXY --build-arg https_proxy=$HTTPS_PROXY --build-arg no_proxy=$NO_PROXY -t opea/edgecraftrag-ui:latest -f ui/docker/Dockerfile.ui .
```

### ChatQnA with LLM Example (Command Line)

```bash
cd GenAIExamples/EdgeCraftRAG

# Activate pipeline test_pipeline_local_llm
curl -X POST http://${HOST_IP}:16010/v1/settings/pipelines -H "Content-Type: application/json" -d @tests/test_pipeline_local_llm.json | jq '.'

# Will need to wait for several minutes
# Expected output:
# {
#   "idx": "3214cf25-8dff-46e6-b7d1-1811f237cf8c",
#   "name": "rag_test",
#   "comp_type": "pipeline",
#   "node_parser": {
#     "idx": "ababed12-c192-4cbb-b27e-e49c76a751ca",
#     "parser_type": "simple",
#     "chunk_size": 400,
#     "chunk_overlap": 48
#   },
#   "indexer": {
#     "idx": "46969b63-8a32-4142-874d-d5c86ee9e228",
#     "indexer_type": "faiss_vector",
#     "model": {
#       "idx": "7aae57c0-13a4-4a15-aecb-46c2ec8fe738",
#       "type": "embedding",
#       "model_id": "BAAI/bge-small-en-v1.5",
#       "model_path": "/home/user/models/bge_ov_embedding",
#       "device": "auto"
#     }
#   },
#   "retriever": {
#     "idx": "3747fa59-ff9b-49b6-a8e8-03cdf8c979a4",
#     "retriever_type": "vectorsimilarity",
#     "retrieve_topk": 30
#   },
#   "postprocessor": [
#     {
#       "idx": "d46a6cae-ba7a-412e-85b7-d334f175efaa",
#       "postprocessor_type": "reranker",
#       "model": {
#         "idx": "374e7471-bd7d-41d0-b69d-a749a052b4b0",
#         "type": "reranker",
#         "model_id": "BAAI/bge-reranker-large",
#         "model_path": "/home/user/models/bge_ov_reranker",
#         "device": "auto"
#       },
#       "top_n": 2
#     }
#   ],
#   "generator": {
#     "idx": "52d8f112-6290-4dd3-bc28-f9bd5deeb7c8",
#     "generator_type": "local",
#     "model": {
#       "idx": "fa0c11e1-46d1-4df8-a6d8-48cf6b99eff3",
#       "type": "llm",
#       "model_id": "qwen2-7b-instruct",
#       "model_path": "/home/user/models/qwen2-7b-instruct/INT4_compressed_weights",
#       "device": "auto"
#     }
#   },
#   "status": {
#     "active": true
#   }
# }

# Prepare data from local directory
curl -X POST http://${HOST_IP}:16010/v1/data -H "Content-Type: application/json" -d '{"local_path":"#REPLACE WITH YOUR LOCAL DOC DIR#"}' | jq '.'

# Validate Mega Service
curl -X POST http://${HOST_IP}:16011/v1/chatqna -H "Content-Type: application/json" -d '{"messages":"#REPLACE WITH YOUR QUESTION HERE#", "top_n":5, "max_tokens":512}' | jq '.'
```

### ChatQnA with LLM Example (UI)

Open your browser, access http://${HOST_IP}:8082

> Your browser should be running on the same host of your console, otherwise you will need to access UI with your host domain name instead of ${HOST_IP}.

### (Optional) Launch vLLM with OpenVINO service

```bash
# 1. export LLM_MODEL
export LLM_MODEL="your model id"
# 2. Uncomment below code in 'GenAIExamples/EdgeCraftRAG/docker_compose/intel/gpu/arc/compose.yaml'
  # vllm-service:
  #   image: vllm:openvino
  #   container_name: vllm-openvino-server
  #   depends_on:
  #     - vllm-service
  #   ports:
  #     - "8008:80"
  #   environment:
  #     no_proxy: ${no_proxy}
  #     http_proxy: ${http_proxy}
  #     https_proxy: ${https_proxy}
  #     vLLM_ENDPOINT: ${vLLM_ENDPOINT}
  #     LLM_MODEL: ${LLM_MODEL}
  #   entrypoint: /bin/bash -c "\
  #     cd / && \
  #     export VLLM_CPU_KVCACHE_SPACE=50 && \
  #     python3 -m vllm.entrypoints.openai.api_server \
  #       --model '${LLM_MODEL}' \
  #       --host 0.0.0.0 \
  #       --port 80"
```

## Advanced User Guide

### Pipeline Management

#### Create a pipeline

```bash
curl -X POST http://${HOST_IP}:16010/v1/settings/pipelines -H "Content-Type: application/json" -d @examples/test_pipeline.json | jq '.'
```

It will take some time to prepare the embedding model.

#### Upload a text

```bash
curl -X POST http://${HOST_IP}:16010/v1/data -H "Content-Type: application/json" -d @examples/test_data.json | jq '.'
```

#### Provide a query to retrieve context with similarity search.

```bash
curl -X POST http://${HOST_IP}:16010/v1/retrieval -H "Content-Type: application/json" -d @examples/test_query.json | jq '.'
```

#### Create the second pipeline test2

```bash
curl -X POST http://${HOST_IP}:16010/v1/settings/pipelines -H "Content-Type: application/json" -d @examples/test_pipeline2.json | jq '.'
```

#### Check all pipelines

```bash
curl -X GET http://${HOST_IP}:16010/v1/settings/pipelines -H "Content-Type: application/json" | jq '.'
```

#### Compare similarity retrieval (test1) and keyword retrieval (test2)

```bash
# Activate pipeline test1
curl -X PATCH http://${HOST_IP}:16010/v1/settings/pipelines/test1 -H "Content-Type: application/json" -d '{"active": "true"}' | jq '.'
# Similarity retrieval
curl -X POST http://${HOST_IP}:16010/v1/retrieval -H "Content-Type: application/json" -d '{"messages":"number"}' | jq '.'

# Activate pipeline test2
curl -X PATCH http://${HOST_IP}:16010/v1/settings/pipelines/test2 -H "Content-Type: application/json" -d '{"active": "true"}' | jq '.'
# Keyword retrieval
curl -X POST http://${HOST_IP}:16010/v1/retrieval -H "Content-Type: application/json" -d '{"messages":"number"}' | jq '.'

```

### Model Management

#### Load a model

```bash
curl -X POST http://${HOST_IP}:16010/v1/settings/models -H "Content-Type: application/json" -d @examples/test_model_load.json | jq '.'
```

It will take some time to load the model.

#### Check all models

```bash
curl -X GET http://${HOST_IP}:16010/v1/settings/models -H "Content-Type: application/json" | jq '.'
```

#### Update a model

```bash
curl -X PATCH http://${HOST_IP}:16010/v1/settings/models/BAAI/bge-reranker-large -H "Content-Type: application/json" -d @examples/test_model_update.json | jq '.'
```

#### Check a certain model

```bash
curl -X GET http://${HOST_IP}:16010/v1/settings/models/BAAI/bge-reranker-large -H "Content-Type: application/json" | jq '.'
```

#### Delete a model

```bash
curl -X DELETE http://${HOST_IP}:16010/v1/settings/models/BAAI/bge-reranker-large -H "Content-Type: application/json" | jq '.'
```

### File Management

#### Add a text

```bash
curl -X POST http://${HOST_IP}:16010/v1/data -H "Content-Type: application/json" -d @examples/test_data.json | jq '.'
```

#### Add files from existed file path

```bash
curl -X POST http://${HOST_IP}:16010/v1/data -H "Content-Type: application/json" -d @examples/test_data_dir.json | jq '.'
curl -X POST http://${HOST_IP}:16010/v1/data -H "Content-Type: application/json" -d @examples/test_data_file.json | jq '.'
```

#### Check all files

```bash
curl -X GET http://${HOST_IP}:16010/v1/data/files -H "Content-Type: application/json" | jq '.'
```

#### Check one file

```bash
curl -X GET http://${HOST_IP}:16010/v1/data/files/test2.docx -H "Content-Type: application/json" | jq '.'
```

#### Delete a file

```bash
curl -X DELETE http://${HOST_IP}:16010/v1/data/files/test2.docx -H "Content-Type: application/json" | jq '.'
```

#### Update a file

```bash
curl -X PATCH http://${HOST_IP}:16010/v1/data/files/test.pdf -H "Content-Type: application/json" -d @examples/test_data_file.json | jq '.'
```
