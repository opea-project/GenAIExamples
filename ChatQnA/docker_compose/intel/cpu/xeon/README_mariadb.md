# Deploying ChatQnA with MariaDB Vector on Intel® Xeon® Processors

This document outlines the deployment process for a ChatQnA application utilizing the [GenAIComps](https://github.com/opea-project/GenAIComps.git) microservice pipeline on Intel® Xeon® servers. The pipeline integrates **MariaDB Vector** as the vector database and includes microservices such as `embedding`, `retriever`, `rerank`, and `llm`.

---

## Table of Contents

1. [Build Docker Images](#build-docker-images)
2. [Validate Microservices](#validate-microservices)
3. [Launch the UI](#launch-the-ui)
4. [Launch the Conversational UI (Optional)](#launch-the-conversational-ui-optional)

---

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

To construct the Mega Service, we utilize the [GenAIComps](https://github.com/opea-project/GenAIComps.git) microservice pipeline within the `chatqna.py` Python script. Build MegaService Docker image via below command:

```bash
git clone https://github.com/opea-project/GenAIExamples.git
cd GenAIExamples/ChatQnA/
docker build --no-cache -t opea/chatqna:latest --build-arg https_proxy=$https_proxy --build-arg http_proxy=$http_proxy -f Dockerfile .
cd ../..
```

### 4. Build UI Docker Image

Build frontend Docker image via below command:

```bash
cd GenAIExamples/ChatQnA/ui
docker build --no-cache -t opea/chatqna-ui:latest --build-arg https_proxy=$https_proxy --build-arg http_proxy=$http_proxy -f ./docker/Dockerfile .
cd ../../..
```

### 5. Build Conversational React UI Docker Image (Optional)

Build frontend Docker image that enables Conversational experience with ChatQnA megaservice via below command:

**Export the value of the public IP address of your Xeon server to the `host_ip` environment variable**

```bash
cd GenAIExamples/ChatQnA/ui
export BACKEND_SERVICE_ENDPOINT="http://${host_ip}:8912/v1/chatqna"
export DATAPREP_SERVICE_ENDPOINT="http://${host_ip}:6043/v1/dataprep/ingest"
docker build --no-cache -t opea/chatqna-conversation-ui:latest --build-arg https_proxy=$https_proxy --build-arg http_proxy=$http_proxy --build-arg BACKEND_SERVICE_ENDPOINT=$BACKEND_SERVICE_ENDPOINT --build-arg DATAPREP_SERVICE_ENDPOINT=$DATAPREP_SERVICE_ENDPOINT -f ./docker/Dockerfile.react .
cd ../../..
```

### 6. Build Nginx Docker Image

```bash
cd GenAIComps
docker build -t opea/nginx:latest --build-arg https_proxy=$https_proxy --build-arg http_proxy=$http_proxy -f comps/third_parties/nginx/src/Dockerfile .
```

Then run the command `docker images`, you will have the following 5 Docker Images:

1. `opea/dataprep:latest`
2. `opea/retriever:latest`
3. `opea/chatqna:latest`
4. `opea/chatqna-ui:latest`
5. `opea/nginx:latest`

## Start Microservices

### Required Models

By default, the embedding, reranking and LLM models are set to a default value as listed below:

| Service   | Model                               |
| --------- | ----------------------------------- |
| Embedding | BAAI/bge-base-en-v1.5               |
| Reranking | BAAI/bge-reranker-base              |
| LLM       | meta-llama/Meta-Llama-3-8B-Instruct |

Change the `xxx_MODEL_ID` below for your needs.

### Setup Environment Variables

Since the `compose.yaml` will consume some environment variables, you need to set them up in advance as below.

**Export the value of the public IP address of your Xeon server to the `host_ip` environment variable**

> Change the External_Public_IP below with the actual IPV4 value

```bash
export host_ip="External_Public_IP"
```

> Change to your actual Huggingface API Token value

```bash
export HUGGINGFACEHUB_API_TOKEN="Your_Huggingface_API_Token"
```

**Append the value of the public IP address to the no_proxy list if you are in a proxy environment**

```bash
export no_proxy=${your_no_proxy},chatqna-xeon-ui-server,chatqna-xeon-backend-server,dataprep-mariadb-vector,tei-embedding-service,retriever,tei-reranking-service,tgi-service,vllm-service
```

```bash
export no_proxy=${your_no_proxy}
export http_proxy=${your_http_proxy}
export https_proxy=${your_http_proxy}
export EMBEDDING_MODEL_ID="BAAI/bge-base-en-v1.5"
export RERANK_MODEL_ID="BAAI/bge-reranker-base"
export LLM_MODEL_ID="meta-llama/Meta-Llama-3-8B-Instruct"
export MARIADB_DATABASE="vectordb"
export MARIADB_USER="chatqna"
export MARIADB_PASSWORD="password"
```

Note: Please replace with `host_ip` with you external IP address, do not use localhost.

### Start all the services Docker Containers

> Before running the docker compose command, you need to be in the folder that has the docker compose yaml file

```bash
cd GenAIExamples/ChatQnA/docker_compose/intel/cpu/xeon/
docker compose -f compose_mariadb.yaml up -d
```

### Validate Microservices

Follow the instructions to validate MicroServices.
For details on how to verify the correctness of the response, refer to [how-to-validate_service](../../hpu/gaudi/how_to_validate_service.md).

1. TEI Embedding Service

   ```bash
   curl ${host_ip}:6040/embed \
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
   curl http://${host_ip}:6045/v1/retrieval \
     -X POST \
     -d '{"text":"What is the revenue of Nike in 2023?","embedding":"'"${your_embedding}"'"}' \
     -H 'Content-Type: application/json'
   ```

3. TEI Reranking Service

   ```bash
   curl http://${host_ip}:6041/rerank \
       -X POST \
       -d '{"query":"What is Deep Learning?", "texts": ["Deep Learning is not...", "Deep learning is..."]}' \
       -H 'Content-Type: application/json'
   ```

4. LLM Backend Service

   In the first startup, this service will take more time to download, load and warm up the model. After it's finished, the service will be ready.

   Try the command below to check whether the LLM service is ready.

   ```bash
   docker logs vllm-service 2>&1 | grep complete
   ```

   If the service is ready, you will get the response like below.

   ```text
   INFO: Application startup complete.
   ```

   Then try the `cURL` command below to validate vLLM service.

   ```bash
   curl http://${host_ip}:6042/v1/chat/completions \
     -X POST \
     -d '{"model": "meta-llama/Meta-Llama-3-8B-Instruct", "messages": [{"role": "user", "content": "What is Deep Learning?"}], "max_tokens":17}' \
     -H 'Content-Type: application/json'
   ```

5. MegaService

   ```bash
   curl http://${host_ip}:8912/v1/chatqna -H "Content-Type: application/json" -d '{
        "messages": "What is the revenue of Nike in 2023?"
        }'
   ```

6. Dataprep Microservice（Optional）

   If you want to update the default knowledge base, you can use the following commands:

   Update Knowledge Base via Local File Upload:

   ```bash
   curl -X POST "http://${host_ip}:6043/v1/dataprep/ingest" \
        -H "Content-Type: multipart/form-data" \
        -F "files=@./your_file.pdf"
   ```

   This command updates a knowledge base by uploading a local file for processing. Update the file path according to your environment.

   Add Knowledge Base via HTTP Links:

   ```bash
   curl -X POST "http://${host_ip}:6043/v1/dataprep/ingest" \
        -H "Content-Type: multipart/form-data" \
        -F 'link_list=["https://opea.dev"]'
   ```

## Launch the UI

To access the frontend, open the following URL in your browser: http://{host_ip}:5173. By default, the UI runs on port 5173 internally. If you prefer to use a different host port to access the frontend, you can modify the port mapping in the `compose.yaml` file as shown below:

```yaml
  chatqna-xeon-ui-server:
    image: opea/chatqna-ui:latest
    ...
    ports:
      - "80:5173"
```

![project-screenshot](../../../../assets/img/chat_ui_init.png)

Here is an example of running ChatQnA:

![project-screenshot](../../../../assets/img/chat_ui_response.png)
