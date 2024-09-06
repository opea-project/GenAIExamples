# Deploy Instruction Tuning Service on Xeon

This document outlines the deployment process for a Instruction Tuning Service utilizing the [GenAIComps](https://github.com/opea-project/GenAIComps.git) microservice on Intel Xeon server. The steps include Docker image creation, container deployment. We will publish the Docker images to Docker Hub, it will simplify the deployment process for this service.

## 🚀 Build Docker Images

First of all, you need to build Docker Images locally. This step can be ignored after the Docker images published to Docker hub.

### 1. Source Code install GenAIComps

```bash
git clone https://github.com/opea-project/GenAIComps.git
cd GenAIComps
```

### 2. Build Docker Image

Build docker image with below command:

```bash
export HF_TOKEN=${your_huggingface_token}
docker build -t opea/finetuning:latest --build-arg https_proxy=$https_proxy --build-arg http_proxy=$http_proxy --build-arg HF_TOKEN=$HF_TOKEN -f comps/finetuning/docker/Dockerfile_cpu .
```

### 3. Run Docker with CLI

Start docker container with below command:

```bash
docker run -d --name="finetuning-server" -p 8005:8005 --runtime=runc --ipc=host -e http_proxy=$http_proxy -e https_proxy=$https_proxy opea/finetuning:latest
```
