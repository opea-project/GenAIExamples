# Build Mega Service of ChatQnA on Xeon

This document outlines the deployment process for OPEA Productivity Suite utilizing the [GenAIComps](https://github.com/opea-project/GenAIComps.git) microservice pipeline on Intel Xeon server and [GenAIExamples](https://github.com/opea-project/GenAIExamppes.git) solutions. The steps include Docker image creation, container deployment via Docker Compose, and service execution to integrate microservices such as `embedding`, `retriever`, `rerank`, and `llm`. We will publish the Docker images to Docker Hub soon, it will simplify the deployment process for this service.

## 🚀 Build Docker Images

First of all, you need to build Docker Images locally and install the python package of it.

```bash
git clone https://github.com/opea-project/GenAIComps.git
cd GenAIComps
```

### 1. Build Embedding Image

```bash
docker build --no-cache -t opea/embedding-tei:latest --build-arg https_proxy=$https_proxy --build-arg http_proxy=$http_proxy -f comps/embeddings/langchain/docker/Dockerfile .
```

### 2. Build Retriever Image

```bash
docker build --no-cache -t opea/retriever-redis:latest --build-arg https_proxy=$https_proxy --build-arg http_proxy=$http_proxy -f comps/retrievers/langchain/redis/docker/Dockerfile .
```

### 3. Build Rerank Image

```bash
docker build --no-cache -t opea/reranking-tei:latest --build-arg https_proxy=$https_proxy --build-arg http_proxy=$http_proxy -f comps/reranks/tei/docker/Dockerfile .
```

### 4. Build LLM Image

#### Use TGI as backend

```bash
docker build --no-cache -t opea/llm-tgi:latest --build-arg https_proxy=$https_proxy --build-arg http_proxy=$http_proxy -f comps/llms/text-generation/tgi/Dockerfile .
```

### 5. Build Dataprep Image

```bash
docker build --no-cache -t opea/dataprep-redis:latest --build-arg https_proxy=$https_proxy --build-arg http_proxy=$http_proxy -f comps/dataprep/redis/langchain/docker/Dockerfile .
cd ..
```

### 6. Build MegaService Docker Images

The Productivity Suite is composed of multiple GenAIExample reference solutions composed together. 

### 6.1 Build ChatQnA MegaService Docker Images

```bash
git clone https://github.com/opea-project/GenAIExamples.git
cd GenAIExamples/ChatQnA/docker
docker build --no-cache -t opea/chatqna:latest --build-arg https_proxy=$https_proxy --build-arg http_proxy=$http_proxy -f Dockerfile .
cd ../../..
```

### 6.2 Build DocSum Megaservice Docker Images

```bash
cd GenAIExamples/DocSum/docker
docker build --no-cache -t opea/docsum:latest --build-arg https_proxy=$https_proxy --build-arg http_proxy=$http_proxy -f Dockerfile .
cd ../../..
```

### 6.3 Build CodeGen Megaservice Docker Images

```bash
cd GenAIExamples/CodeGen/docker
docker build --no-cache -t opea/codegen:latest --build-arg https_proxy=$https_proxy --build-arg http_proxy=$http_proxy -f Dockerfile .
cd ../../..
```

### 6.4 Build FAQGen Megaservice Docker Images

```bash
cd GenAIExamples/FaqGen/docker
docker build --no-cache -t opea/faqgen:latest --build-arg https_proxy=$https_proxy --build-arg http_proxy=$http_proxy -f Dockerfile .
cd ../../..
```

### 7. Build  UI Docker Image (Optional)

Build frontend Docker image that enables via below command:

**Export the value of the public IP address of your Xeon server to the `host_ip` environment variable**

```bash
cd GenAIExamples/ChatQnA/docker/ui/
export BACKEND_SERVICE_ENDPOINT="http://${host_ip}:8888/v1/chatqna"
export DATAPREP_SERVICE_ENDPOINT="http://${host_ip}:6007/v1/dataprep"
export DATAPREP_GET_FILE_ENDPOINT="http://${host_ip}:6007/v1/dataprep/get_file"
docker build --no-cache -t opea/productivity-suite-ui:latest --build-arg https_proxy=$https_proxy --build-arg http_proxy=$http_proxy --build-arg BACKEND_SERVICE_ENDPOINT=$BACKEND_SERVICE_ENDPOINT --build-arg DATAPREP_SERVICE_ENDPOINT=$DATAPREP_SERVICE_ENDPOINT --build-arg DATAPREP_GET_FILE_ENDPOINT=$DATAPREP_GET_FILE_ENDPOINT -f ./docker/Dockerfile.react .
cd ../../../..
```

## 🚀 Start Microservices

### Setup Environment Variables

Since the `compose.yaml` will consume some environment variables, you need to setup them in advance as below.

**Export the value of the public IP address of your Xeon server to the `host_ip` environment variable**

> Change the External_Public_IP below with the actual IPV4 value

```
export host_ip="External_Public_IP"
```

**Export the value of your Huggingface API token to the `your_hf_api_token` environment variable**

> Change the Your_Huggingface_API_Token below with tyour actual Huggingface API Token value

```
export your_hf_api_token="Your_Huggingface_API_Token"
```

**Append the value of the public IP address to the no_proxy list**

```
export your_no_proxy=${your_no_proxy},"External_Public_IP"
```

```bash
export MONGO_HOST=${host_ip}
export MONGO_PORT=27017
export DB_NAME="opea"
export COLLECTION_NAME="Conversations"
export EMBEDDING_MODEL_ID="BAAI/bge-base-en-v1.5"
export RERANK_MODEL_ID="BAAI/bge-reranker-base"
export LLM_MODEL_ID="Intel/neural-chat-7b-v3-3"
export LLM_MODEL_ID_CODEGEN=codellama/CodeLlama-7b-hf
export TEI_EMBEDDING_ENDPOINT="http://${host_ip}:6006"
export TEI_RERANKING_ENDPOINT="http://${host_ip}:8808"
export TGI_LLM_ENDPOINT="http://${host_ip}:9009"
export REDIS_URL="redis://${host_ip}:6379"
export INDEX_NAME="rag-redis"
export HUGGINGFACEHUB_API_TOKEN=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
export MEGA_SERVICE_HOST_IP=${host_ip}
export EMBEDDING_SERVICE_HOST_IP=${host_ip}
export RETRIEVER_SERVICE_HOST_IP=${host_ip}
export RERANK_SERVICE_HOST_IP=${host_ip}
export LLM_SERVICE_HOST_IP=${host_ip}
export LLM_SERVICE_HOST_IP_DOCSUM=${host_ip}
export LLM_SERVICE_HOST_IP_FAQGEN=${host_ip}
export LLM_SERVICE_HOST_IP_CODEGEN=${host_ip}
export LLM_SERVICE_HOST_IP_CHATQNA=${host_ip}
export LLM_SERVICE_HOST_PORT_FAQGEN=9002
export LLM_SERVICE_HOST_PORT_CODEGEN=9001
export LLM_SERVICE_HOST_PORT_DOCSUM=9003
export PROMPT_COLLECTION_NAME="prompt"
export TGI_LLM_ENDPOINT_CHATQNA="http://${host_ip}:9009"
export TGI_LLM_ENDPOINT_CODEGEN="http://${host_ip}:8028"
export TGI_LLM_ENDPOINT_FAQGEN="http://${host_ip}:8008"
export TGI_LLM_ENDPOINT_DOCSUM="http://${host_ip}:8018"
export BACKEND_SERVICE_ENDPOINT_CHATQNA="http://${host_ip}:8888/v1/chatqna"
export DATAPREP_DELETE_FILE_ENDPOINT="http://${host_ip}:6007/v1/dataprep/delete_file"
export DATAPREP_SERVICE_ENDPOINT="http://${host_ip}:6007/v1/dataprep"
export DATAPREP_GET_FILE_ENDPOINT="http://${host_ip}:6007/v1/dataprep/get_file"
export BACKEND_SERVICE_ENDPOINT_FAQGEN="http://${host_ip}:8889/v1/faqgen"
export BACKEND_SERVICE_ENDPOINT_CODEGEN="http://${host_ip}:7778/v1/codegen"
export BACKEND_SERVICE_ENDPOINT_DOCSUM="http://${host_ip}:8890/v1/docsum"
```

Note: Please replace with `host_ip` with you external IP address, do not use localhost.

### Start all the services Docker Containers

> Before running the docker compose command, you need to be in the folder that has the docker compose yaml file

```bash
cd GenAIExamples/ChatQnA/docker/xeon/
```

```bash
docker compose -f compose.yaml up -d
```

### Validate Microservices

1. TEI Embedding Service

```bash
curl ${host_ip}:6006/embed \
    -X POST \
    -d '{"inputs":"What is Deep Learning?"}' \
    -H 'Content-Type: application/json'
```

2. Embedding Microservice

```bash
curl http://${host_ip}:6000/v1/embeddings\
  -X POST \
  -d '{"text":"hello"}' \
  -H 'Content-Type: application/json'
```

3. Retriever Microservice

To consume the retriever microservice, you need to generate a mock embedding vector by Python script. The length of embedding vector
is determined by the embedding model.
Here we use the model `EMBEDDING_MODEL_ID="BAAI/bge-base-en-v1.5"`, which vector size is 768.

Check the vector dimension of your embedding model, set `your_embedding` dimension equals to it.

```bash
export your_embedding=$(python3 -c "import random; embedding = [random.uniform(-1, 1) for _ in range(768)]; print(embedding)")
curl http://${host_ip}:7000/v1/retrieval \
  -X POST \
  -d "{\"text\":\"test\",\"embedding\":${your_embedding}}" \
  -H 'Content-Type: application/json'
```

4. TEI Reranking Service

```bash
curl http://${host_ip}:8808/rerank \
    -X POST \
    -d '{"query":"What is Deep Learning?", "texts": ["Deep Learning is not...", "Deep learning is..."]}' \
    -H 'Content-Type: application/json'
```

5. Reranking Microservice

```bash
curl http://${host_ip}:8000/v1/reranking\
  -X POST \
  -d '{"initial_query":"What is Deep Learning?", "retrieved_docs": [{"text":"Deep Learning is not..."}, {"text":"Deep learning is..."}]}' \
  -H 'Content-Type: application/json'
```

6. LLM backend Service

```bash
# TGI service
curl http://${host_ip}:9009/generate \
  -X POST \
  -d '{"inputs":"What is Deep Learning?","parameters":{"max_new_tokens":17, "do_sample": true}}' \
  -H 'Content-Type: application/json'
```

```bash
# vLLM Service
curl http://${host_ip}:9009/v1/completions \
  -H "Content-Type: application/json" \
  -d '{"model": "Intel/neural-chat-7b-v3-3", "prompt": "What is Deep Learning?", "max_tokens": 32, "temperature": 0}'
```

7. LLM Microservice

```bash
curl http://${host_ip}:9000/v1/chat/completions\
  -X POST \
  -d '{"query":"What is Deep Learning?","max_new_tokens":17,"top_k":10,"top_p":0.95,"typical_p":0.95,"temperature":0.01,"repetition_penalty":1.03,"streaming":true}' \
  -H 'Content-Type: application/json'
```

8. ChatQnA MegaService

```bash
curl http://${host_ip}:8888/v1/chatqna -H "Content-Type: application/json" -d '{
     "messages": "What is the revenue of Nike in 2023?"
     }'
```

9. Dataprep Microservice（Optional）

If you want to update the default knowledge base, you can use the following commands:

Update Knowledge Base via Local File Upload:

```bash
curl -X POST "http://${host_ip}:6007/v1/dataprep" \
     -H "Content-Type: multipart/form-data" \
     -F "files=@./nke-10k-2023.pdf"
```

This command updates a knowledge base by uploading a local file for processing. Update the file path according to your environment.

Add Knowledge Base via HTTP Links:

```bash
curl -X POST "http://${host_ip}:6007/v1/dataprep" \
     -H "Content-Type: multipart/form-data" \
     -F 'link_list=["https://opea.dev"]'
```

This command updates a knowledge base by submitting a list of HTTP links for processing.

Also, you are able to get the file list that you uploaded:

```bash
curl -X POST "http://${host_ip}:6007/v1/dataprep/get_file" \
     -H "Content-Type: application/json"
```

To delete the file/link you uploaded:

```bash
# delete link
curl -X POST "http://${host_ip}:6007/v1/dataprep/delete_file" \
     -d '{"file_path": "https://opea.dev"}' \
     -H "Content-Type: application/json"

# delete file
curl -X POST "http://${host_ip}:6007/v1/dataprep/delete_file" \
     -d '{"file_path": "nke-10k-2023.pdf"}' \
     -H "Content-Type: application/json"

# delete all uploaded files and links
curl -X POST "http://${host_ip}:6007/v1/dataprep/delete_file" \
     -d '{"file_path": "all"}' \
     -H "Content-Type: application/json"
```
## 🚀 Launch the UI

To access the frontend, open the following URL in your browser: http://{host_ip}:5173. By default, the UI runs on port 5173 internally. If you prefer to use a different host port to access the frontend, you can modify the port mapping in the `compose.yaml` file as shown below:

```yaml

#TODO
  comboapp-ui-server:
    image: opea/chatqna-ui:latest
    ...
    ports:
      - "80:5173"
```

#TODO
![project-screenshot](../../assets/img/chat_ui_init.png)

Here is an example of running Productivity Suite