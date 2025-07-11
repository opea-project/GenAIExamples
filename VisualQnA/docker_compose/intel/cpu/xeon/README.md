# Deploying VisualQnA on Intel® Xeon® Processors

This document outlines the deployment process for a VisualQnA application utilizing the [GenAIComps](https://github.com/opea-project/GenAIComps.git) microservice pipeline on Intel Xeon server. The steps include Docker image creation, container deployment via Docker Compose, and service execution to integrate microservices such as `llm`. We will publish the Docker images to Docker Hub soon, it will simplify the deployment process for this service.

## Table of Contents

1. [VisualQnA Quick Start Deployment](#visualqna-quick-start-deployment)
2. [Validate Microservices](#validate-microservices)
3. [Launch the UI](#launch-the-UI)

## VisualQnA Quick Start Deployment

This section describes how to quickly deploy and test the VisualQnA service manually on an Intel® Xeon® processor. The basic steps are:

1. [Apply Xeon Server on AWS](#apply-xeon-server-on-aws)
2. [Build Docker Images](#build-docker-images)
3. [Setup Environment Variables](#setup-environment-variables)
4. [Deploy the Services Using Docker Compose](#deploy-the-services-using-docker-compose)

### Apply Xeon Server on AWS

To apply a Xeon server on AWS, start by creating an AWS account if you don't have one already. Then, head to the [EC2 Console](https://console.aws.amazon.com/ec2/v2/home) to begin the process. Within the EC2 service, select the Amazon EC2 M7i or M7i-flex instance type to leverage 4th Generation Intel Xeon Scalable processors. These instances are optimized for high-performance computing and demanding workloads.

For detailed information about these instance types, you can refer to this [link](https://aws.amazon.com/ec2/instance-types/m7i/). Once you've chosen the appropriate instance type, proceed with configuring your instance settings, including network configurations, security groups, and storage options.

After launching your instance, you can connect to it using SSH (for Linux instances) or Remote Desktop Protocol (RDP) (for Windows instances). From there, you'll have full access to your Xeon server, allowing you to install, configure, and manage your applications as needed.

### Build Docker Images

First of all, you need to build Docker Images locally and install the python package of it.

Please refer to the table below to build different microservices from source:

| Microservice  | Deployment Guide                                                                              |
| ------------- | --------------------------------------------------------------------------------------------- |
| MegaService   | [MegaService build guide](../../../../README_miscellaneous.md#build-megaservice-docker-image) |
| LVM and NGINX | [vLLM build guide](../../../../README_miscellaneous.md#build-lvm-and-nginx-docker-images)     |
| vLLM or TGI   | [Pull vLLM/TGI Xeon Image](../../../../README_miscellaneous.md#pull-vLLM/TGI-xeon-image)      |
| UI            | [Basic UI build guide](../../../../README_miscellaneous.md#build-ui-docker-image)             |

Then run the command `docker images`, you will have the following Docker Images:

1. `opea/vllm:latest`
2. `ghcr.io/huggingface/text-generation-inference:2.4.0-intel-cpu` (Optional)
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

> Before running the docker compose command, you need to be in the folder that has the docker compose yaml file

```bash
cd GenAIExamples/VisualQnA/docker_compose/intel/cpu/xeon
```

```bash
docker compose -f compose.yaml up -d
# if use TGI as the LLM serving backend
docker compose -f compose_tgi.yaml up -d
```

After running docker compose, check if all the containers launched via docker compose have started.

## Validate Microservices

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
