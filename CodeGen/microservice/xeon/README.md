# Build Mega Service of CodeGen on Xeon

This document outlines the deployment process for a CodeGen application utilizing the [GenAIComps](https://github.com/opea-project/GenAIComps.git) microservice pipeline on Intel Xeon server. The steps include Docker image creation, container deployment via Docker Compose, and service execution to integrate microservices such as `llm`. We will publish the Docker images to Docker Hub soon, it will simplify the deployment process for this service.

## 🚀 Apply Xeon Server on AWS

To apply a Xeon server on AWS, start by creating an AWS account if you don't have one already. Then, head to the [EC2 Console](https://console.aws.amazon.com/ec2/v2/home) to begin the process. Within the EC2 service, select the Amazon EC2 M7i or M7i-flex instance type to leverage the power of 4th Generation Intel Xeon Scalable processors. These instances are optimized for high-performance computing and demanding workloads.

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
docker build -t opea/gen-ai-comps:llm-tgi-server --build-arg https_proxy=$https_proxy --build-arg http_proxy=$http_proxy -f comps/llms/langchain/docker/Dockerfile .
```

### 2. Build MegaService Docker Image

To construct the Mega Service, we utilize the [GenAIComps](https://github.com/opea-project/GenAIComps.git) microservice pipeline within the `codegen.py` Python script. Build MegaService Docker image via below command:

```bash
git clone https://github.com/opea-project/GenAIExamples
cd GenAIExamples/CodeGen/microservice/xeon/
docker build -t opea/gen-ai-comps:codegen-megaservice-server --build-arg https_proxy=$https_proxy --build-arg http_proxy=$http_proxy -f docker/Dockerfile .
```

### 6. Build UI Docker Image

Build frontend Docker image via below command:

```bash
cd GenAIExamples/CodeGen/ui/
docker build -t opea/gen-ai-comps:codegen-ui-server --build-arg https_proxy=$https_proxy --build-arg http_proxy=$http_proxy -f ./docker/Dockerfile .
```

Then run the command `docker images`, you will have the following four Docker Images:

1. `opea/gen-ai-comps:llm-tgi-server`
2. `opea/gen-ai-comps:codegen-megaservice-server`
3. `opea/gen-ai-comps:codegen-ui-server`

## 🚀 Start Microservices

### Setup Environment Variables

Since the `docker_compose.yaml` will consume some environment variables, you need to setup them in advance as below.

```bash
export http_proxy=${your_http_proxy}
export https_proxy=${your_http_proxy}
export LLM_MODEL_ID="ise-uiuc/Magicoder-S-DS-6.7B"
export TGI_LLM_ENDPOINT="http://${host_ip}:9009"
export HUGGINGFACEHUB_API_TOKEN=${your_hf_api_token}
export MEGA_SERVICE_HOST_IP=${host_ip}
export BACKEND_SERVICE_ENDPOINT="http://${host_ip}:6666/v1/codegen"
```

Note: Please replace with `host_ip` with you external IP address, do not use localhost.

### Start all the services Docker Containers

```bash
docker compose -f docker_compose.yaml up -d
```

### Validate Microservices

1. TGI Service

```bash
curl http://${host_ip}:9009/generate \
  -X POST \
  -d '{"inputs":"Write a function that checks if a year is a leap year in Python.","parameters":{"max_new_tokens":128, "do_sample": true}}' \
  -H 'Content-Type: application/json'
```

2. LLM Microservice

```bash
curl http://${host_ip}:9000/v1/chat/completions\
  -X POST \
  -d '{"query":"Write a function that checks if a year is a leap year in Python.","max_new_tokens":128,"top_k":10,"top_p":0.95,"typical_p":0.95,"temperature":0.01,"repetition_penalty":1.03,"streaming":true}' \
  -H 'Content-Type: application/json'
```

3. MegaService

```bash
curl http://${host_ip}:6666/v1/codegen -H "Content-Type: application/json" -d '{
     "model": "ise-uiuc/Magicoder-S-DS-6.7B",
     "messages": "Write a function that checks if a year is a leap year in Python."
     }'
```

## 🚀 Launch the UI

To access the frontend, open the following URL in your browser: http://{host_ip}:5173. By default, the UI runs on port 5173 internally. If you prefer to use a different host port to access the frontend, you can modify the port mapping in the `docker_compose.yaml` file as shown below:

```yaml
  chaqna-gaudi-ui-server:
    image: opea/gen-ai-comps:codegen-ui-server
    ...
    ports:
      - "80:5173"
```

![project-screenshot](https://imgur.com/d1SmaRb.png)
