# Build Mega Service of Document Summarization on Intel Xeon Processor

This document outlines the deployment process for a Document Summarization application utilizing the [GenAIComps](https://github.com/opea-project/GenAIComps.git) microservice pipeline on an Intel Xeon server. The steps include Docker image creation, container deployment via Docker Compose, and service execution to integrate microservices such as `llm`. We will publish the Docker images to Docker Hub soon, which will simplify the deployment process for this service.

## 🚀 Apply Intel Xeon Server on AWS

To apply a Intel Xeon server on AWS, start by creating an AWS account if you don't have one already. Then, head to the [EC2 Console](https://console.aws.amazon.com/ec2/v2/home) to begin the process. Within the EC2 service, select the Amazon EC2 M7i or M7i-flex instance type to leverage the power of 4th Generation Intel Xeon Scalable processors. These instances are optimized for high-performance computing and demanding workloads.

For detailed information about these instance types, you can refer to this [link](https://aws.amazon.com/ec2/instance-types/m7i/). Once you've chosen the appropriate instance type, proceed with configuring your instance settings, including network configurations, security groups, and storage options.

After launching your instance, you can connect to it using SSH (for Linux instances) or Remote Desktop Protocol (RDP) (for Windows instances). From there, you'll have full access to your Xeon server, allowing you to install, configure, and manage your applications as needed.

## 🚀 Build Docker Images

First of all, you need to build Docker Images locally and install the python package of it.

```bash
git clone https://github.com/opea-project/GenAIComps.git
cd GenAIComps
```

### 1. Build LLM Image

```bash
docker build -t opea/llm-docsum-tgi:latest --build-arg https_proxy=$https_proxy --build-arg http_proxy=$http_proxy -f comps/llms/docsum/langchain/docker/Dockerfile .
```

Then run the command `docker images`, you will have the following four Docker Images:

### 2. Build MegaService Docker Image

To construct the Mega Service, we utilize the [GenAIComps](https://github.com/opea-project/GenAIComps.git) microservice pipeline within the `docsum.py` Python script. Build the MegaService Docker image via below command:

```bash
git clone https://github.com/opea-project/GenAIExamples
cd GenAIExamples/DocSum/docker
docker build -t opea/docsum:latest --build-arg https_proxy=$https_proxy --build-arg http_proxy=$http_proxy -f Dockerfile .
```

### 3. Build UI Docker Image

Build the frontend Docker image via below command:

```bash
cd GenAIExamples/DocSum/docker/ui/
docker build -t opea/docsum-ui:latest --build-arg https_proxy=$https_proxy --build-arg http_proxy=$http_proxy -f ./docker/Dockerfile .
```

Then run the command `docker images`, you will have the following Docker Images:

1. `opea/llm-docsum-tgi:latest`
2. `opea/docsum:latest`
3. `opea/docsum-ui:latest`

## 🚀 Start Microservices and MegaService

### Setup Environment Variables

Since the `docker_compose.yaml` will consume some environment variables, you need to setup them in advance as below.

```bash
export http_proxy=${your_http_proxy}
export https_proxy=${your_http_proxy}
export LLM_MODEL_ID="Intel/neural-chat-7b-v3-3"
export TGI_LLM_ENDPOINT="http://${your_ip}:8008"
export HUGGINGFACEHUB_API_TOKEN=${your_hf_api_token}
export MEGA_SERVICE_HOST_IP=${host_ip}
export LLM_SERVICE_HOST_IP=${host_ip}
export BACKEND_SERVICE_ENDPOINT="http://${host_ip}:8888/v1/docsum"
```

Note: Please replace with `host_ip` with your external IP address, do not use localhost.

### Start Microservice Docker Containers

```bash
cd GenAIExamples/DocSum/docker/xeon
docker compose -f docker_compose.yaml up -d
```

### Validate Microservices

1. TGI Service

```bash
curl http://${your_ip}:8008/generate \
  -X POST \
  -d '{"inputs":"What is Deep Learning?","parameters":{"max_new_tokens":17, "do_sample": true}}' \
  -H 'Content-Type: application/json'
```

2. LLM Microservice

```bash
curl http://${your_ip}:9000/v1/chat/docsum \
  -X POST \
  -d '{"query":"Text Embeddings Inference (TEI) is a toolkit for deploying and serving open source text embeddings and sequence classification models. TEI enables high-performance extraction for the most popular models, including FlagEmbedding, Ember, GTE and E5."}' \
  -H 'Content-Type: application/json'
```

3. MegaService

```bash
curl http://${host_ip}:8888/v1/docsum -H "Content-Type: application/json" -d '{
     "messages": "Text Embeddings Inference (TEI) is a toolkit for deploying and serving open source text embeddings and sequence classification models. TEI enables high-performance extraction for the most popular models, including FlagEmbedding, Ember, GTE and E5."
     }'
```

Following the validation of all aforementioned microservices, we are now prepared to construct a mega-service.

## Enable LangSmith to Monitor an Application (Optional)

LangSmith offers tools to debug, evaluate, and monitor language models and intelligent agents. It can be used to assess benchmark data for each microservice. Before launching your services with `docker compose -f docker_compose.yaml up -d`, you need to enable LangSmith tracing by setting the `LANGCHAIN_TRACING_V2` environment variable to true and configuring your LangChain API key.

Here's how you can do it:

1. Install the latest version of LangSmith:

```bash
pip install -U langsmith
```

2. Set the necessary environment variables:

```bash
export LANGCHAIN_TRACING_V2=true
export LANGCHAIN_API_KEY=ls_...
```

## 🚀 Launch the UI

Open this URL `http://{host_ip}:5173` in your browser to access the frontend.

![project-screenshot](https://i.imgur.com/26zMnEr.png)
