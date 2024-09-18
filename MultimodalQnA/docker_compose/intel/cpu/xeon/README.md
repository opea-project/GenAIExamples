# Build Mega Service of MultimodalQnA on Xeon

This document outlines the deployment process for a MultimodalQnA application utilizing the [GenAIComps](https://github.com/opea-project/GenAIComps.git) microservice pipeline on Intel Xeon server. The steps include Docker image creation, container deployment via Docker Compose, and service execution to integrate microservices such as `multimodal_embedding` that employs [BridgeTower](https://huggingface.co/BridgeTower/bridgetower-large-itm-mlm-gaudi) model as embedding model, `multimodal_retriever`, `lvm`, and `multimodal-data-prep`. We will publish the Docker images to Docker Hub soon, it will simplify the deployment process for this service.

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

embedding-multimodal-bridgetower
=====================
Port 6006 - Open to 0.0.0.0/0

embedding-multimodal
=========
Port 6000 - Open to 0.0.0.0/0

retriever-multimodal-redis
=========
Port 7000 - Open to 0.0.0.0/0

lvm-llava
================
Port 8399 - Open to 0.0.0.0/0

lvm-llava-svc
===
Port 9399 - Open to 0.0.0.0/0

dataprep-multimodal-redis
===
Port 6007 - Open to 0.0.0.0/0

multimodalqna
==========================
Port 8888 - Open to 0.0.0.0/0

multimodalqna-ui
=====================
Port 5173 - Open to 0.0.0.0/0
```

## Setup Environment Variables

Since the `compose.yaml` will consume some environment variables, you need to setup them in advance as below.

**Export the value of the public IP address of your Xeon server to the `host_ip` environment variable**

> Change the External_Public_IP below with the actual IPV4 value

```
export host_ip="External_Public_IP"
```

**Append the value of the public IP address to the no_proxy list**

```bash
export your_no_proxy=${your_no_proxy},"External_Public_IP"
```

```bash
export no_proxy=${your_no_proxy}
export http_proxy=${your_http_proxy}
export https_proxy=${your_http_proxy}
export EMBEDDER_PORT=6006
export MMEI_EMBEDDING_ENDPOINT="http://${host_ip}:$EMBEDDER_PORT/v1/encode"
export MM_EMBEDDING_PORT_MICROSERVICE=6000
export REDIS_URL="redis://${host_ip}:6379"
export REDIS_HOST=${host_ip}
export INDEX_NAME="mm-rag-redis"
export LLAVA_SERVER_PORT=8399
export LVM_ENDPOINT="http://${host_ip}:8399"
export EMBEDDING_MODEL_ID="BridgeTower/bridgetower-large-itm-mlm-itc"
export WHISPER_MODEL="base"
export MM_EMBEDDING_SERVICE_HOST_IP=${host_ip}
export MM_RETRIEVER_SERVICE_HOST_IP=${host_ip}
export LVM_SERVICE_HOST_IP=${host_ip}
export MEGA_SERVICE_HOST_IP=${host_ip}
export BACKEND_SERVICE_ENDPOINT="http://${host_ip}:8888/v1/multimodalqna"
export DATAPREP_GEN_TRANSCRIPT_SERVICE_ENDPOINT="http://${host_ip}:6007/v1/generate_transcripts"
export DATAPREP_GEN_CAPTION_SERVICE_ENDPOINT="http://${host_ip}:6007/v1/generate_captions"
export DATAPREP_GET_VIDEO_ENDPOINT="http://${host_ip}:6007/v1/dataprep/get_videos"
export DATAPREP_DELETE_VIDEO_ENDPOINT="http://${host_ip}:6007/v1/dataprep/delete_videos"
```

Note: Please replace with `host_ip` with you external IP address, do not use localhost.

## 🚀 Build Docker Images

### 1. Build embedding-multimodal-bridgetower Image

Build embedding-multimodal-bridgetower docker image

```bash
git clone https://github.com/opea-project/GenAIComps.git
cd GenAIComps
docker build --no-cache -t opea/embedding-multimodal-bridgetower:latest --build-arg EMBEDDER_PORT=$EMBEDDER_PORT --build-arg https_proxy=$https_proxy --build-arg http_proxy=$http_proxy -f comps/embeddings/multimodal/bridgetower/Dockerfile .
```

Build embedding-multimodal microservice image

```bash
docker build --no-cache -t opea/embedding-multimodal:latest --build-arg https_proxy=$https_proxy --build-arg http_proxy=$http_proxy -f comps/embeddings/multimodal/multimodal_langchain/Dockerfile .
```

### 2. Build retriever-multimodal-redis Image

```bash
docker build --no-cache -t opea/retriever-multimodal-redis:latest --build-arg https_proxy=$https_proxy --build-arg http_proxy=$http_proxy -f comps/retrievers/multimodal/redis/langchain/Dockerfile .
```

### 3. Build LVM Images

Build lvm-llava image

```bash
docker build --no-cache -t opea/lvm-llava:latest --build-arg https_proxy=$https_proxy --build-arg http_proxy=$http_proxy -f comps/lvms/llava/dependency/Dockerfile .
```

Build lvm-llava-svc microservice image

```bash
docker build --no-cache -t opea/lvm-llava-svc:latest --build-arg https_proxy=$https_proxy --build-arg http_proxy=$http_proxy -f comps/lvms/llava/Dockerfile .
```

### 4. Build dataprep-multimodal-redis Image

```bash
docker build --no-cache -t opea/dataprep-multimodal-redis:latest --build-arg https_proxy=$https_proxy --build-arg http_proxy=$http_proxy -f comps/dataprep/multimodal/redis/langchain/Dockerfile .
```

### 5. Build MegaService Docker Image

To construct the Mega Service, we utilize the [GenAIComps](https://github.com/opea-project/GenAIComps.git) microservice pipeline within the [multimodalqna.py](../../../../multimodalqna.py) Python script. Build MegaService Docker image via below command:

```bash
git clone https://github.com/opea-project/GenAIExamples.git
cd GenAIExamples/MultimodalQnA
docker build --no-cache -t opea/multimodalqna:latest --build-arg https_proxy=$https_proxy --build-arg http_proxy=$http_proxy -f Dockerfile .
cd ../..
```

### 6. Build UI Docker Image

Build frontend Docker image via below command:

```bash
cd GenAIExamples/MultimodalQnA/ui/
docker build --no-cache -t opea/multimodalqna-ui:latest --build-arg https_proxy=$https_proxy --build-arg http_proxy=$http_proxy -f ./docker/Dockerfile .
cd ../../../
```

Then run the command `docker images`, you will have the following 8 Docker Images:

1. `opea/dataprep-multimodal-redis:latest`
2. `opea/lvm-llava-svc:latest`
3. `opea/lvm-llava:latest`
4. `opea/retriever-multimodal-redis:latest`
5. `opea/embedding-multimodal:latest`
6. `opea/embedding-multimodal-bridgetower:latest`
7. `opea/multimodalqna:latest`
8. `opea/multimodalqna-ui:latest`

## 🚀 Start Microservices

### Required Models

By default, the multimodal-embedding and LVM models are set to a default value as listed below:

| Service              | Model                                       |
| -------------------- | ------------------------------------------- |
| embedding-multimodal | BridgeTower/bridgetower-large-itm-mlm-gaudi |
| LVM                  | llava-hf/llava-1.5-7b-hf                    |

### Start all the services Docker Containers

> Before running the docker compose command, you need to be in the folder that has the docker compose yaml file

```bash
cd GenAIExamples/MultimodalQnA/docker_compose/intel/cpu/xeon/
docker compose -f compose.yaml up -d
```

### Validate Microservices

1. embedding-multimodal-bridgetower

```bash
curl http://${host_ip}:${EMBEDDER_PORT}/v1/encode \
     -X POST \
     -H "Content-Type:application/json" \
     -d '{"text":"This is example"}'
```

```bash
curl http://${host_ip}:${EMBEDDER_PORT}/v1/encode \
     -X POST \
     -H "Content-Type:application/json" \
     -d '{"text":"This is example", "img_b64_str": "iVBORw0KGgoAAAANSUhEUgAAAAoAAAAKCAYAAACNMs+9AAAAFUlEQVR42mP8/5+hnoEIwDiqkL4KAcT9GO0U4BxoAAAAAElFTkSuQmCC"}'
```

2. embedding-multimodal

```bash
curl http://${host_ip}:$MM_EMBEDDING_PORT_MICROSERVICE/v1/embeddings \
    -X POST \
    -H "Content-Type: application/json" \
    -d '{"text" : "This is some sample text."}'
```

```bash
curl http://${host_ip}:$MM_EMBEDDING_PORT_MICROSERVICE/v1/embeddings \
    -X POST \
    -H "Content-Type: application/json" \
    -d '{"text": {"text" : "This is some sample text."}, "image" : {"url": "https://github.com/docarray/docarray/blob/main/tests/toydata/image-data/apple.png?raw=true"}}'
```

3. retriever-multimodal-redis

```bash
export your_embedding=$(python3 -c "import random; embedding = [random.uniform(-1, 1) for _ in range(512)]; print(embedding)")
curl http://${host_ip}:7000/v1/multimodal_retrieval \
    -X POST \
    -H "Content-Type: application/json" \
    -d "{\"text\":\"test\",\"embedding\":${your_embedding}}"
```

4. lvm-llava

```bash
curl http://${host_ip}:${LLAVA_SERVER_PORT}/generate \
     -X POST \
     -H "Content-Type:application/json" \
     -d '{"prompt":"Describe the image please.", "img_b64_str": "iVBORw0KGgoAAAANSUhEUgAAAAoAAAAKCAYAAACNMs+9AAAAFUlEQVR42mP8/5+hnoEIwDiqkL4KAcT9GO0U4BxoAAAAAElFTkSuQmCC"}'
```

5. lvm-llava-svc

```bash
curl http://${host_ip}:9399/v1/lvm \
    -X POST \
    -H 'Content-Type: application/json' \
    -d '{"retrieved_docs": [], "initial_query": "What is this?", "top_n": 1, "metadata": [{"b64_img_str": "iVBORw0KGgoAAAANSUhEUgAAAAoAAAAKCAYAAACNMs+9AAAAFUlEQVR42mP8/5+hnoEIwDiqkL4KAcT9GO0U4BxoAAAAAElFTkSuQmCC", "transcript_for_inference": "yellow image", "video_id": "8c7461df-b373-4a00-8696-9a2234359fe0", "time_of_frame_ms":"37000000", "source_video":"WeAreGoingOnBullrun_8c7461df-b373-4a00-8696-9a2234359fe0.mp4"}], "chat_template":"The caption of the image is: '\''{context}'\''. {question}"}'
```

```bash
curl http://${host_ip}:9399/v1/lvm  \
    -X POST \
    -H 'Content-Type: application/json' \
    -d '{"image": "iVBORw0KGgoAAAANSUhEUgAAAAoAAAAKCAYAAACNMs+9AAAAFUlEQVR42mP8/5+hnoEIwDiqkL4KAcT9GO0U4BxoAAAAAElFTkSuQmCC", "prompt":"What is this?"}'
```

Also, validate LVM Microservice with empty retrieval results

```bash
curl http://${host_ip}:9399/v1/lvm \
    -X POST \
    -H 'Content-Type: application/json' \
    -d '{"retrieved_docs": [], "initial_query": "What is this?", "top_n": 1, "metadata": [], "chat_template":"The caption of the image is: '\''{context}'\''. {question}"}'
```

6. dataprep-multimodal-redis

Download a sample video

```bash
export video_fn="WeAreGoingOnBullrun.mp4"
wget http://commondatastorage.googleapis.com/gtv-videos-bucket/sample/WeAreGoingOnBullrun.mp4 -O ${video_fn}
```

Test dataprep microservice. This command updates a knowledge base by uploading a local video .mp4.

```bash
curl --silent --write-out "HTTPSTATUS:%{http_code}" \
    ${DATAPREP_GEN_TRANSCRIPT_SERVICE_ENDPOINT} \
    -H 'Content-Type: multipart/form-data' \
    -X POST -F "files=@./${video_fn}"
```

Also, test dataprep microservice with generating caption using lvm microservice

```bash
curl --silent --write-out "HTTPSTATUS:%{http_code}" \
    ${DATAPREP_GEN_CAPTION_SERVICE_ENDPOINT} \
    -H 'Content-Type: multipart/form-data' \
    -X POST -F "files=@./${video_fn}"
```

Also, you are able to get the list of all videos that you uploaded:

```bash
curl -X POST \
    -H "Content-Type: application/json" \
    ${DATAPREP_GET_VIDEO_ENDPOINT}
```

Then you will get the response python-style LIST like this. Notice the name of each uploaded video e.g., `videoname.mp4` will become `videoname_uuid.mp4` where `uuid` is a unique ID for each uploaded video. The same video that are uploaded twice will have different `uuid`.

```bash
[
    "WeAreGoingOnBullrun_7ac553a1-116c-40a2-9fc5-deccbb89b507.mp4",
    "WeAreGoingOnBullrun_6d13cf26-8ba2-4026-a3a9-ab2e5eb73a29.mp4"
]
```

To delete all uploaded videos along with data indexed with `$INDEX_NAME` in REDIS.

```bash
curl -X POST \
    -H "Content-Type: application/json" \
    ${DATAPREP_DELETE_VIDEO_ENDPOINT}
```

7. MegaService

```bash
curl http://${host_ip}:8888/v1/multimodalqna \
    -H "Content-Type: application/json" \
    -X POST \
    -d '{"messages": "What is the revenue of Nike in 2023?"}'
```

```bash
curl http://${host_ip}:8888/v1/multimodalqna \
    -H "Content-Type: application/json" \
    -d '{"messages": [{"role": "user", "content": [{"type": "text", "text": "hello, "}, {"type": "image_url", "image_url": {"url": "https://www.ilankelman.org/stopsigns/australia.jpg"}}]}, {"role": "assistant", "content": "opea project! "}, {"role": "user", "content": "chao, "}], "max_tokens": 10}'
```
