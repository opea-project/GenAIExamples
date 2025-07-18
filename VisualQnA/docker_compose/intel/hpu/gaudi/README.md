# Deploying VisualQnA on Intel® Gaudi® Processors

This document outlines the deployment process for a VisualQnA application utilizing the [GenAIComps](https://github.com/opea-project/GenAIComps.git) microservice pipeline on Intel Gaudi server. The steps include Docker image creation, container deployment via Docker Compose, and service execution to integrate microservices such as llm. We will publish the Docker images to Docker Hub, it will simplify the deployment process for this service.

## Table of Contents

1. [VisualQnA Quick Start Deployment](#visualqna-quick-start-deployment)
2. [Validate Microservices](#validate-microservices)
3. [Launch the UI](#launch-the-UI)

## VisualQnA Quick Start Deployment

This section describes how to quickly deploy and test the VisualQnA service manually on an Intel® Xeon® processor. The basic steps are:

1. [Build Docker Images](#build-docker-images)
2. [Setup Environment Variables](#setup-environment-variables)
3. [Deploy the Services Using Docker Compose](#deploy-the-services-using-docker-compose)

### Build Docker Images

First of all, you need to build Docker Images locally. This step can be ignored after the Docker images published to Docker hub.

Please refer the table below to build different microservices from source:

| Microservice  | Deployment Guide                                                                                             |
| ------------- | ------------------------------------------------------------------------------------------------------------ |
| MegaService   | [Build MegaService Docker Image](../../../../README_miscellaneous.md#build-megaservice-docker-image)         |
| LVM and NGINX | [Build LVM and NGINX Docker Images](../../../../README_miscellaneous.md#build-lvm-and-nginx-docker-images)   |
| vLLM or TGI   | [Build vLLM or Pull TGI Gaudi Image](../../../../README_miscellaneous.md#build-vllm-or-pull-tgi-gaudi-image) |
| UI            | [Basic UI build guide](../../../../README_miscellaneous.md#build-ui-docker-image)                            |

Then run the command `docker images`, you will have the following 5 Docker Images:

1. `opea/vllm-gaudi:latest`
2. `ghcr.io/huggingface/tgi-gaudi:2.3.1` (Optional)
3. `opea/lvm:latest`
4. `opea/visualqna:latest`
5. `opea/visualqna-ui:latest`
6. `opea/nginx`

### Setup Environment Variables

Since the `compose.yaml` will consume some environment variables, you need to setup them in advance as below.

```bash
source set_env.sh
```

Note: Please replace with `host_ip` with you external IP address, do not use localhost.

### Deploy the Services Using Docker Compose

```bash
cd GenAIExamples/VisualQnA/docker_compose/intel/hpu/gaudi/
```

```bash
docker compose -f compose.yaml up -d
# if use TGI as the LLM serving backend
docker compose -f compose_tgi.yaml up -d
```

> **_NOTE:_** Users need at least one Gaudi cards to run the VisualQnA successfully.

After running docker compose, check if all the containers launched via docker compose have started.

## Validate MicroServices

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

## Launch the UI

To access the frontend, open the following URL in your browser: http://{host_ip}:5173. By default, the UI runs on port 5173 internally. If you prefer to use a different host port to access the frontend, you can modify the port mapping in the `compose.yaml` file as shown below:

```yaml
  visualqna-gaudi-ui-server:
    image: opea/visualqna-ui:latest
    ...
    ports:
      - "80:5173"
```
