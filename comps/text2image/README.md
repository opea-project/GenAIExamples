# Text-to-Image Microservice

Text-to-Image is a task that generate image conditioning on the provided text. This microservice supports text-to-image task by using Stable Diffusion (SD) model.

# 🚀1. Start Microservice with Python (Option 1)

## 1.1 Install Requirements

```bash
pip install -r requirements.txt
```

## 1.2 Start Text-to-Image Microservice

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

Start the OPEA Microservice:

```bash
python text2image.py --bf16 --model_name_or_path $MODEL --token $HF_TOKEN
```

# 🚀2. Start Microservice with Docker (Option 2)

## 2.1 Build Images

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

### 2.1.1 Text-to-Image Service Image on Xeon

Build text-to-image service image on Xeon with below command:

```bash
cd ../..
docker build -t opea/text2image:latest --build-arg https_proxy=$https_proxy --build-arg http_proxy=$http_proxy -f comps/text2image/Dockerfile .
```

### 2.1.2 Text-to-Image Service Image on Gaudi

Build text-to-image service image on Gaudi with below command:

```bash
cd ../..
docker build -t opea/text2image-gaudi:latest --build-arg https_proxy=$https_proxy --build-arg http_proxy=$http_proxy -f comps/text2image/Dockerfile.intel_hpu .
```

## 2.2 Start Text-to-Image Service

### 2.2.1 Start Text-to-Image Service on Xeon

Start text-to-image service on Xeon with below command:

```bash
docker run --ipc=host -p 9379:9379 -e http_proxy=$http_proxy -e https_proxy=$https_proxy -e HF_TOKEN=$HF_TOKEN -e MODEL=$MODEL opea/text2image:latest
```

### 2.2.2 Start Text-to-Image Service on Gaudi

Start text-to-image service on Gaudi with below command:

```bash
docker run -p 9379:9379 --runtime=habana -e HABANA_VISIBLE_DEVICES=all -e OMPI_MCA_btl_vader_single_copy_mechanism=none --cap-add=sys_nice --ipc=host -e http_proxy=$http_proxy -e https_proxy=$https_proxy -e HF_TOKEN=$HF_TOKEN -e MODEL=$MODEL opea/text2image-gaudi:latest
```

# 3 Test Text-to-Image Service

```bash
http_proxy="" curl http://localhost:9379/v1/text2image -XPOST -d '{"prompt":"An astronaut riding a green horse", "num_images_per_prompt":1}' -H 'Content-Type: application/json'
```
