# Build Mega Service of ChatQnA on AIPC

This document outlines the deployment process for a ChatQnA application utilizing the [GenAIComps](https://github.com/opea-project/GenAIComps.git) microservice pipeline on AIPC. The steps include Docker image creation, container deployment via Docker Compose, and service execution to integrate microservices such as `embedding`, `retriever`, `rerank`, and `llm`.

## 🚀 Build Docker Images

First of all, you need to build Docker Images locally and install the python package of it.

```bash
git clone https://github.com/opea-project/GenAIComps.git
cd GenAIComps
```

If you are in a proxy environment, set the proxy-related environment variables:

export http_proxy="Your_HTTP_Proxy"
export https_proxy="Your_HTTPs_Proxy"

### 1. Build Retriever Image

```bash
docker build --no-cache -t opea/retriever-redis:latest --build-arg https_proxy=$https_proxy --build-arg http_proxy=$http_proxy -f comps/retrievers/redis/langchain/Dockerfile .
```

### 2. Set up Ollama Service and Build LLM Image

We use [Ollama](https://ollama.com/) as our LLM service for AIPC.

Please set up Ollama on your PC follow the instructions. This will set the entrypoint needed for the Ollama to suit the ChatQnA examples.

#### 2.1 Set Up Ollama LLM Service

Install Ollama service with one command

curl -fsSL https://ollama.com/install.sh | sh

##### Set Ollama Service Configuration

Ollama Service Configuration file is /etc/systemd/system/ollama.service. Edit the file to set OLLAMA_HOST environment (Replace **${host_ip}** with your host IPV4).

```
Environment="OLLAMA_HOST=${host_ip}:11434"
```

##### Set https_proxy environment for Ollama

if your system access network through proxy, add https_proxy in Ollama Service Configuration file

```
Environment="https_proxy="Your_HTTPS_Proxy"
```

##### Restart Ollam services

```
$ sudo systemctl daemon-reload
$ sudo systemctl restart ollama.service
```

##### Pull LLM model

```
#export OLLAMA_HOST=http://${host_ip}:11434
#ollama pull llam3
#ollama lists
NAME            ID              SIZE    MODIFIED
llama3:latest   365c0bd3c000    4.7 GB  5 days ago
```

#### 2.2 Build LLM Image

```bash
docker build --no-cache -t opea/llm-ollama:latest --build-arg https_proxy=$https_proxy --build-arg http_proxy=$http_proxy -f comps/llms/text-generation/ollama/langchain/Dockerfile .
```

### 3. Build Dataprep Image

```bash
docker build --no-cache -t opea/dataprep-redis:latest --build-arg https_proxy=$https_proxy --build-arg http_proxy=$http_proxy -f comps/dataprep/redis/langchain/Dockerfile .
cd ..
```

### 4. Build MegaService Docker Image

To construct the Mega Service, we utilize the [GenAIComps](https://github.com/opea-project/GenAIComps.git) microservice pipeline within the `chatqna.py` Python script. Build MegaService Docker image via below command:

```bash
git clone https://github.com/opea-project/GenAIExamples.git
cd GenAIExamples/ChatQnA
docker build --no-cache -t opea/chatqna:latest -f Dockerfile .
cd ../../..
```

### 5. Build UI Docker Image

Build frontend Docker image via below command:

```bash
cd GenAIExamples/ChatQnA/ui
docker build --no-cache -t opea/chatqna-ui:latest --build-arg https_proxy=$https_proxy --build-arg http_proxy=$http_proxy -f ./docker/Dockerfile .
cd ../../../..
```

Then run the command `docker images`, you will have the following 5 Docker Images:

1. `opea/dataprep-redis:latest`
2. `opea/retriever-redis:latest`
3. `opea/llm-ollama:latest`
4. `opea/chatqna:latest`
5. `opea/chatqna-ui:latest`

## 🚀 Start Microservices

### Setup Environment Variables

Since the `compose.yaml` will consume some environment variables, you need to setup them in advance as below.

**Export the value of the public IP address of your AIPC to the `host_ip` environment variable**

> Change the External_Public_IP below with the actual IPV4 value

```
export host_ip="External_Public_IP"
```

For Linux users, please run `hostname -I | awk '{print $1}'`. For Windows users, please run `ipconfig | findstr /i "IPv4"` to get the external public ip.

**Export the value of your Huggingface API token to the `your_hf_api_token` environment variable**

> Change the Your_Huggingface_API_Token below with tyour actual Huggingface API Token value

```
export your_hf_api_token="Your_Huggingface_API_Token"
```

**Append the value of the public IP address to the no_proxy list**

```
export your_no_proxy=${your_no_proxy},"External_Public_IP"
```

- Linux PC

```bash
export no_proxy=${your_no_proxy}
export http_proxy=${your_http_proxy}
export https_proxy=${your_http_proxy}
export EMBEDDING_MODEL_ID="BAAI/bge-base-en-v1.5"
export RERANK_MODEL_ID="BAAI/bge-reranker-base"
export TEI_EMBEDDING_ENDPOINT="http://${host_ip}:6006"
export REDIS_URL="redis://${host_ip}:6379"
export INDEX_NAME="rag-redis"
export HUGGINGFACEHUB_API_TOKEN=${your_hf_api_token}
export MEGA_SERVICE_HOST_IP=${host_ip}
export EMBEDDING_SERVER_HOST_IP=${host_ip}
export RETRIEVER_SERVICE_HOST_IP=${host_ip}
export RERANK_SERVER_HOST_IP=${host_ip}
export LLM_SERVER_HOST_IP=${host_ip}
export BACKEND_SERVICE_ENDPOINT="http://${host_ip}:8888/v1/chatqna"
export DATAPREP_SERVICE_ENDPOINT="http://${host_ip}:6007/v1/dataprep"

export OLLAMA_ENDPOINT=http://${host_ip}:11434
export OLLAMA_MODEL="llama3"
```

- Windows PC

```bash
set EMBEDDING_MODEL_ID=BAAI/bge-base-en-v1.5
set RERANK_MODEL_ID=BAAI/bge-reranker-base
set TEI_EMBEDDING_ENDPOINT=http://%host_ip%:6006
set REDIS_URL=redis://%host_ip%:6379
set INDEX_NAME=rag-redis
set HUGGINGFACEHUB_API_TOKEN=%your_hf_api_token%
set MEGA_SERVICE_HOST_IP=%host_ip%
set EMBEDDING_SERVER_HOST_IP=%host_ip%
set RETRIEVER_SERVICE_HOST_IP=%host_ip%
set RERANK_SERVER_HOST_IP=%host_ip%
set LLM_SERVER_HOST_IP=%host_ip%
set BACKEND_SERVICE_ENDPOINT=http://%host_ip%:8888/v1/chatqna
set DATAPREP_SERVICE_ENDPOINT=http://%host_ip%:6007/v1/dataprep

set OLLAMA_ENDPOINT=http://host.docker.internal:11434
set OLLAMA_MODEL="llama3"
```

Note: Please replace with `host_ip` with you external IP address, do not use localhost.

### Start all the services Docker Containers

> Before running the docker compose command, you need to be in the folder that has the docker compose yaml file

```bash
cd GenAIExamples/ChatQnA/docker_compose/intel/cpu/aipc/
docker compose up -d

# let ollama service runs
# e.g. ollama run llama3
OLLAMA_HOST=${host_ip}:11434 ollama run $OLLAMA_MODEL
# for windows
# ollama run %OLLAMA_MODEL%
```

### Validate Microservices

Follow the instructions to validate MicroServices.
For details on how to verify the correctness of the response, refer to [how-to-validate_service](../../hpu/gaudi/how_to_validate_service.md).

1. TEI Embedding Service

   ```bash
   curl ${host_ip}:6006/embed \
       -X POST \
       -d '{"inputs":"What is Deep Learning?"}' \
       -H 'Content-Type: application/json'
   ```

2. Retriever Microservice  
   To validate the retriever microservice, you need to generate a mock embedding vector of length 768 in Python script:

   ```bash
   export your_embedding=$(python3 -c "import random; embedding = [random.uniform(-1, 1) for _ in range(768)]; print(embedding)")
   curl http://${host_ip}:7000/v1/retrieval \
     -X POST \
     -d '{"text":"What is the revenue of Nike in 2023?","embedding":"'"${your_embedding}"'"}' \
     -H 'Content-Type: application/json'
   ```

3. TEI Reranking Service

   ```bash
   curl http://${host_ip}:8808/rerank \
       -X POST \
       -d '{"query":"What is Deep Learning?", "texts": ["Deep Learning is not...", "Deep learning is..."]}' \
       -H 'Content-Type: application/json'
   ```

4. Ollama Service

   ```bash
   curl http://${host_ip}:11434/api/generate -d '{"model": "llama3", "prompt":"What is Deep Learning?"}'
   ```

5. LLM Microservice

   ```bash
   curl http://${host_ip}:9000/v1/chat/completions\
     -X POST \
     -d '{"query":"What is Deep Learning?","max_tokens":17,"top_k":10,"top_p":0.95,"typical_p":0.95,"temperature":0.01,"repetition_penalty":1.03,"streaming":true}' \
     -H 'Content-Type: application/json'
   ```

6. MegaService

   ```bash
   curl http://${host_ip}:8888/v1/chatqna -H "Content-Type: application/json" -d '{
        "messages": "What is the revenue of Nike in 2023?", "model": "'"${OLLAMA_MODEL}"'"
        }'
   ```

7. Dataprep Microservice（Optional）

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

## 🚀 Launch the UI

To access the frontend, open the following URL in your browser: http://{host_ip}:5173.
