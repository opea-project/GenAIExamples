# Deploy Rerank Model Finetuning Service on Gaudi

This document outlines the deployment process for a rerank model finetuning service utilizing the [GenAIComps](https://github.com/opea-project/GenAIComps.git) microservice on Intel Xeon server. The steps include Docker image creation, container deployment. We will publish the Docker images to Docker Hub, it will simplify the deployment process for this service.

## 🚀 Build Docker Images

First of all, you need to build Docker Images locally. This step can be ignored after the Docker images published to Docker hub.

### 1. Build Docker Image

Build docker image with below command:

```bash
git clone https://github.com/opea-project/GenAIComps.git
cd GenAIComps
docker build -t opea/finetuning-gaudi:latest --build-arg https_proxy=$https_proxy --build-arg http_proxy=$http_proxy -f comps/finetuning/Dockerfile.intel_hpu .
```

### 2. Run Docker with CLI

Start docker container with below command:

```bash
export HF_TOKEN=${your_huggingface_token}
docker run --runtime=habana -e HABANA_VISIBLE_DEVICES=all -p 8015:8015 -e OMPI_MCA_btl_vader_single_copy_mechanism=none --cap-add=sys_nice --net=host --ipc=host -e https_proxy=$https_proxy -e http_proxy=$http_proxy -e no_proxy=$no_proxy -e HF_TOKEN=$HF_TOKEN opea/finetuning-gaudi:latest
```
