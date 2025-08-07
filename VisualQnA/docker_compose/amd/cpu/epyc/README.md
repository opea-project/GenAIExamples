# Build Mega Service of VisualQnA on AMD EPYC™ Processors

This document outlines the deployment process for a VisualQnA application utilizing the [GenAIComps](https://github.com/opea-project/GenAIComps.git) microservice pipeline on AMD EPYC server. The steps include Docker image creation, container deployment via Docker Compose, and service execution to integrate microservices such as `llm`. We will publish the Docker images to Docker Hub soon, it will simplify the deployment process for this service.

## 🚀 Build Docker Images

First of all, you need to build Docker Images locally and install the python package of it.

### 1. Build LVM and NGINX Docker Images

```bash
git clone https://github.com/opea-project/GenAIComps.git
cd GenAIComps
docker build --no-cache -t opea/lvm:latest --build-arg https_proxy=$https_proxy --build-arg http_proxy=$http_proxy -f comps/lvms/src/Dockerfile .
docker build --no-cache -t opea/nginx:latest --build-arg https_proxy=$https_proxy --build-arg http_proxy=$http_proxy -f comps/third_parties/nginx/src/Dockerfile .
```

### 2. Build MegaService Docker Image

To construct the Mega Service, we utilize the [GenAIComps](https://github.com/opea-project/GenAIComps.git) microservice pipeline within the `visualqna.py` Python script. Build MegaService Docker image via below command:

```bash
git clone https://github.com/opea-project/GenAIExamples.git
cd GenAIExamples/VisualQnA
docker build --no-cache -t opea/visualqna:latest --build-arg https_proxy=$https_proxy --build-arg http_proxy=$http_proxy -f Dockerfile .
```

### 3. Build UI Docker Image

Build frontend Docker image via below command:

```bash
cd GenAIExamples/VisualQnA/ui
docker build --no-cache -t opea/visualqna-ui:latest --build-arg https_proxy=$https_proxy --build-arg http_proxy=$http_proxy -f docker/Dockerfile .
```

### 4. Pull vLLM/TGI epyc Image

```bash
# vLLM
docker pull opea/vllm:latest
# TGI (Optional)
docker pull ghcr.io/huggingface/text-generation-inference:2.4.0-intel-cpu
```

Then run the command `docker images`, you will have the following Docker Images:

1. `opea/vllm:latest`
2. `ghcr.io/huggingface/text-generation-inference:2.4.0-intel-cpu` (Optional)
3. `opea/lvm:latest`
4. `opea/visualqna:latest`
5. `opea/visualqna-ui:latest`
6. `opea/nginx`

## 🚀 Start Microservices

### Setup Environment Variables

Since the `compose.yaml` will consume some environment variables, you need to setup them in advance as below.

```bash
source set_env.sh
```

Note: Please replace with `host_ip` with you external IP address, do not use localhost. Also set the `HF_TOKEN`.

### Start all the services Docker Containers

> Before running the docker compose command, you need to be in the folder that has the docker compose yaml file

```bash
cd GenAIExamples/VisualQnA/docker_compose/amd/cpu/epyc
```

```bash
docker compose -f compose.yaml up -d
# if use TGI as the LLM serving backend
docker compose -f compose_tgi.yaml up -d
```

### Validate Microservices

Follow the instructions to validate MicroServices.

> Note: If you see an "Internal Server Error" from the `curl` command, wait a few minutes for the microserver to be ready and then try again.

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
