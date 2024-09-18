# Build Mega Service of VideoQnA on Xeon

This document outlines the deployment process for a videoqna application utilizing the [GenAIComps](https://github.com/opea-project/GenAIComps.git) microservice pipeline on Intel Xeon server. The steps include Docker image creation, container deployment via Docker Compose, and service execution to integrate microservices such as `embedding`, `retriever`, `rerank`, and `lvm`. We will publish the Docker images to Docker Hub soon, it will simplify the deployment process for this service.

VideoQnA is a pipeline that retrieves video based on provided user prompt. It uses only the video embeddings to perform vector similarity search in Intel's VDMS vector database and performs all operations on Intel Xeon CPU. The pipeline supports long form videos and time-based search.

## 🚀 Port used for the microservices

```
dataprep
========
Port 6007 - Open to 0.0.0.0/0

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

### 1. Build Embedding Image

```bash
git clone https://github.com/opea-project/GenAIComps.git
cd GenAIComps
docker build -t opea/embedding-multimodal-clip:latest --build-arg https_proxy=$https_proxy --build-arg http_proxy=$http_proxy -f comps/embeddings/multimodal_clip/Dockerfile .
```

### 2. Build Retriever Image

```bash
docker build -t opea/retriever-vdms:latest --build-arg https_proxy=$https_proxy --build-arg http_proxy=$http_proxy -f comps/retrievers/vdms/langchain/Dockerfile .
```

### 3. Build Rerank Image

```bash
docker build -t opea/reranking-videoqna:latest --build-arg https_proxy=$https_proxy --build-arg http_proxy=$http_proxy  -f comps/reranks/videoqna/Dockerfile .
```

### 4. Build LVM Image (Xeon)

```bash
docker build -t opea/video-llama-lvm-server:latest --build-arg https_proxy=$https_proxy --build-arg http_proxy=$http_proxy -f comps/lvms/video-llama/dependency/Dockerfile .

# LVM Service Image
docker build -t opea/lvm-video-llama:latest --build-arg https_proxy=$https_proxy --build-arg http_proxy=$http_proxy -f comps/lvms/video-llama/Dockerfile .
```

### 5. Build Dataprep Image

```bash
docker build -t opea/dataprep-multimodal-vdms:latest --build-arg https_proxy=$https_proxy --build-arg http_proxy=$http_proxy -f comps/dataprep/vdms/multimodal_langchain/Dockerfile .
```

### 6. Build MegaService Docker Image

To construct the Mega Service, we utilize the [GenAIComps](https://github.com/opea-project/GenAIComps.git) microservice pipeline within the `videoqna.py` Python script.

Build MegaService Docker image via below command:

```bash
git clone https://github.com/opea-project/GenAIExamples.git
cd GenAIExamples/VideoQnA/
docker build -t opea/videoqna:latest --build-arg https_proxy=$https_proxy --build-arg http_proxy=$http_proxy -f Dockerfile .
```

### 7. Build UI Docker Image

Build frontend Docker image via below command:

```bash
cd GenAIExamples/VideoQnA/ui/
docker build -t opea/videoqna-ui:latest --build-arg https_proxy=$https_proxy --build-arg http_proxy=$http_proxy -f ./docker/Dockerfile .
```

Then run the command `docker images`, you will have the following 8 Docker Images:

1. `opea/dataprep-multimodal-vdms:latest`
2. `opea/embedding-multimodal-clip:latest`
3. `opea/retriever-vdms:latest`
4. `opea/reranking-videoqna:latest`
5. `opea/video-llama-lvm-server:latest`
6. `opea/lvm-video-llama:latest`
7. `opea/videoqna:latest`
8. `opea/videoqna-ui:latest`

## 🚀 Start Microservices

### Setup Environment Variables

Since the `compose.yaml` will consume some environment variables, you need to setup them in advance as below.

**Export the value of the public IP address of your Xeon server to the `host_ip` environment variable**

> Change the `External_Public_IP` below with the actual IPV4 value

```
export host_ip="External_Public_IP"
```

**Export the value of your Huggingface API token to the `your_hf_api_token` environment variable**

> Change the `Your_Huggingface_API_Token` below with your actual Huggingface API Token value

```
export your_hf_api_token="Your_Huggingface_API_Token"
```

**Append the value of the public IP address to the no_proxy list**

```
export your_no_proxy="${your_no_proxy},${host_ip}"
```

Then you can run below commands or `source set_env.sh` to set all the variables

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
export BACKEND_SERVICE_ENDPOINT="http://${host_ip}:8888/v1/videoqna"
export BACKEND_HEALTH_CHECK_ENDPOINT="http://${host_ip}:8888/v1/health_check"
export DATAPREP_SERVICE_ENDPOINT="http://${host_ip}:6007/v1/dataprep"
export DATAPREP_GET_FILE_ENDPOINT="http://${host_ip}:6007/v1/dataprep/get_file"
export DATAPREP_GET_VIDEO_LIST_ENDPOINT="http://${host_ip}:6007/v1/dataprep/get_videos"

export VDMS_HOST=${host_ip}
export VDMS_PORT=8001
export INDEX_NAME="mega-videoqna"
export LLM_DOWNLOAD="True"
export USECLIP=1

export HUGGINGFACEHUB_API_TOKEN=${your_hf_api_token}
```

Note: Replace with `host_ip` with you external IP address, do not use localhost.

### Start all the services with Docker Containers

Before running the docker compose command, you need to be in the folder that has the docker compose yaml file. To avoid model re-download, we manage the volume separately using [external volume](https://docs.docker.com/reference/compose-file/volumes/#external).

There are 2 parts of the pipeline:

- The first is the data preparation, with which you could add your videos into the database.
- The second is the megaservice, serves as the main service, takes the user query, consumes the microservices to give the response. Including embedding, retrieving, reranking and LVM.

In the deploy steps, you need to start the VDMS DB and dataprep firstly, then insert some sample data into it. After that you could get the megaservice up.

```bash
cd GenAIExamples/VideoQnA/docker_compose/intel/cpu/xeon/

docker volume create video-llama-model
docker compose up vdms-vector-db dataprep -d
sleep 1m # wait for the services ready

# Insert some sample data to the DB
curl -X POST http://${host_ip}:6007/v1/dataprep \
      -H "Content-Type: multipart/form-data" \
      -F "files=@./data/op_1_0320241830.mp4"

# Bring all the others
docker compose up -d
# wait until all the services is up. The LVM server will download models, so it take ~1.5hr to get ready.
```

### Validate Microservices

1. Dataprep Microservice

   Once the microservice is up, ingest the videos files into vector store using dataprep microservice. Both single and multiple file(s) uploads are supported.

   ```bash
   # Single file upload
   curl -X POST ${DATAPREP_SERVICE_ENDPOINT} \
       -H "Content-Type: multipart/form-data" \
       -F "files=@./file1.mp4"
   # Multiple file upload
   curl -X POST ${DATAPREP_SERVICE_ENDPOINT} \
       -H "Content-Type: multipart/form-data" \
       -F "files=@./file1.mp4" \
       -F "files=@./file2.mp4" \
       -F "files=@./file3.mp4"
   ```

   Use below method to check and download available videos the microservice. The download endpoint is also used for LVM and UI.

   ```bash
   # List available videos
   curl -X 'GET' ${DATAPREP_GET_VIDEO_LIST_ENDPOINT} -H 'accept: application/json'
   # Download available video
   curl -X 'GET' ${DATAPREP_GET_FILE_ENDPOINT}/video_name.mp4 -H 'accept: application/json'
   ```

2. Embedding Microservice

   ```bash
   curl http://${host_ip}:6000/v1/embeddings \
       -X POST \
       -d '{"text":"Sample text"}' \
       -H 'Content-Type: application/json'
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

4. Reranking Microservice

   ```bash
   curl http://${host_ip}:8000/v1/reranking \
     -X 'POST' \
     -H 'accept: application/json' \
     -H 'Content-Type: application/json' \
     -d '{
       "retrieved_docs": [{"doc": [{"text": "this is the retrieved text"}]}],
       "initial_query": "this is the query",
       "top_n": 1,
       "metadata": [
           {"other_key": "value", "video":"top_video_name", "timestamp":"20"}
       ]
     }'
   ```

5. LVM backend Service

   In first startup, this service will take times to download the LLM file. After it's finished, the service will be ready.

   Use `docker logs video-llama-lvm-server` to check if the download is finished.

   ```bash
   curl -X POST \
     "http://${host_ip}:9009/generate?video_url=silence_girl.mp4&start=0.0&duration=9&prompt=What%20is%20the%20person%20doing%3F&max_new_tokens=150" \
     -H "accept: */*" \
     -d ''
   ```

   > To avoid re-download for the model in case of restart, see [here](#clean-microservices)

6. LVM Microservice

   This service depends on above LLM backend service startup. It will be ready after long time, to wait for them being ready in first startup.

   ```bash
   curl http://${host_ip}:9000/v1/lvm\
     -X POST \
     -d '{"video_url":"https://github.com/DAMO-NLP-SG/Video-LLaMA/raw/main/examples/silence_girl.mp4","chunk_start": 0,"chunk_duration": 7,"prompt":"What is the person doing?","max_new_tokens": 50}' \
     -H 'Content-Type: application/json'
   ```

   > Note that the local video file will be deleted after completion to conserve disk space.

7. MegaService

   ```bash
   curl http://${host_ip}:8888/v1/videoqna -H "Content-Type: application/json" -d '{
         "messages": "What is the man doing?",
         "stream": "True"
         }'
   ```

   > Note that the megaservice support only stream output.

## 🚀 Launch the UI

To access the frontend, open the following URL in your browser: http://{host_ip}:5173. By default, the UI runs on port 5173 internally. If you prefer to use a different host port to access the frontend, you can modify the port mapping in the `compose.yaml` file as shown below:

```yaml
  videoqna-xeon-ui-server:
    image: opea/videoqna-ui:latest
    ...
    ports:
      - "80:5173" # port map to host port 80
```

Here is an example of running videoqna:

![project-screenshot](../../../../assets/img/videoqna.gif)

## Clean Microservices

All the allocated resources could be easily removed by:

```bash
docker compose -f compose.yaml down
```

If you plan to restart the service in the future, the above command is enough. The model file is saved in docker volume `video-llama-model` and will be reserved on your server. Next time when you restart the service, set `export LLM_DOWNLOAD="False"` before start to reuse the volume.

To clean the volume:

```bash
docker volume rm video-llama-model
```
