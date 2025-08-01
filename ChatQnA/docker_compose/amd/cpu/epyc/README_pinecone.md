# Deploying ChatQnA with Pinecone on AMD EPYC™ Processors

This document outlines the deployment process for a ChatQnA application utilizing the [GenAIComps](https://github.com/opea-project/GenAIComps.git) microservice pipeline on AMD EPYC servers. The pipeline integrates **Pinecone** as the vector database (VectorDB) and includes microservices such as `embedding`, `retriever`, `rerank`, and `llm`.

---

## Table of Contents

1. [Quick Start](#quick-start)
2. [Build Docker Images](#build-docker-images)
3. [Validate Microservices](#validate-microservices)
4. [Launch the UI](#launch-the-ui)
5. [Launch the Conversational UI (Optional)](#launch-the-conversational-ui-optional)

---

## Quick Start

### 1.Set up Environment Variable

To set up environment variables for deploying ChatQnA services, follow these steps:

1. Set the required environment variables:

   ```bash
   # Example: host_ip="192.168.1.1"
   export host_ip="External_Public_IP"
   export HF_TOKEN="Your_Huggingface_API_Token"
   ```

2. Set the required Pinecone environment variables:

Please refer to [Getting started with Pinecone](https://docs.pinecone.io/guides/get-started/quickstart) to get the below details.

```bash
export PINECONE_API_KEY="Pinecone_API_Key"
export PINECONE_INDEX_NAME="Pinecone_Index_Name"
export INDEX_NAME="Pinecone_Index_Name"
```

3. If you are in a proxy environment, also set the proxy-related environment variables:

   ```bash
   export http_proxy="Your_HTTP_Proxy"
   export https_proxy="Your_HTTPS_Proxy"
   # Example: no_proxy="localhost,127.0.0.1,192.168.1.1"
   export no_proxy="Your_No_Proxy",chatqna-epyc-ui-server,chatqna-epyc-backend-server,dataprep-pinecone-service,tei-embedding-service,retriever,tei-reranking-service,tgi-service,vllm-service
   ```

4. Set up other environment variables, make sure to update the INDEX_NAME variable to Pinecone index value:
   ```bash
   source ./set_env.sh
   ```

### 2.Run Docker Compose

```bash
docker compose -f compose_pinecone.yaml up -d
```

It will automatically download the Docker image on `Docker hub`:

```bash
docker pull opea/chatqna:latest
docker pull opea/chatqna-ui:latest
```

Note: You should build docker image from source by yourself if:

- You are developing off the git main branch (as the container's ports in the repo may be different from the published docker image).
- You can't download the docker image.
- You want to use a specific version of Docker image.

Please refer to ['Build Docker Images'](#build-docker-images) in below.

### 3.Consume the ChatQnA Service

```bash
curl http://${host_ip}:8888/v1/chatqna \
    -H "Content-Type: application/json" \
    -d '{
        "messages": "What is the revenue of Nike in 2023?"
    }'
```

## Build Docker Images

First of all, you need to build Docker Images locally and install the python package of it.

```bash
git clone https://github.com/opea-project/GenAIComps.git
cd GenAIComps
```

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

1. MegaService with Rerank

   To construct the Mega Service with Rerank, we utilize the [GenAIComps](https://github.com/opea-project/GenAIComps.git) microservice pipeline within the `chatqna.py` Python script. Build MegaService Docker image via below command:

   ```bash
   git clone https://github.com/opea-project/GenAIExamples.git
   cd GenAIExamples/ChatQnA
   docker build --no-cache -t opea/chatqna:latest --build-arg https_proxy=$https_proxy --build-arg http_proxy=$http_proxy -f Dockerfile .
   ```

2. MegaService without Rerank

   To construct the Mega Service without Rerank, we utilize the [GenAIComps](https://github.com/opea-project/GenAIComps.git) microservice pipeline within the `chatqna_without_rerank.py` Python script. Build MegaService Docker image via below command:

   ```bash
   git clone https://github.com/opea-project/GenAIExamples.git
   cd GenAIExamples/ChatQnA
   docker build --no-cache -t opea/chatqna-without-rerank:latest --build-arg https_proxy=$https_proxy --build-arg http_proxy=$http_proxy -f Dockerfile.without_rerank .
   ```

### 4. Build UI Docker Image

Build frontend Docker image via below command:

```bash
cd GenAIExamples/ChatQnA/ui
docker build --no-cache -t opea/chatqna-ui:latest --build-arg https_proxy=$https_proxy --build-arg http_proxy=$http_proxy -f ./docker/Dockerfile .
```

### 5. Build Conversational React UI Docker Image (Optional)

Build frontend Docker image that enables Conversational experience with ChatQnA megaservice via below command:

**Export the value of the public IP address of your epyc server to the `host_ip` environment variable**

```bash
cd GenAIExamples/ChatQnA/ui
docker build --no-cache -t opea/chatqna-conversation-ui:latest --build-arg https_proxy=$https_proxy --build-arg http_proxy=$http_proxy -f ./docker/Dockerfile.react .
```

### 6. Build Nginx Docker Image

```bash
cd GenAIComps
docker build -t opea/nginx:latest --build-arg https_proxy=$https_proxy --build-arg http_proxy=$http_proxy -f comps/third_parties/nginx/src/Dockerfile .
```

Then run the command `docker images`, you will have the following 5 Docker Images:

1. `opea/dataprep:latest`
2. `opea/retriever:latest`
3. `opea/chatqna:latest` or `opea/chatqna-without-rerank:latest`
4. `opea/chatqna-ui:latest`
5. `opea/nginx:latest`

## 🚀 Start Microservices

### Required Models

By default, the embedding, reranking and LLM models are set to a default value as listed below:

| Service   | Model                               |
| --------- | ----------------------------------- |
| Embedding | BAAI/bge-base-en-v1.5               |
| Reranking | BAAI/bge-reranker-base              |
| LLM       | meta-llama/Meta-Llama-3-8B-Instruct |

Change the `xxx_MODEL_ID` below for your needs.

For users in China who are unable to download models directly from Huggingface, you can use [ModelScope](https://www.modelscope.cn/models) or a Huggingface mirror to download models. The vLLM can load the models either online or offline as described below:

1. Online

   ```bash
   export HF_TOKEN=${your_hf_token}
   export HF_ENDPOINT="https://hf-mirror.com"
   model_name="meta-llama/Meta-Llama-3-8B-Instruct"
   docker run -p 8008:80 -v ./data:/root/.cache/huggingface/hub --name vllm-service -e HF_ENDPOINT=$HF_ENDPOINT -e http_proxy=$http_proxy -e https_proxy=$https_proxy --shm-size 128g opea/vllm:latest --model $model_name --host 0.0.0.0 --port 80
   ```

2. Offline

   - Search your model name in ModelScope. For example, check [this page](https://modelscope.cn/models/LLM-Research/Meta-Llama-3-8B-Instruct/files) for model `Meta-Llama-3-8B-Instruct`.

   - Click on `Download this model` button, and choose one way to download the model to your local path `/path/to/model`.

   - Run the following command to start the LLM service.

     ```bash
     export HF_TOKEN=${your_hf_token}
     export model_path="/path/to/model"
     docker run -p 8008:80 -v $model_path:/root/.cache/huggingface/hub --name vllm-service --shm-size 128g opea/vllm:latest --model /root/.cache/huggingface/hub --host 0.0.0.0 --port 80
     ```

### Set up Environment Variables

1. Set the required environment variables:

   ```bash
   # Example: host_ip="192.168.1.1"
   export host_ip="External_Public_IP"
   export HF_TOKEN="Your_Huggingface_API_Token"
   # Example: NGINX_PORT=80
   export NGINX_PORT=${your_nginx_port}
   export PINECONE_API_KEY="Pinecone_API_Key"
   export PINECONE_INDEX_NAME="Pinecone_Index_Name"
   export INDEX_NAME="Pinecone_Index_Name"
   ```

2. If you are in a proxy environment, also set the proxy-related environment variables:

   ```bash
   export http_proxy="Your_HTTP_Proxy"
   export https_proxy="Your_HTTPs_Proxy"
   # Example: no_proxy="localhost, 127.0.0.1, 192.168.1.1"
   export no_proxy="Your_No_Proxy",chatqna-epyc-ui-server,chatqna-epyc-backend-server,dataprep-pinecone-service,tei-embedding-service,retriever,tei-reranking-service,tgi-service,vllm-service
   ```

3. Set up other environment variables, make sure to update the INDEX_NAME variable to use Pinecone Index name:

   ```bash
   source ./set_env.sh
   ```

### Start all the services Docker Containers

> Before running the docker compose command, you need to be in the folder that has the docker compose yaml file

```bash
cd GenAIExamples/ChatQnA/docker_compose/amd/cpu/epyc/
```

If use vLLM backend.

```bash
# Start ChatQnA with Rerank Pipeline
docker compose -f compose_pinecone.yaml up -d
```

## Validate Microservices

Note, when verify the microservices by curl or API from remote client, please make sure the **ports** of the microservices are opened in the firewall of the cloud node.
Follow the instructions to validate MicroServices.

1. TEI Embedding Service

   ```bash
   curl ${host_ip}:6006/embed \
       -X POST \
       -d '{"inputs":"What is Deep Learning?"}' \
       -H 'Content-Type: application/json'
   ```

2. Retriever Microservice

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

3. TEI Reranking Service

   > Skip for ChatQnA without Rerank pipeline

   ```bash
   curl http://${host_ip}:8808/rerank \
       -X POST \
       -d '{"query":"What is Deep Learning?", "texts": ["Deep Learning is not...", "Deep learning is..."]}' \
       -H 'Content-Type: application/json'
   ```

4. LLM backend Service

   In the first startup, this service will take more time to download, load and warm up the model. After it's finished, the service will be ready.

   Try the command below to check whether the LLM serving is ready.

   ```bash
   docker logs vllm-service 2>&1 | grep complete
   ```

   If the service is ready, you will get the response like below.

   ```text
   INFO: Application startup complete.
   ```

   Then try the `cURL` command below to validate services.

   ```bash
   curl http://${host_ip}:9009/v1/chat/completions \
     -X POST \
     -d '{"model": "meta-llama/Meta-Llama-3-8B-Instruct", "messages": [{"role": "user", "content": "What is Deep Learning?"}], "max_tokens":17}' \
     -H 'Content-Type: application/json'
   ```

5. MegaService

   ```bash
    curl http://${host_ip}:8888/v1/chatqna -H "Content-Type: application/json" -d '{
          "messages": "What is the revenue of Nike in 2023?"
          }'
   ```

6. Nginx Service

   ```bash
   curl http://${host_ip}:${NGINX_PORT}/v1/chatqna \
       -H "Content-Type: application/json" \
       -d '{"messages": "What is the revenue of Nike in 2023?"}'
   ```

7. Dataprep Microservice（Optional）

If you want to update the default knowledge base, you can use the following commands:

Update Knowledge Base via Local File [nke-10k-2023.pdf](https://raw.githubusercontent.com/opea-project/GenAIComps/v1.3/comps/third_parties/pathway/src/data/nke-10k-2023.pdf). Or
click [here](https://raw.githubusercontent.com/opea-project/GenAIComps/v1.3/comps/third_parties/pathway/src/data/nke-10k-2023.pdf) to download the file via any web browser.
Or run this command to get the file on a terminal.

```bash
wget https://raw.githubusercontent.com/opea-project/GenAIComps/v1.3/comps/third_parties/pathway/src/data/nke-10k-2023.pdf

```

Upload:

```bash
curl -X POST "http://${host_ip}:6007/v1/dataprep/ingest" \
     -H "Content-Type: multipart/form-data" \
     -F "files=@./nke-10k-2023.pdf"
```

This command updates a knowledge base by uploading a local file for processing. Update the file path according to your environment.

Add Knowledge Base via HTTP Links:

```bash
curl -X POST "http://${host_ip}:6007/v1/dataprep/ingest" \
     -H "Content-Type: multipart/form-data" \
     -F 'link_list=["https://opea.dev"]'
```

This command updates a knowledge base by submitting a list of HTTP links for processing.

To delete the files/link you uploaded:

```bash
# delete all uploaded files and links
curl -X POST "http://${host_ip}:6007/v1/dataprep/delete" \
     -d '{"file_path": "all"}' \
     -H "Content-Type: application/json"
```

## Launch the UI

### Launch with origin port

To access the frontend, open the following URL in your browser: http://{host_ip}:5173. By default, the UI runs on port 5173 internally. If you prefer to use a different host port to access the frontend, you can modify the port mapping in the `compose.yaml` file as shown below:

```yaml
  chaqna-epyc-ui-server:
    image: opea/chatqna-ui:latest
    ...
    ports:
      - "80:5173"
```

### Launch with Nginx

If you want to launch the UI using Nginx, open this URL: `http://${host_ip}:${NGINX_PORT}` in your browser to access the frontend.

## Launch the Conversational UI (Optional)

To access the Conversational UI (react based) frontend, modify the UI service in the `compose.yaml` file. Replace `chaqna-epyc-ui-server` service with the `chatqna-epyc-conversation-ui-server` service as per the config below:

```yaml
chaqna-epyc-conversation-ui-server:
  image: opea/chatqna-conversation-ui:latest
  container_name: chatqna-epyc-conversation-ui-server
  environment:
    - APP_BACKEND_SERVICE_ENDPOINT=${BACKEND_SERVICE_ENDPOINT}
    - APP_DATA_PREP_SERVICE_URL=${DATAPREP_SERVICE_ENDPOINT}
  ports:
    - "5174:80"
  depends_on:
    - chaqna-epyc-backend-server
  ipc: host
  restart: always
```

Once the services are up, open the following URL in your browser: http://{host_ip}:5174. By default, the UI runs on port 80 internally. If you prefer to use a different host port to access the frontend, you can modify the port mapping in the `compose.yaml` file as shown below:

```yaml
  chaqna-epyc-conversation-ui-server:
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
