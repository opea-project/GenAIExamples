# LVM Microservice

Visual Question and Answering is one of the multimodal tasks empowered by LVMs (Large Visual Models). This microservice supports visual Q&A by using Llama Vision as the base large visual model. It accepts two inputs: a prompt and an image. It outputs the answer to the prompt about the image.

## 🚀 Start Microservice with Docker

### Build Images

#### Build Llama Vision Model

```bash
cd ../../../
docker build -t opea/lvm-llama-vision:latest --build-arg https_proxy=$https_proxy --build-arg http_proxy=$http_proxy -f comps/lvms/llama-vision/Dockerfile .
```

#### Build Llama Vision Model with deepspeed

If you need to build the image for 90B models, use the following command:

```bash
docker build -t opea/lvm-llama-vision-tp:latest --build-arg https_proxy=$https_proxy --build-arg http_proxy=$http_proxy -f comps/lvms/llama-vision/Dockerfile_tp .
```

#### Build Llama Vision Guard Model

```bash
cd ../../../
docker build -t opea/lvm-llama-vision-guard:latest --build-arg https_proxy=$https_proxy --build-arg http_proxy=$http_proxy -f comps/lvms/llama-vision/Dockerfile_guard .
```

### Start Llama LVM Service

#### Start Llama Vision Model Service

```bash
export HUGGINGFACEHUB_API_TOKEN=${your_hf_token}
docker run -it -p 9399:9399 --ipc=host -e http_proxy=$http_proxy -e https_proxy=$https_proxy -e LLAMA_VISION_MODEL_ID="meta-llama/Llama-3.2-11B-Vision-Instruct" -e HUGGINGFACEHUB_API_TOKEN=$HUGGINGFACEHUB_API_TOKEN --runtime=habana -e HABANA_VISIBLE_DEVICES=all -e OMPI_MCA_btl_vader_single_copy_mechanism=none --cap-add=sys_nice --ipc=host opea/lvm-llama-vision:latest
```

#### Start Llama Vision Model Service with deepspeed

If you need to run the 90B models, use the following command:

```bash
export HUGGINGFACEHUB_API_TOKEN=${your_hf_token}
export WORLD_SIZE=4
export no_proxy=localhosst,127.0.0.1
docker run -it -p 9599:9599 --ipc=host -e http_proxy=$http_proxy -e https_proxy=$https_proxy -e no_proxy=$no_proxy -e MODEL_ID="meta-llama/Llama-3.2-90B-Vision-Instruct" -e HUGGINGFACEHUB_API_TOKEN=$HUGGINGFACEHUB_API_TOKEN -e WORLD_SIZE=$WORLD_SIZE --runtime=habana -e HABANA_VISIBLE_DEVICES=all -e OMPI_MCA_btl_vader_single_copy_mechanism=none --cap-add=sys_nice opea/lvm-llama-vision-tp:latest
```

#### Start Llama Vision Guard Model Service

```bash
export HUGGINGFACEHUB_API_TOKEN=${your_hf_token}
docker run -it -p 9499:9499 --ipc=host -e http_proxy=$http_proxy -e https_proxy=$https_proxy -e LLAMA_VISION_MODEL_ID="meta-llama/Llama-Guard-3-11B-Vision" -e HUGGINGFACEHUB_API_TOKEN=$HUGGINGFACEHUB_API_TOKEN --runtime=habana -e HABANA_VISIBLE_DEVICES=all -e OMPI_MCA_btl_vader_single_copy_mechanism=none --cap-add=sys_nice --ipc=host opea/lvm-llama-vision-guard:latest
```

### Test

```bash
# Use curl

# curl Llama Vision 11B Model Service
http_proxy="" curl http://localhost:9399/v1/lvm -XPOST -d '{"image": "iVBORw0KGgoAAAANSUhEUgAAAAoAAAAKCAYAAACNMs+9AAAAFUlEQVR42mP8/5+hnoEIwDiqkL4KAcT9GO0U4BxoAAAAAElFTkSuQmCC", "prompt":"What is this?", "max_new_tokens": 128}' -H 'Content-Type: application/json'

# curl Llama Vision Guard Model Service
http_proxy="" curl http://localhost:9499/v1/lvm -XPOST -d '{"image": "iVBORw0KGgoAAAANSUhEUgAAAAoAAAAKCAYAAACNMs+9AAAAFUlEQVR42mP8/5+hnoEIwDiqkL4KAcT9GO0U4BxoAAAAAElFTkSuQmCC", "prompt":"What is this?", "max_new_tokens": 128}' -H 'Content-Type: application/json'

# curl Llama Vision 90B Model Service
http_proxy="" curl http://localhost:9599/v1/lvm -XPOST -d '{"image": "iVBORw0KGgoAAAANSUhEUgAAAAoAAAAKCAYAAACNMs+9AAAAFUlEQVR42mP8/5+hnoEIwDiqkL4KAcT9GO0U4BxoAAAAAElFTkSuQmCC", "prompt":"What is this?", "max_new_tokens": 128}' -H 'Content-Type: application/json'

```
