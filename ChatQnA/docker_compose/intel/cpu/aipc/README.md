# Build Mega Service of ChatQnA on AIPC

This document outlines the deployment process for a ChatQnA application utilizing the [GenAIComps](https://github.com/opea-project/GenAIComps.git) microservice pipeline on AIPC. The steps include Docker image creation, container deployment via Docker Compose, and service execution to integrate microservices such as `embedding`, `retriever`, `rerank`, and `llm`.

## Quick Start:

1. Set up the environment variables.
2. Run Docker Compose.
3. Consume the ChatQnA Service.

### Quick Start: 1. Set up Environment Variable

To set up environment variables for deploying ChatQnA services, follow these steps:

```bash
mkdir ~/OPEA -p
cd ~/OPEA
git clone https://github.com/opea-project/GenAIExamples.git
cd GenAIExamples/ChatQnA/docker_compose/intel/cpu/aipc
```

1. Set the required environment variables:

   ```bash
   export HUGGINGFACEHUB_API_TOKEN="Your_Huggingface_API_Token"
   ```

2. If you are in a proxy environment, also set the proxy-related environment variables:

   ```bash
   export https_proxy="Your_HTTPs_Proxy"
   # Example: no_proxy="localhost, 127.0.0.1, 192.168.1.1"
   export no_proxy=$no_proxy,chatqna-aipc-backend-server,tei-embedding-service,retriever,tei-reranking-service,redis-vector-db,dataprep-redis-service,ollama-service
   ```

3. Set up other environment variables

   By default, llama3.2 is used for LLM serving, the default model can be changed to other LLM models. Please pick a [validated llm models](https://github.com/opea-project/GenAIComps/tree/main/comps/llms/src/text-generation#validated-llm-models) from the table.  
   To change the default model defined in set_env.sh, overwrite it by exporting OLLAMA_MODEL to the new model or by modifying set_env.sh.  
   For example, change to using the following model.

   ```bash
   export OLLAMA_MODEL="deepseek-r1:8b"
   ```

   to use the [DeepSeek-R1-Distill-Llama-8B model](https://ollama.com/library/deepseek-r1:8b)

   ```bash
   source ./set_env.sh
   ```

### Quick Start: 2. Run Docker Compose

```bash
    docker compose up -d
```

It will take several minutes to automatically download the docker images

NB: You should build docker image from source by yourself if:

- You are developing off the git main branch (as the container's ports in the repo may be different from the published docker image).
- You can't download the docker image.
- You want to use a specific version of Docker image.

Please refer to ['Build Docker Images'](#🚀-build-docker-images) in below.

### Quick Start:3. Consume the ChatQnA Service

Once the services are up, open the following URL from your browser: http://{host_ip}:80.
Enter Prompt like What is deep learning?

Or if you prefer to try only on the localhost machine, then try

```bash
curl http://${host_ip}:8888/v1/chatqna \
    -H "Content-Type: application/json" \
    -d '{
        "messages": "What is deep learning?"
    }'
```

## 🚀 Build Docker Images

First of all, you need to build Docker Images locally and install the python package of it.

```bash
mkdir ~/OPEA -p
cd ~/OPEA
git clone https://github.com/opea-project/GenAIComps.git
cd GenAIComps
```

If you are in a proxy environment, set the proxy-related environment variables:

export http_proxy="Your_HTTP_Proxy"
export https_proxy="Your_HTTPs_Proxy"

### 1. Build Retriever Image

```bash
docker build --no-cache -t opea/retriever:latest --build-arg https_proxy=$https_proxy --build-arg http_proxy=$http_proxy -f comps/retrievers/src/Dockerfile .
```

### 2. Build Dataprep Image

```bash
docker build --no-cache -t opea/dataprep:latest --build-arg https_proxy=$https_proxy --build-arg http_proxy=$http_proxy -f comps/dataprep/src/Dockerfile .
cd ..
```

### 3. Build MegaService Docker Image

To construct the Mega Service, we utilize the [GenAIComps](https://github.com/opea-project/GenAIComps.git) microservice pipeline within the `chatqna.py` Python script. Build MegaService Docker image via below command:

```bash
cd ~/OPEA
git clone https://github.com/opea-project/GenAIExamples.git
cd GenAIExamples/ChatQnA
docker build --no-cache -t opea/chatqna:latest --build-arg https_proxy=$https_proxy --build-arg http_proxy=$http_proxy  -f Dockerfile .
```

### 4. Build UI Docker Image

Build frontend Docker image via below command:

```bash
cd ~/OPEA/GenAIExamples/ChatQnA/ui
docker build --no-cache -t opea/chatqna-ui:latest --build-arg https_proxy=$https_proxy --build-arg http_proxy=$http_proxy -f ./docker/Dockerfile .
```

### 5. Build Nginx Docker Image

```bash
cd GenAIComps
docker build -t opea/nginx:latest --build-arg https_proxy=$https_proxy --build-arg http_proxy=$http_proxy -f comps/third_parties/nginx/src/Dockerfile .
```

Then run the command `docker images`, you will have the following Docker Images:

1. `opea/dataprep:latest`
2. `opea/retriever:latest`
3. `opea/chatqna:latest`
4. `opea/chatqna-ui:latest`
5. `opea/nginx:latest`

## 🚀 Start Microservices

### Setup Environment Variables

Since the `compose.yaml` will consume some environment variables, you need to setup them in advance as below.

**Export the value of the public IP address of your AIPC to the `host_ip` environment variable**

> Change the External_Public_IP below with the actual IPV4 value

```
export host_ip="External_Public_IP"
```

For Linux users, please run `hostname -I | awk '{print $1}'`. For Windows users, please run `ipconfig | findstr /i "IPv4"` to get the external public ip.

**Export the value of your Huggingface API token to the `HUGGINGFACEHUB_API_TOKEN` environment variable**

> Change the Your_Huggingface_API_Token below with tyour actual Huggingface API Token value

```
export HUGGINGFACEHUB_API_TOKEN="Your_Huggingface_API_Token"
```

**Append the value of the public IP address to the no_proxy list if you are in a proxy environment**

```
export your_no_proxy=${your_no_proxy},"External_Public_IP",chatqna-aipc-backend-server,tei-embedding-service,retriever,tei-reranking-service,redis-vector-db,dataprep-redis-service,ollama-service
```

- Linux PC

```bash
export no_proxy=${your_no_proxy}
export http_proxy=${your_http_proxy}
export https_proxy=${your_http_proxy}
export EMBEDDING_MODEL_ID="BAAI/bge-base-en-v1.5"
export RERANK_MODEL_ID="BAAI/bge-reranker-base"
export INDEX_NAME="rag-redis"
export HUGGINGFACEHUB_API_TOKEN=${HUGGINGFACEHUB_API_TOKEN}
export OLLAMA_HOST=${host_ip}
export OLLAMA_MODEL="llama3.2"
```

- Windows PC

```bash
set EMBEDDING_MODEL_ID=BAAI/bge-base-en-v1.5
set RERANK_MODEL_ID=BAAI/bge-reranker-base
set INDEX_NAME=rag-redis
set HUGGINGFACEHUB_API_TOKEN=%HUGGINGFACEHUB_API_TOKEN%
set OLLAMA_HOST=host.docker.internal
set OLLAMA_MODEL="llama3.2"
```

Note: Please replace with `host_ip` with you external IP address, do not use localhost.

### Start all the services Docker Containers

> Before running the docker compose command, you need to be in the folder that has the docker compose yaml file

```bash
cd ~/OPEA/GenAIExamples/ChatQnA/docker_compose/intel/cpu/aipc/
docker compose up -d
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
   curl http://${host_ip}:11434/api/generate -d '{"model": "llama3.2", "prompt":"What is Deep Learning?"}'
   ```

5. MegaService

   ```bash
   curl http://${host_ip}:8888/v1/chatqna -H "Content-Type: application/json" -d '{
        "messages": "What is the revenue of Nike in 2023?"
        }'
   ```

6. Upload RAG Files through Dataprep Microservice (Optional)

   To chat with retrieved information, you need to upload a file using Dataprep service.

   Here is an example of Nike 2023 pdf file.

```bash
# download pdf file
wget https://raw.githubusercontent.com/opea-project/GenAIComps/v1.1/comps/retrievers/redis/data/nke-10k-2023.pdf

# upload pdf file with dataprep
curl -X POST "http://${host_ip}:6007/v1/dataprep/ingest" \
     -H "Content-Type: multipart/form-data" \
     -F "files=@./nke-10k-2023.pdf"
```

This command updates a knowledge base by uploading a local file for processing. Update the file path according to your environment.

Alternatively, you can add knowledge base via HTTP Links:

```bash
curl -X POST "http://${host_ip}:6007/v1/dataprep/ingest" \
     -H "Content-Type: multipart/form-data" \
     -F 'link_list=["https://opea.dev"]'
```

This command updates a knowledge base by submitting a list of HTTP links for processing.

To check the uploaded files, you are able to get the file list that uploaded:

```bash
curl -X POST "http://${host_ip}:6007/v1/dataprep/get" \
     -H "Content-Type: application/json"
```

the output is:
`[{"name":"nke-10k-2023.pdf","id":"nke-10k-2023.pdf","type":"File","parent":""}]`

## 🚀 Launch the UI

To access the frontend, open the following URL in your browser: http://{host_ip}:80.
