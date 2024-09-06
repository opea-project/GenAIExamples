# Build Mega Service of MultimodalRAGWithVideos on Xeon

This document outlines the deployment process for a MultimodalRAGWithVideos application utilizing the [GenAIComps](https://github.com/opea-project/GenAIComps.git) microservice pipeline on Intel Xeon server. The steps include Docker image creation, container deployment via Docker Compose, and service execution to integrate microservices such as `multimodal_embedding` that employs [BridgeTower](https://huggingface.co/BridgeTower/bridgetower-large-itm-mlm-gaudi) model as embedding model, `multimodal_retriever`, `lvm`, and `multimodal-data-prep`. We will publish the Docker images to Docker Hub soon, it will simplify the deployment process for this service.

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

bridgetower_embedder_service
=====================
Port 6006 - Open to 0.0.0.0/0

multimodal_embedding
=========
Port 6000 - Open to 0.0.0.0/0

multimodal_retriever
=========
Port 7000 - Open to 0.0.0.0/0

llava_service
================
Port 8399 - Open to 0.0.0.0/0

lvm
===
Port 9399 - Open to 0.0.0.0/0

chaqna-xeon-backend-server
==========================
Port 8888 - Open to 0.0.0.0/0

chaqna-xeon-ui-server
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
export REDIS_URL="redis://${host_ip}:6379"
export INDEX_NAME="mm-rag-redis"
export LLAVA_SERVER_PORT=8399
export LVM_ENDPOINT="http://${host_ip}:8399/v1/lvm"
export EMBEDDING_MODEL_ID="BridgeTower/bridgetower-large-itm-mlm-itc"
export WHISPER_MODEL="base"


export BACKEND_SERVICE_ENDPOINT="http://${host_ip}:8888/v1/chatqna"
export DATAPREP_SERVICE_ENDPOINT="http://${host_ip}:6007/v1/dataprep"
export DATAPREP_GET_FILE_ENDPOINT="http://${host_ip}:6007/v1/dataprep/get_file"
export DATAPREP_DELETE_FILE_ENDPOINT="http://${host_ip}:6007/v1/dataprep/delete_file"
```

Note: Please replace with `host_ip` with you external IP address, do not use localhost.

## 🚀 Build Docker Images

First of all, you need to build Docker Images locally and install the python package of it.

```bash
git clone https://github.com/opea-project/GenAIComps.git
cd GenAIComps
```

### 1. Build Multimodal-Embedding Image

Build bridgetower_embedder_service docker image

```bash
docker build --no-cache -t opea/bridgetower-embedder:latest --build-arg EMBEDDER_PORT=$EMBEDDER_PORT --build-arg https_proxy=$https_proxy --build-arg http_proxy=$http_proxy -f comps/embeddings/multimodal_embeddings/bridgetower/docker/Dockerfile .
```

Build microservice image

```bash
docker build --no-cache -t opea/multimodal-embedding:latest --build-arg https_proxy=$https_proxy --build-arg http_proxy=$http_proxy -f comps/embeddings/multimodal_embeddings/multimodal_langchain/docker/Dockerfile .

```

### 2. Build Multimodal-Retriever Image

```bash
docker build --no-cache -t opea/multimodal-retriever-redis:latest --build-arg https_proxy=$https_proxy --build-arg http_proxy=$http_proxy -f comps/retrievers/langchain/redis_multimodal/docker/Dockerfile .

```

### 3. Build LVM Image

Build LLaVA server image

```bash
docker build --no-cache -t opea/llava:latest --build-arg https_proxy=$https_proxy --build-arg http_proxy=$http_proxy -f comps/lvms/llava/Dockerfile .
```

Build LVM microservice image

```bash
docker build --no-cache -t opea/lvm:latest --build-arg https_proxy=$https_proxy --build-arg http_proxy=$http_proxy -f comps/lvms/Dockerfile .
```

### 4. Build Multimodal-Data-Prep Image

```bash
docker build --no-cache -t opea/multimodal-dataprep-redis:latest --build-arg https_proxy=$https_proxy --build-arg http_proxy=$http_proxy -f comps/dataprep/redis/multimodal_langchain/docker/Dockerfile .
```