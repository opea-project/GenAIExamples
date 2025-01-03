# Deploy Text-to-Image Service on Gaudi

This document outlines the deployment process for a text-to-image service utilizing the [GenAIComps](https://github.com/opea-project/GenAIComps.git) microservice on Intel Xeon server. The steps include Docker image creation, container deployment. We will publish the Docker images to Docker Hub, it will simplify the deployment process for this service.

## 🚀 Build Docker Images

First of all, you need to build Docker Images locally. This step can be ignored after the Docker images published to Docker hub.

### 1. Build Docker Image

Build text-to-image service image on Gaudi with below command:

```bash
git clone https://github.com/opea-project/GenAIComps.git
cd GenAIComps
docker build -t opea/text2image-gaudi:latest --build-arg https_proxy=$https_proxy --build-arg http_proxy=$http_proxy -f comps/text2image/src/Dockerfile.intel_hpu .
```

### 2. Run Docker with CLI

Select Stable Diffusion (SD) model and assign its name to a environment variable as below:

```bash
# SD1.5
export MODEL=stable-diffusion-v1-5/stable-diffusion-v1-5
# SD2.1
export MODEL=stabilityai/stable-diffusion-2-1
# SDXL
export MODEL=stabilityai/stable-diffusion-xl-base-1.0
# SD3
export MODEL=stabilityai/stable-diffusion-3-medium-diffusers
```

Set huggingface token:

```bash
export HF_TOKEN=<your huggingface token>
```

Start text-to-image service on Gaudi with below command:

```bash
docker run -p 9379:9379 --runtime=habana -e HABANA_VISIBLE_DEVICES=all -e OMPI_MCA_btl_vader_single_copy_mechanism=none --cap-add=sys_nice --ipc=host -e http_proxy=$http_proxy -e https_proxy=$https_proxy -e HF_TOKEN=$HF_TOKEN -e MODEL=$MODEL opea/text2image-gaudi:latest
```
