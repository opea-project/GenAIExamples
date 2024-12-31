# Image-to-Video Microservice

Image-to-Video is a task that generate video conditioning on the provided image(s). This microservice supports image-to-video task by using Stable Video Diffusion (SVD) model.

# 🚀1. Start Microservice with Python (Option 1)

## 1.1 Install Requirements

```bash
pip install -r src/requirements.txt
```

## 1.2 Start Image-to-Video Microservice

```bash
cd ..
# Start the OPEA Microservice
python opea_image2video_microservice.py
```

# 🚀2. Start Microservice with Docker (Option 2)

## 2.1 Build Images

Build Image-to-Video Service image on Xeon with below command:

```bash
cd ../..
docker build -t opea/image2video:latest --build-arg https_proxy=$https_proxy --build-arg http_proxy=$http_proxy -f comps/image2video/src/Dockerfile .
```

Build Image-to-Video Service image on Gaudi with below command:

```bash
cd ../..
docker build -t opea/image2video-gaudi:latest --build-arg https_proxy=$https_proxy --build-arg http_proxy=$http_proxy -f comps/image2video/src/Dockerfile.intel_hpu .
```

## 2.2 Start Image-to-Video Service

Start SVD server on Xeon with below command:

```bash
docker run --ipc=host -p 9369:9369 -e http_proxy=$http_proxy -e https_proxy=$https_proxy opea/image2video:latest
```

Start SVD server on Gaudi with below command:

```bash
docker run -p 9369:9369 --runtime=habana -e HABANA_VISIBLE_DEVICES=all -e OMPI_MCA_btl_vader_single_copy_mechanism=none --cap-add=sys_nice --ipc=host -e http_proxy=$http_proxy -e https_proxy=$https_proxy opea/image2video-gaudi:latest
```

## 2.3 Test

```bash
http_proxy="" curl http://localhost:9369/v1/image2video -XPOST -d '{"images_path":[{"image_path":"https://huggingface.co/datasets/huggingface/documentation-images/resolve/main/diffusers/svd/rocket.png"}]}' -H 'Content-Type: application/json'
```
