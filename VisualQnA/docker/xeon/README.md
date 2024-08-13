# Build Mega Service of VisualQnA on Xeon

This document outlines the deployment process for a VisualQnA application utilizing the [GenAIComps](https://github.com/opea-project/GenAIComps.git) microservice pipeline on Intel Xeon server. The steps include Docker image creation, container deployment via Docker Compose, and service execution to integrate microservices such as `llm`. We will publish the Docker images to Docker Hub soon, it will simplify the deployment process for this service.

## 🚀 Apply Xeon Server on AWS

To apply a Xeon server on AWS, start by creating an AWS account if you don't have one already. Then, head to the [EC2 Console](https://console.aws.amazon.com/ec2/v2/home) to begin the process. Within the EC2 service, select the Amazon EC2 M7i or M7i-flex instance type to leverage the power of 4th Generation Intel Xeon Scalable processors. These instances are optimized for high-performance computing and demanding workloads.

For detailed information about these instance types, you can refer to this [link](https://aws.amazon.com/ec2/instance-types/m7i/). Once you've chosen the appropriate instance type, proceed with configuring your instance settings, including network configurations, security groups, and storage options.

After launching your instance, you can connect to it using SSH (for Linux instances) or Remote Desktop Protocol (RDP) (for Windows instances). From there, you'll have full access to your Xeon server, allowing you to install, configure, and manage your applications as needed.

**Certain ports in the EC2 instance need to opened up in the security group, for the microservices to work with the curl commands**

> See one example below. Please open up these ports in the EC2 instance based on the IP addresses you want to allow

```
llava-tgi-service
===========
Port 8399 - Open to 0.0.0.0/0

llm
===
Port 9399 - Open to 0.0.0.0/0

visualqna-xeon-backend-server
==========================
Port 8888 - Open to 0.0.0.0/0

visualqna-xeon-ui-server
=====================
Port 5173 - Open to 0.0.0.0/0
```

## 🚀 Build Docker Images

First of all, you need to build Docker Images locally and install the python package of it.

```bash
git clone https://github.com/opea-project/GenAIComps.git
cd GenAIComps
```

### 1. Build LVM Image

```bash
docker build --no-cache -t opea/lvm-tgi:latest --build-arg https_proxy=$https_proxy --build-arg http_proxy=$http_proxy -f comps/lvms/Dockerfile_tgi .
```

### 2. Build MegaService Docker Image

To construct the Mega Service, we utilize the [GenAIComps](https://github.com/opea-project/GenAIComps.git) microservice pipeline within the `visualqna.py` Python script. Build MegaService Docker image via below command:

```bash
git clone https://github.com/opea-project/GenAIExamples.git
cd GenAIExamples/VisualQnA/docker
docker build --no-cache -t opea/visualqna:latest --build-arg https_proxy=$https_proxy --build-arg http_proxy=$http_proxy -f Dockerfile .
cd ../../..
```

### 3. Build UI Docker Image

Build frontend Docker image via below command:

```bash
cd GenAIExamples/VisualQnA/docker/ui/
docker build --no-cache -t opea/visualqna-ui:latest --build-arg https_proxy=$https_proxy --build-arg http_proxy=$http_proxy -f ./docker/Dockerfile .
cd ../../../..
```

### 4. Build TGI Xeon Image

Since TGI official image has not supported llava-next for CPU, we'll need to build it based on Dockerfile_intel.

```bash
git clone https://github.com/huggingface/text-generation-inference
cd text-generation-inference/
docker build -t opea/llava-tgi-xeon:latest --build-arg PLATFORM=cpu --build-arg http_proxy=${http_proxy} --build-arg https_proxy=${https_proxy} . -f Dockerfile_intel
cd ../
```

Then run the command `docker images`, you will have the following 4 Docker Images:

1. `opea/llava-tgi-xeon:latest`
2. `opea/lvm-tgi:latest`
3. `opea/visualqna:latest`
4. `opea/visualqna-ui:latest`

## 🚀 Start Microservices

### Setup Environment Variables

Since the `compose.yaml` will consume some environment variables, you need to setup them in advance as below.

**Export the value of the public IP address of your Xeon server to the `host_ip` environment variable**

> Change the External_Public_IP below with the actual IPV4 value

```
export host_ip="External_Public_IP"
```

**Append the value of the public IP address to the no_proxy list**

```
export your_no_proxy=${your_no_proxy},"External_Public_IP"
```

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

Note: Please replace with `host_ip` with you external IP address, do not use localhost.

### Start all the services Docker Containers

> Before running the docker compose command, you need to be in the folder that has the docker compose yaml file

```bash
cd GenAIExamples/VisualQnA/docker/xeon/
```

```bash
docker compose -f compose.yaml up -d
```

### Validate Microservices

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
