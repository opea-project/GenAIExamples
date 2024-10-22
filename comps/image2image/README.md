# Image-to-Image Microservice

Image-to-Image is a task that generate image conditioning on the provided image and text. This microservice supports image-to-image task by using Stable Diffusion (SD) model.

# 🚀1. Start Microservice with Python (Option 1)

## 1.1 Install Requirements

```bash
pip install -r requirements.txt
```

## 1.2 Start Image-to-Image Microservice

Select Stable Diffusion (SD) model and assign its name to a environment variable as below:

```bash
# SDXL
export MODEL=stabilityai/stable-diffusion-xl-refiner-1.0
```

Set huggingface token:

```bash
export HF_TOKEN=<your huggingface token>
```

Start the OPEA Microservice:

```bash
python image2image.py --bf16 --model_name_or_path $MODEL --token $HF_TOKEN
```

# 🚀2. Start Microservice with Docker (Option 2)

## 2.1 Build Images

Select Stable Diffusion (SD) model and assign its name to a environment variable as below:

```bash
# SDXL
export MODEL=stabilityai/stable-diffusion-xl-refiner-1.0
```

### 2.1.1 Image-to-Image Service Image on Xeon

Build image-to-image service image on Xeon with below command:

```bash
cd ../..
docker build -t opea/image2image:latest --build-arg https_proxy=$https_proxy --build-arg http_proxy=$http_proxy -f comps/image2image/Dockerfile .
```

### 2.1.2 Image-to-Image Service Image on Gaudi

Build image-to-image service image on Gaudi with below command:

```bash
cd ../..
docker build -t opea/image2image-gaudi:latest --build-arg https_proxy=$https_proxy --build-arg http_proxy=$http_proxy -f comps/image2image/Dockerfile.intel_hpu .
```

## 2.2 Start Image-to-Image Service

### 2.2.1 Start Image-to-Image Service on Xeon

Start image-to-image service on Xeon with below command:

```bash
docker run --ipc=host -p 9389:9389 -e http_proxy=$http_proxy -e https_proxy=$https_proxy -e HF_TOKEN=$HF_TOKEN -e MODEL=$MODEL opea/image2image:latest
```

### 2.2.2 Start Image-to-Image Service on Gaudi

Start image-to-image service on Gaudi with below command:

```bash
docker run -p 9389:9389 --runtime=habana -e HABANA_VISIBLE_DEVICES=all -e OMPI_MCA_btl_vader_single_copy_mechanism=none --cap-add=sys_nice --ipc=host -e http_proxy=$http_proxy -e https_proxy=$https_proxy -e HF_TOKEN=$HF_TOKEN -e MODEL=$MODEL opea/image2image-gaudi:latest
```

# 3 Test Image-to-Image Service

```bash
http_proxy="" curl http://localhost:9389/v1/image2image -XPOST -d '{"image": "https://huggingface.co/datasets/patrickvonplaten/images/resolve/main/aa_xl/000000009.png", "prompt":"a photo of an astronaut riding a horse on mars", "num_images_per_prompt":1}' -H 'Content-Type: application/json'
```
