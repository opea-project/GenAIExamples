# LVM Microservice

Visual Question and Answering is one of the multimodal tasks empowered by LVMs (Large Visual Models). This microservice supports visual Q&A by using LLaVA as the base large visual model. It accepts two inputs: a prompt and an image. It outputs the answer to the prompt about the image.

## 🚀1. Start Microservice with Python (Option 1)

### 1.1 Install Requirements

```bash
pip install -r requirements.txt
```

### 1.2 Start LLaVA Service/Test

- Xeon CPU

```bash
# Start LLaVA service
cd dependency/
nohup python llava_server.py --device=cpu &
# Wait until the server is up
# Test
python check_llava_server.py
```

- Gaudi2 HPU

```bash
pip install optimum[habana]
```

```bash
cd dependency/
# Start LLaVA service
nohup python llava_server.py &
# Test
python check_llava_server.py
```

### 1.3 Start Image To Text Service/Test

```bash
cd ..
# Start the OPEA Microservice
python lvm.py
# Test
python check_lvm.py
```

## 🚀2. Start Microservice with Docker (Option 2)

### 2.1 Build Images

#### 2.1.1 LLaVA Server Image

- Xeon CPU

```bash
cd ../../../
docker build -t opea/lvm-llava:latest --build-arg https_proxy=$https_proxy --build-arg http_proxy=$http_proxy -f comps/lvms/llava/dependency/Dockerfile .
```

- Gaudi2 HPU

```bash
cd ../../../
docker build -t opea/lvm-llava:latest --build-arg https_proxy=$https_proxy --build-arg http_proxy=$http_proxy -f comps/lvms/llava/dependency/Dockerfile.intel_hpu .
```

#### 2.1.2 LVM Service Image

```bash
cd ../../../
docker build -t opea/lvm-llava-svc:latest --build-arg https_proxy=$https_proxy --build-arg http_proxy=$http_proxy -f comps/lvms/llava/Dockerfile .
```

### 2.2 Start LLaVA and LVM Service

#### 2.2.1 Start LLaVA server

- Xeon

```bash
docker run -p 8399:8399 -e http_proxy=$http_proxy --ipc=host -e https_proxy=$https_proxy opea/lvm-llava:latest
```

- Gaudi2 HPU

```bash
docker run -p 8399:8399 --runtime=habana -e HABANA_VISIBLE_DEVICES=all -e OMPI_MCA_btl_vader_single_copy_mechanism=none --cap-add=sys_nice --ipc=host -e http_proxy=$http_proxy -e https_proxy=$https_proxy opea/lvm-llava:latest
```

#### 2.2.2 Start LVM service

```bash
ip_address=$(hostname -I | awk '{print $1}')

docker run -p 9399:9399 --ipc=host -e http_proxy=$http_proxy -e https_proxy=$https_proxy -e LVM_ENDPOINT=http://$ip_address:8399 opea/lvm-llava-svc:latest
```

#### 2.2.3 Test

```bash
# Use curl/python

# curl with an image and a prompt
http_proxy="" curl http://localhost:9399/v1/lvm -XPOST -d '{"image": "iVBORw0KGgoAAAANSUhEUgAAAAoAAAAKCAYAAACNMs+9AAAAFUlEQVR42mP8/5+hnoEIwDiqkL4KAcT9GO0U4BxoAAAAAElFTkSuQmCC", "prompt":"What is this?"}' -H 'Content-Type: application/json'

# curl with a prompt only (no image)
http_proxy="" curl http://localhost:9399/v1/lvm -XPOST -d '{"image": "", "prompt":"What is deep learning?"}' -H 'Content-Type: application/json'

# python
python check_lvm.py
```
