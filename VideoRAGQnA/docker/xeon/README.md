# Build Mega Service of videoragqna on Xeon

This document outlines the deployment process for a videoragqna application utilizing the [GenAIComps](https://github.com/opea-project/GenAIComps.git) microservice pipeline on Intel Xeon server. The steps include Docker image creation, container deployment via Docker Compose, and service execution to integrate microservices such as `embedding`, `retriever`, `rerank`, and `lvm`. We will publish the Docker images to Docker Hub soon, it will simplify the deployment process for this service.

## 🚀 Port used for the microservices

```
vdms-vector-db
===============
Port 8001 - Open to 0.0.0.0/0

embedding
=========
Port 6000 - Open to 0.0.0.0/0

retriever
=========
Port 7000 - Open to 0.0.0.0/0

reranking
=========
Port 8000 - Open to 0.0.0.0/0

lvm video-llama
===============
Port 9009 - Open to 0.0.0.0/0

lvm
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
docker build --no-cache -t opea/embedding-multimodal:latest --build-arg https_proxy=$https_proxy --build-arg http_proxy=$http_proxy -f comps/embeddings/langchain_multimodal/docker/Dockerfile .
```

### 2. Build Retriever Image

```bash
docker build --no-cache -t opea/retriever-vdms:latest --build-arg https_proxy=$https_proxy --build-arg http_proxy=$http_proxy --build-arg huggingfacehub_api_token=$hf_token -f comps/retrievers/langchain/vdms/docker/Dockerfile .
# FIXME: OK to rm the token?
```

### 3. Build Rerank Image

```bash
docker build --no-cache -t opea/reranking-videoragqna:latest --build-arg https_proxy=$https_proxy --build-arg http_proxy=$http_proxy  -f comps/reranks/video-rag-qna/docker/Dockerfile .
```

### 4. Build LVM Image (Xeon)

```bash
docker build --no-cache -t opea/video-llama-lvm-server:latest --build-arg https_proxy=$https_proxy --build-arg http_proxy=$http_proxy -f comps/lvms/video-llama/server/docker/Dockerfile .

# LVM Service Image
docker build --no-cache -t opea/lvm-video-llama:latest --build-arg https_proxy=$https_proxy --build-arg http_proxy=$http_proxy  -f comps/lvms/video-llama/Dockerfile .
```

### 5. Build Dataprep Image

```bash
# docker build --no-cache -t opea/dataprep-redis:latest --build-arg https_proxy=$https_proxy --build-arg http_proxy=$http_proxy -f comps/dataprep/redis/langchain/docker/Dockerfile .
cd ..
```

### 6. Build MegaService Docker Image

To construct the Mega Service, we utilize the [GenAIComps](https://github.com/opea-project/GenAIComps.git) microservice pipeline within the `videoragqna.py` Python script. 

Build MegaService Docker image via below command:

```bash
git clone https://github.com/opea-project/GenAIExamples.git
cd GenAIExamples/VideoRAGQnA/docker
docker build --no-cache -t opea/videoragqna:latest --build-arg https_proxy=$https_proxy --build-arg http_proxy=$http_proxy -f Dockerfile .
```

### 7. Build UI Docker Image

Build frontend Docker image via below command:

```bash
cd ui
docker build --no-cache -t opea/videoragqna-ui:latest --build-arg https_proxy=$https_proxy --build-arg http_proxy=$http_proxy -f ./docker/Dockerfile .
```

Then run the command `docker images`, you will have the following 8 Docker Images:

1. `opea/dataprep-vdms:latest`
2. `opea/embedding-multimodal:latest`
3. `opea/retriever-vdms:latest`
4. `opea/reranking-videoragqna:latest`
5. `opea/video-llama-lvm-server:latest`
6. `opea/lvm-video-llama:latest`
7. `opea/videoragqna:latest`
8. `opea/videoragqna-ui:latest`

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
export no_proxy=${your_no_proxy}
export http_proxy=${your_http_proxy}
export https_proxy=${your_http_proxy}
export MEGA_SERVICE_HOST_IP=${host_ip}
export EMBEDDING_SERVICE_HOST_IP=${host_ip}
export RETRIEVER_SERVICE_HOST_IP=${host_ip}
export RERANK_SERVICE_HOST_IP=${host_ip}
export LVM_SERVICE_HOST_IP=${host_ip}
export LVM_ENDPOINT="http://${host_ip}:9009"
export FILE_SERVER_ENDPOINT="http://${host_ip}:8080" # FIXME
export BACKEND_SERVICE_ENDPOINT="http://${host_ip}:8888/v1/chatqna"
export BACKEND_HEALTH_CHECK_ENDPOINT="http://${host_ip}:8888/v1/health_check"
export VDMS_HOST=${host_ip}
export VDMS_PORT=8001
export INDEX_NAME="video-test"
export LLM_DOWNLOAD="True"
export USECLIP=1

# export HUGGINGFACEHUB_API_TOKEN=${your_hf_api_token}
# export DATAPREP_SERVICE_ENDPOINT="http://${host_ip}:6007/v1/dataprep"
# export DATAPREP_GET_FILE_ENDPOINT="http://${host_ip}:6007/v1/dataprep/get_file"
# export DATAPREP_DELETE_FILE_ENDPOINT="http://${host_ip}:6007/v1/dataprep/delete_file"
```

Note: Please replace with `host_ip` with you external IP address, do not use localhost.

### Start all the services Docker Containers

> Before running the docker compose command, you need to be in the folder that has the docker compose yaml file

```bash
cd GenAIExamples/videoragqna/docker/xeon/
```

```bash
docker compose -f compose.yaml up -d
```

### Validate Microservices 
TODO: test all the command


2. Embedding Microservice
TODO
```bash
# curl http://${host_ip}:6000/v1/embeddings\
#   -X POST \
#   -d '{"text":"hello"}' \
#   -H 'Content-Type: application/json'
```

3. Retriever Microservice

To consume the retriever microservice, you need to generate a mock embedding vector by Python script. The length of embedding vector
is determined by the embedding model.
Here we use the model `openai/clip-vit-base-patch32`, which vector size is 512.

Check the vector dimension of your embedding model, set `your_embedding` dimension equals to it.

```bash
export your_embedding=$(python3 -c "import random; embedding = [random.uniform(-1, 1) for _ in range(512)]; print(embedding)")
curl http://${host_ip}:7000/v1/retrieval \
  -X POST \
  -d "{\"text\":\"test\",\"embedding\":${your_embedding}}" \
  -H 'Content-Type: application/json'
```

5. Reranking Microservice
TODO
```bash
# curl http://${host_ip}:8000/v1/reranking\
#   -X POST \
#   -d '{"initial_query":"What is Deep Learning?", "retrieved_docs": [{"text":"Deep Learning is not..."}, {"text":"Deep learning is..."}]}' \
#   -H 'Content-Type: application/json'
```

6. LVM backend Service

In first startup, this service will take times to download the LLM file. After it's finished, the service will be ready.

Use `docker logs video-llama-lvm-server` to check if the download is finished.

```bash
curl -X POST \
  "http://${host_ip}:9009/generate?video_url=silence_girl.mp4&start=0.0&duration=9&prompt=What%20is%20the%20person%20doing%3F&max_new_tokens=150" \
  -H "accept: */*"
  -d ''
```

7. LVM Microservice

This service depends on above LLM backend service startup. It will be ready after long time, to wait for them being ready in first startup.

```bash
curl http://${host_ip}:9000/v1/lvm\
  -X POST \
  -d '{"video_url":"https://github.com/DAMO-NLP-SG/Video-LLaMA/raw/main/examples/silence_girl.mp4","chunk_start": 0,"chunk_duration": 7,"prompt":"What is the person doing?","max_new_tokens": 50}' \
  -H 'Content-Type: application/json'
```

> Please note that the local video will be deleted after completion to conserve disk space.

8. MegaService
TODO
```bash
# curl http://${host_ip}:8888/v1/videoragqna -H "Content-Type: application/json" -d '{
#     #  "messages": "What is the revenue of Nike in 2023?"
#     #  }'
```

9. Dataprep Microservice
TODO
```bash

```

## 🚀 Launch the UI

To access the frontend, open the following URL in your browser: http://{host_ip}:5173. By default, the UI runs on port 5173 internally. If you prefer to use a different host port to access the frontend, you can modify the port mapping in the `compose.yaml` file as shown below:

```yaml
  videoragqna-xeon-ui-server:
    image: opea/videoragqna-ui:latest
    ...
    ports:
      - "80:5173" # port map to host port 80
```

Here is an example of running videoragqna:

![project-screenshot](../../assets/img/videoragqna.png)
