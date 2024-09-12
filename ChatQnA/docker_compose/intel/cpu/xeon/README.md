# Build Mega Service of ChatQnA on Xeon

This document outlines the deployment process for a ChatQnA application utilizing the [GenAIComps](https://github.com/opea-project/GenAIComps.git) microservice pipeline on Intel Xeon server. The steps include Docker image creation, container deployment via Docker Compose, and service execution to integrate microservices such as `embedding`, `retriever`, `rerank`, and `llm`. We will publish the Docker images to Docker Hub soon, it will simplify the deployment process for this service.

## 🚀 Apply Xeon Server on AWS

To apply a Xeon server on AWS, start by creating an AWS account if you don't have one already. Then, head to the [EC2 Console](https://console.aws.amazon.com/ec2/v2/home) to begin the process. Within the EC2 service, select the Amazon EC2 M7i or M7i-flex instance type to leverage the power of 4th Generation Intel Xeon Scalable processors. These instances are optimized for high-performance computing and demanding workloads.

For detailed information about these instance types, you can refer to this [link](https://aws.amazon.com/ec2/instance-types/m7i/). Once you've chosen the appropriate instance type, proceed with configuring your instance settings, including network configurations, security groups, and storage options.

After launching your instance, you can connect to it using SSH (for Linux instances) or Remote Desktop Protocol (RDP) (for Windows instances). From there, you'll have full access to your Xeon server, allowing you to install, configure, and manage your applications as needed.

**Certain ports in the EC2 instance need to opened up in the security group, for the microservices to work with the curl commands**

> See one example below. Please open up these ports in the EC2 instance based on the IP addresses you want to allow

```
redis-vector-db
===============
Port 6379 - Open to 0.0.0.0/0
Port 8001 - Open to 0.0.0.0/0

tei_embedding_service
=====================
Port 6006 - Open to 0.0.0.0/0

embedding
=========
Port 6000 - Open to 0.0.0.0/0

retriever
=========
Port 7000 - Open to 0.0.0.0/0

tei_xeon_service
================
Port 8808 - Open to 0.0.0.0/0

reranking
=========
Port 8000 - Open to 0.0.0.0/0

tgi-service or vLLM_service
===========
Port 9009 - Open to 0.0.0.0/0

llm
===
Port 9000 - Open to 0.0.0.0/0

chaqna-xeon-backend-server
==========================
Port 8888 - Open to 0.0.0.0/0

chaqna-xeon-ui-server
=====================
Port 5173 - Open to 0.0.0.0/0
```

## 🚀 Build Docker Images

First of all, you need to build Docker Images locally and install the python package of it.

```bash
git clone https://github.com/opea-project/GenAIComps.git
cd GenAIComps
```

### 1. Build Embedding Image

```bash
docker build --no-cache -t opea/embedding-tei:latest --build-arg https_proxy=$https_proxy --build-arg http_proxy=$http_proxy -f comps/embeddings/tei/langchain/Dockerfile .
```

### 2. Build Retriever Image

```bash
docker build --no-cache -t opea/retriever-redis:latest --build-arg https_proxy=$https_proxy --build-arg http_proxy=$http_proxy -f comps/retrievers/redis/langchain/Dockerfile .
```

### 3. Build Rerank Image

> Skip for ChatQnA without Rerank pipeline

```bash
docker build --no-cache -t opea/reranking-tei:latest --build-arg https_proxy=$https_proxy --build-arg http_proxy=$http_proxy -f comps/reranks/tei/Dockerfile .
```

### 4. Build LLM Image

#### Use TGI as backend

```bash
docker build --no-cache -t opea/llm-tgi:latest --build-arg https_proxy=$https_proxy --build-arg http_proxy=$http_proxy -f comps/llms/text-generation/tgi/Dockerfile .
```

#### Use vLLM as backend

Build vLLM docker.

```bash
git clone https://github.com/vllm-project/vllm.git
cd ./vllm/
docker build --no-cache -t opea/vllm:latest --build-arg https_proxy=$https_proxy --build-arg http_proxy=$http_proxy -f Dockerfile.cpu .
cd ..
```

Build microservice.

```bash
docker build --no-cache -t opea/llm-vllm:latest --build-arg https_proxy=$https_proxy --build-arg http_proxy=$http_proxy -f comps/llms/text-generation/vllm/langchain/Dockerfile .
```

### 5. Build Dataprep Image

```bash
docker build --no-cache -t opea/dataprep-redis:latest --build-arg https_proxy=$https_proxy --build-arg http_proxy=$http_proxy -f comps/dataprep/redis/langchain/Dockerfile .
cd ..
```

### 6. Build MegaService Docker Image

1. MegaService with Rerank

   To construct the Mega Service with Rerank, we utilize the [GenAIComps](https://github.com/opea-project/GenAIComps.git) microservice pipeline within the `chatqna.py` Python script. Build MegaService Docker image via below command:

   ```bash
   git clone https://github.com/opea-project/GenAIExamples.git
   cd GenAIExamples/ChatQnA/docker
   docker build --no-cache -t opea/chatqna:latest --build-arg https_proxy=$https_proxy --build-arg http_proxy=$http_proxy -f Dockerfile .
   cd ../../..
   ```

2. MegaService without Rerank

   To construct the Mega Service without Rerank, we utilize the [GenAIComps](https://github.com/opea-project/GenAIComps.git) microservice pipeline within the `chatqna_without_rerank.py` Python script. Build MegaService Docker image via below command:

   ```bash
   git clone https://github.com/opea-project/GenAIExamples.git
   cd GenAIExamples/ChatQnA/docker
   docker build --no-cache -t opea/chatqna-without-rerank:latest --build-arg https_proxy=$https_proxy --build-arg http_proxy=$http_proxy -f Dockerfile.without_rerank .
   cd ../../..
   ```

### 7. Build UI Docker Image

Build frontend Docker image via below command:

```bash
cd GenAIExamples/ChatQnA/ui
docker build --no-cache -t opea/chatqna-ui:latest --build-arg https_proxy=$https_proxy --build-arg http_proxy=$http_proxy -f ./docker/Dockerfile .
cd ../../../..
```

### 8. Build Conversational React UI Docker Image (Optional)

Build frontend Docker image that enables Conversational experience with ChatQnA megaservice via below command:

**Export the value of the public IP address of your Xeon server to the `host_ip` environment variable**

```bash
cd GenAIExamples/ChatQnA/ui
docker build --no-cache -t opea/chatqna-conversation-ui:latest --build-arg https_proxy=$https_proxy --build-arg http_proxy=$http_proxy -f ./docker/Dockerfile.react .
cd ../../../..
```

Then run the command `docker images`, you will have the following 7 Docker Images:

1. `opea/dataprep-redis:latest`
2. `opea/embedding-tei:latest`
3. `opea/retriever-redis:latest`
4. `opea/reranking-tei:latest`
5. `opea/llm-tgi:latest` or `opea/llm-vllm:latest`
6. `opea/chatqna:latest` or `opea/chatqna-without-rerank:latest`
7. `opea/chatqna-ui:latest`

## 🚀 Start Microservices

### Required Models

By default, the embedding, reranking and LLM models are set to a default value as listed below:

| Service   | Model                     |
| --------- | ------------------------- |
| Embedding | BAAI/bge-base-en-v1.5     |
| Reranking | BAAI/bge-reranker-base    |
| LLM       | Intel/neural-chat-7b-v3-3 |

Change the `xxx_MODEL_ID` below for your needs.

For customers with proxy issues, the models from [ModelScope](https://www.modelscope.cn/models) are also supported in ChatQnA with TGI serving. ModelScope models are supported in two ways for TGI:

1. Online

   ```bash
   export HF_TOKEN=${your_hf_token}
   export HF_ENDPOINT="https://hf-mirror.com"
   model_name="Intel/neural-chat-7b-v3-3"
   docker run -p 8008:80 -v ./data:/data --name tgi-service -e HF_ENDPOINT=$HF_ENDPOINT -e http_proxy=$http_proxy -e https_proxy=$https_proxy --shm-size 1g ghcr.io/huggingface/text-generation-inference:2.1.0 --model-id $model_name
   ```

2. Offline

   - Search your model name in ModelScope. For example, check [this page](https://www.modelscope.cn/models/ai-modelscope/neural-chat-7b-v3-1/files) for model `neural-chat-7b-v3-1`.

   - Click on `Download this model` button, and choose one way to download the model to your local path `/path/to/model`.

   - Run the following command to start TGI service.

     ```bash
     export HF_TOKEN=${your_hf_token}
     export model_path="/path/to/model"
     docker run -p 8008:80 -v $model_path:/data --name tgi_service --shm-size 1g ghcr.io/huggingface/text-generation-inference:2.1.0 --model-id /data
     ```

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

```bash
export your_no_proxy=${your_no_proxy},"External_Public_IP"
```

```bash
export no_proxy=${your_no_proxy}
export http_proxy=${your_http_proxy}
export https_proxy=${your_http_proxy}
export EMBEDDING_MODEL_ID="BAAI/bge-base-en-v1.5"
export RERANK_MODEL_ID="BAAI/bge-reranker-base"
export LLM_MODEL_ID="Intel/neural-chat-7b-v3-3"
export TEI_EMBEDDING_ENDPOINT="http://${host_ip}:6006"
export TEI_RERANKING_ENDPOINT="http://${host_ip}:8808"
export TGI_LLM_ENDPOINT="http://${host_ip}:9009"
export vLLM_LLM_ENDPOINT="http://${host_ip}:9009"
export LLM_SERVICE_PORT=9000
export REDIS_URL="redis://${host_ip}:6379"
export INDEX_NAME="rag-redis"
export HUGGINGFACEHUB_API_TOKEN=${your_hf_api_token}
export MEGA_SERVICE_HOST_IP=${host_ip}
export EMBEDDING_SERVICE_HOST_IP=${host_ip}
export RETRIEVER_SERVICE_HOST_IP=${host_ip}
export RERANK_SERVICE_HOST_IP=${host_ip}
export LLM_SERVICE_HOST_IP=${host_ip}
export BACKEND_SERVICE_ENDPOINT="http://${host_ip}:8888/v1/chatqna"
export DATAPREP_SERVICE_ENDPOINT="http://${host_ip}:6007/v1/dataprep"
export DATAPREP_GET_FILE_ENDPOINT="http://${host_ip}:6007/v1/dataprep/get_file"
export DATAPREP_DELETE_FILE_ENDPOINT="http://${host_ip}:6007/v1/dataprep/delete_file"
```

Note: Please replace with `host_ip` with you external IP address, do not use localhost.

### Start all the services Docker Containers

> Before running the docker compose command, you need to be in the folder that has the docker compose yaml file

```bash
cd GenAIExamples/ChatQnA/docker_compose/intel/cpu/xeon/
```

If use TGI backend.

```bash
# Start ChatQnA with Rerank Pipeline
docker compose -f compose.yaml up -d
# Start ChatQnA without Rerank Pipeline
docker compose -f compose_without_rerank.yaml up -d
```

If use vLLM backend.

```bash
docker compose -f compose_vllm.yaml up -d
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

   > Skip for ChatQnA without Rerank pipeline

   ```bash
   curl http://${host_ip}:8808/rerank \
       -X POST \
       -d '{"query":"What is Deep Learning?", "texts": ["Deep Learning is not...", "Deep learning is..."]}' \
       -H 'Content-Type: application/json'
   ```

5. Reranking Microservice

   > Skip for ChatQnA without Rerank pipeline

   ```bash
   curl http://${host_ip}:8000/v1/reranking\
     -X POST \
     -d '{"initial_query":"What is Deep Learning?", "retrieved_docs": [{"text":"Deep Learning is not..."}, {"text":"Deep learning is..."}]}' \
     -H 'Content-Type: application/json'
   ```

6. LLM backend Service

   In first startup, this service will take more time to download the model files. After it's finished, the service will be ready.

   Try the command below to check whether the LLM serving is ready.

   ```bash
   docker logs ${CONTAINER_ID} | grep Connected
   ```

   If the service is ready, you will get the response like below.

   ```
   2024-09-03T02:47:53.402023Z  INFO text_generation_router::server: router/src/server.rs:2311: Connected
   ```

   Then try the `cURL` command below to validate services.

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

   This service depends on above LLM backend service startup. It will be ready after long time, to wait for them being ready in first startup.

   ```bash
   curl http://${host_ip}:9000/v1/chat/completions\
     -X POST \
     -d '{"query":"What is Deep Learning?","max_new_tokens":17,"top_k":10,"top_p":0.95,"typical_p":0.95,"temperature":0.01,"repetition_penalty":1.03,"streaming":true}' \
     -H 'Content-Type: application/json'
   ```

8. MegaService

   ```bash
   curl http://${host_ip}:8888/v1/chatqna -H "Content-Type: application/json" -d '{
        "messages": "What is the revenue of Nike in 2023?"
        }'
   ```

9. Dataprep Microservice（Optional）

   If you want to update the default knowledge base, you can use the following commands:

   Update Knowledge Base via Local File [nke-10k-2023.pdf](https://github.com/opea-project/GenAIComps/blob/main/comps/retrievers/langchain/redis/data/nke-10k-2023.pdf)
   Click [here](https://raw.githubusercontent.com/opea-project/GenAIComps/main/comps/retrievers/langchain/redis/data/nke-10k-2023.pdf) to download the file via any web browser.
   Or run this command to get the file on a terminal.

   ```bash
   wget https://raw.githubusercontent.com/opea-project/GenAIComps/main/comps/retrievers/langchain/redis/data/nke-10k-2023.pdf
   ```

   Upload:

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

   Then you will get the response JSON like this. Notice that the returned `name`/`id` of the uploaded link is `https://xxx.txt`.

   ```json
   [
     {
       "name": "nke-10k-2023.pdf",
       "id": "nke-10k-2023.pdf",
       "type": "File",
       "parent": ""
     },
     {
       "name": "https://opea.dev.txt",
       "id": "https://opea.dev.txt",
       "type": "File",
       "parent": ""
     }
   ]
   ```

   To delete the file/link you uploaded:

   The `file_path` here should be the `id` get from `/v1/dataprep/get_file` API.

   ```bash
   # delete link
   curl -X POST "http://${host_ip}:6007/v1/dataprep/delete_file" \
        -d '{"file_path": "https://opea.dev.txt"}' \
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
  chaqna-gaudi-ui-server:
    image: opea/chatqna-ui:latest
    ...
    ports:
      - "80:5173"
```

## 🚀 Launch the Conversational UI (Optional)

To access the Conversational UI (react based) frontend, modify the UI service in the `compose.yaml` file. Replace `chaqna-xeon-ui-server` service with the `chatqna-xeon-conversation-ui-server` service as per the config below:

```yaml
chaqna-xeon-conversation-ui-server:
  image: opea/chatqna-conversation-ui:latest
  container_name: chatqna-xeon-conversation-ui-server
  environment:
    - APP_BACKEND_SERVICE_ENDPOINT=${BACKEND_SERVICE_ENDPOINT}
    - APP_DATA_PREP_SERVICE_URL=${DATAPREP_SERVICE_ENDPOINT}
  ports:
    - "5174:80"
  depends_on:
    - chaqna-xeon-backend-server
  ipc: host
  restart: always
```

Once the services are up, open the following URL in your browser: http://{host_ip}:5174. By default, the UI runs on port 80 internally. If you prefer to use a different host port to access the frontend, you can modify the port mapping in the `compose.yaml` file as shown below:

```yaml
  chaqna-gaudi-conversation-ui-server:
    image: opea/chatqna-conversation-ui:latest
    ...
    ports:
      - "80:80"
```

![project-screenshot](../../../../assets/img/chat_ui_init.png)

Here is an example of running ChatQnA:

![project-screenshot](../../../../assets/img/chat_ui_response.png)

Here is an example of running ChatQnA with Conversational UI (React):

![project-screenshot](../../../../assets/img/conversation_ui_response.png)
