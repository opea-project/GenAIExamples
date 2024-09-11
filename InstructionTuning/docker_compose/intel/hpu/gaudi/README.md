# Deploy Instruction Tuning Service on Gaudi

This document outlines the deployment process for a Instruction Tuning Service utilizing the [GenAIComps](https://github.com/opea-project/GenAIComps.git) microservice on Intel Gaudi server. The steps include Docker image creation, container deployment. We will publish the Docker images to Docker Hub, it will simplify the deployment process for this service.

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
docker build -t opea/finetuning-gaudi:latest --build-arg https_proxy=$https_proxy --build-arg http_proxy=$http_proxy -f comps/finetuning/Dockerfile.intel_hpu .
```

### 3. Run Docker with CLI

Start docker container with below command:

```bash
export HF_TOKEN=${your_huggingface_token}
docker run --runtime=habana -e HABANA_VISIBLE_DEVICES=all -p 8005:8005 -e OMPI_MCA_btl_vader_single_copy_mechanism=none --cap-add=sys_nice --net=host --ipc=host -e https_proxy=$https_proxy -e http_proxy=$http_proxy -e no_proxy=$no_proxy -e HF_TOKEN=$HF_TOKEN opea/finetuning-gaudi:latest
```
