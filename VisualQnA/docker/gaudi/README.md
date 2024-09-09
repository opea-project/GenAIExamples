# Build MegaService of VisualQnA on Gaudi

This document outlines the deployment process for a VisualQnA application utilizing the [GenAIComps](https://github.com/opea-project/GenAIComps.git) microservice pipeline on Intel Gaudi server. The steps include Docker image creation, container deployment via Docker Compose, and service execution to integrate microservices such as llm. We will publish the Docker images to Docker Hub, it will simplify the deployment process for this service.

## 🚀 Build Docker Images

First of all, you need to build Docker Images locally. This step can be ignored after the Docker images published to Docker hub.

### 1. Source Code install GenAIComps

```bash
git clone https://github.com/opea-project/GenAIComps.git
cd GenAIComps
```

### 2. Build LLM Image

```bash
docker build --no-cache -t opea/lvm-tgi:latest --build-arg https_proxy=$https_proxy --build-arg http_proxy=$http_proxy -f comps/lvms/Dockerfile_tgi .
```

### 3. Pull TGI Gaudi Image

```bash
docker pull ghcr.io/huggingface/tgi-gaudi:2.0.4
```

### 4. Build MegaService Docker Image

To construct the Mega Service, we utilize the [GenAIComps](https://github.com/opea-project/GenAIComps.git) microservice pipeline within the `visuralqna.py` Python script. Build the MegaService Docker image using the command below:

```bash
git clone https://github.com/opea-project/GenAIExamples.git
cd GenAIExamples/VisualQnA/docker
docker build --no-cache -t opea/visualqna:latest --build-arg https_proxy=$https_proxy --build-arg http_proxy=$http_proxy -f Dockerfile .
cd ../../..
```

### 5. Build UI Docker Image

Build frontend Docker image via below command:

```bash
cd GenAIExamples/VisualQnA/docker/ui/
docker build --no-cache -t opea/visualqna-ui:latest --build-arg https_proxy=$https_proxy --build-arg http_proxy=$http_proxy -f ./docker/Dockerfile .
cd ../../../..
```

Then run the command `docker images`, you will have the following 4 Docker Images:

1. `opea/llava-tgi:latest`
2. `opea/lvm-tgi:latest`
3. `opea/visualqna:latest`
4. `opea/visualqna-ui:latest`

## 🚀 Start MicroServices and MegaService

### Setup Environment Variables

Since the `compose.yaml` will consume some environment variables, you need to setup them in advance as below.

```bash
export no_proxy=${your_no_proxy}
export http_proxy=${your_http_proxy}
export https_proxy=${your_http_proxy}
export LVM_MODEL_ID="llava-hf/llava-v1.6-mistral-7b-hf"
export LVM_ENDPOINT="http://${host_ip}:8399"
export LVM_SERVICE_PORT=9399
export MEGA_SERVICE_HOST_IP=${host_ip}
export LVM_SERVICE_HOST_IP=${host_ip}
export BACKEND_SERVICE_ENDPOINT="http://${host_ip}:8888/v1/visualqna"
```

Note: Please replace with `host_ip` with you external IP address, do **NOT** use localhost.

### Start all the services Docker Containers

```bash
cd GenAIExamples/VisualQnA/docker/gaudi/
```

```bash
docker compose -f compose.yaml up -d
```

> **_NOTE:_** Users need at least one Gaudi cards to run the VisualQnA successfully.

### Validate MicroServices and MegaService

Follow the instructions to validate MicroServices.

1. LLM Microservice

   ```bash
   http_proxy="" curl http://${host_ip}:9399/v1/lvm -XPOST -d '{"image": "iVBORw0KGgoAAAANSUhEUgAAAAoAAAAKCAYAAACNMs+9AAAAFUlEQVR42mP8/5+hnoEIwDiqkL4KAcT9GO0U4BxoAAAAAElFTkSuQmCC", "prompt":"What is this?"}' -H 'Content-Type: application/json'
   ```

2. MegaService

   ```bash
   curl http://${host_ip}:8888/v1/visualqna -H "Content-Type: application/json" -d '{
        "messages": [
         {
           "role": "user",
           "content": [
             {
               "type": "text",
               "text": "What'\''s in this image?"
             },
             {
               "type": "image_url",
               "image_url": {
                 "url": "https://www.ilankelman.org/stopsigns/australia.jpg"
               }
             }
           ]
         }
       ],
       "max_tokens": 300
       }'
   ```

## 🚀 Launch the UI

To access the frontend, open the following URL in your browser: http://{host_ip}:5173. By default, the UI runs on port 5173 internally. If you prefer to use a different host port to access the frontend, you can modify the port mapping in the `compose.yaml` file as shown below:

```yaml
  visualqna-gaudi-ui-server:
    image: opea/visualqna-ui:latest
    ...
    ports:
      - "80:5173"
```
