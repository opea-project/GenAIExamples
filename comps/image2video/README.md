# Image-to-Video Microservice

Image-to-Video is a task that generate video conditioning on the provided image(s). This microservice supports image-to-video task by using Stable Video Diffusion (SVD) model.

# 🚀1. Start Microservice with Python (Option 1)

## 1.1 Install Requirements

```bash
pip install -r requirements.txt
pip install -r dependency/requirements.txt
```

## 1.2 Start SVD Service

```bash
# Start SVD service
cd dependency/
python svd_server.py
```

## 1.3 Start Image-to-Video Microservice

```bash
cd ..
# Start the OPEA Microservice
python image2video.py
```

# 🚀2. Start Microservice with Docker (Option 2)

## 2.1 Build Images

### 2.1.1 SVD Server Image

Build SVD server image on Xeon with below command:

```bash
cd ../..
docker build -t opea/svd:latest --build-arg https_proxy=$https_proxy --build-arg http_proxy=$http_proxy -f comps/image2video/dependency/Dockerfile .
```

Build SVD server image on Gaudi with below command:

```bash
cd ../..
docker build -t opea/svd-gaudi:latest --build-arg https_proxy=$https_proxy --build-arg http_proxy=$http_proxy -f comps/image2video/dependency/Dockerfile.intel_hpu .
```

### 2.1.2 Image-to-Video Service Image

```bash
docker build -t opea/image2video:latest --build-arg https_proxy=$https_proxy --build-arg http_proxy=$http_proxy -f comps/image2video/Dockerfile .
```

## 2.2 Start SVD and Image-to-Video Service

### 2.2.1 Start SVD server

Start SVD server on Xeon with below command:

```bash
docker run --ipc=host -p 9368:9368 -e http_proxy=$http_proxy -e https_proxy=$https_proxy opea/svd:latest
```

Start SVD server on Gaudi with below command:

```bash
docker run -p 9368:9368 --runtime=habana -e HABANA_VISIBLE_DEVICES=all -e OMPI_MCA_btl_vader_single_copy_mechanism=none --cap-add=sys_nice --ipc=host -e http_proxy=$http_proxy -e https_proxy=$https_proxy opea/svd-gaudi:latest
```

### 2.2.2 Start Image-to-Video service

```bash
ip_address=$(hostname -I | awk '{print $1}')
docker run -p 9369:9369 --ipc=host -e http_proxy=$http_proxy -e https_proxy=$https_proxy -e SVD_ENDPOINT=http://$ip_address:9368 opea/image2video:latest
```

### 2.2.3 Test

```bash
http_proxy="" curl http://localhost:9369/v1/image2video -XPOST -d '{"images_path":[{"image_path":"https://huggingface.co/datasets/huggingface/documentation-images/resolve/main/diffusers/svd/rocket.png"}]}' -H 'Content-Type: application/json'
```
