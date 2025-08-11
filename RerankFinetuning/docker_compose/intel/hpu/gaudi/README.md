# Deploy Rerank Model Finetuning Service on Gaudi

## Table of Contents

- [Overview](#overview)
- [Build Docker Image](#build-docker-image)
- [Run Docker with CLI](#run-docker-with-cli)

## Overview

This document outlines the deployment process for a rerank model finetuning service utilizing the [GenAIComps](https://github.com/opea-project/GenAIComps.git) microservice on Intel Gaudi. The steps include Docker image creation, container deployment. We will publish the Docker images to Docker Hub, it will simplify the deployment process for this service.

## Build Docker Image

First of all, you need to build Docker Images locally. This step can be ignored after the Docker images published to Docker hub. Build docker image with below command:

```bash
git clone https://github.com/opea-project/GenAIComps.git
cd GenAIComps
docker build -t opea/finetuning-gaudi:latest \
    --build-arg https_proxy=$https_proxy \
    --build-arg http_proxy=$http_proxy \
    -f comps/finetuning/src/Dockerfile.intel_hpu .
```

## Run Docker with CLI

Start docker container with below command:

```bash
export HF_TOKEN=${your_huggingface_token}
docker run -d --name="finetuning-server-gaudi" \
    --runtime=habana \
    -e HABANA_VISIBLE_DEVICES=all \
    -p 8015:8015 \
    -e OMPI_MCA_btl_vader_single_copy_mechanism=none \
    --cap-add=sys_nice \
    --net=host \
    --ipc=host \
    -e https_proxy=$https_proxy \
    -e http_proxy=$http_proxy \
    -e no_proxy=$no_proxy \
    -e HF_TOKEN=$HF_TOKEN \
    opea/finetuning-gaudi:latest
```
