# Build Mega Service of CodeTrans on Gaudi

This document outlines the deployment process for a CodeTrans application utilizing the [GenAIComps](https://github.com/opea-project/GenAIComps.git) microservice pipeline on Intel Gaudi server. The steps include Docker image creation, container deployment via Docker Compose, and service execution using microservices `llm`. We will publish the Docker images to Docker Hub soon, it will simplify the deployment process for this service.

## 🚀 Build Docker Images

First of all, you need to build Docker Images locally and install the python package of it. This step can be ignored after the Docker images published to Docker hub.

### 1. Source Code install GenAIComps

```bash
git clone https://github.com/opea-project/GenAIComps.git
cd GenAIComps
```

### 2. Build the LLM Docker Image

```bash
docker build -t opea/llm-tgi:latest --no-cache --build-arg https_proxy=$https_proxy --build-arg http_proxy=$http_proxy -f comps/llms/text-generation/tgi/Dockerfile .
```

### 3. Build MegaService Docker Image

```bash
git clone https://github.com/opea-project/GenAIExamples.git
cd GenAIExamples/CodeTrans/docker
docker build -t opea/codetrans:latest --build-arg https_proxy=$https_proxy --build-arg http_proxy=$http_proxy -f Dockerfile .
```

### 4. Build UI Docker Image

```bash
cd GenAIExamples/CodeTrans/docker/ui
docker build -t opea/codetrans-ui:latest --build-arg https_proxy=$https_proxy --build-arg http_proxy=$http_proxy -f ./docker/Dockerfile .
```

### 5. Build Nginx Docker Image

```bash
cd GenAIComps
docker build -t opea/nginx:latest --build-arg https_proxy=$https_proxy --build-arg http_proxy=$http_proxy -f comps/nginx/docker/Dockerfile .
```

Then run the command `docker images`, you will have the following Docker Images:

- `opea/llm-tgi:latest`
- `opea/codetrans:latest`
- `opea/codetrans-ui:latest`
- `opea/nginx:latest`

## 🚀 Start Microservices

### Required Models

By default, the LLM model is set to a default value as listed below:

| Service | Model                         |
| ------- | ----------------------------- |
| LLM     | HuggingFaceH4/mistral-7b-grok |

Change the `LLM_MODEL_ID` below for your needs.

### Setup Environment Variables

1. Set the required environment variables:

   ```bash
   # Example: host_ip="192.168.1.1"
   export host_ip="External_Public_IP"
   # Example: no_proxy="localhost, 127.0.0.1, 192.168.1.1"
   export no_proxy="Your_No_Proxy"
   export HUGGINGFACEHUB_API_TOKEN="Your_Huggingface_API_Token"
   # Example: NGINX_PORT=80
   export NGINX_PORT=${your_nginx_port}
   ```

2. If you are in a proxy environment, also set the proxy-related environment variables:

   ```bash
   export http_proxy="Your_HTTP_Proxy"
   export https_proxy="Your_HTTPs_Proxy"
   ```

3. Set up other environment variables:

   ```bash
   source ../set_env.sh
   ```

### Start Microservice Docker Containers

```bash
cd GenAIExamples/CodeTrans/docker/gaudi
docker compose up -d
```

### Validate Microservices

1. TGI Service

   ```bash
   curl http://${host_ip}:8008/generate \
     -X POST \
     -d '{"inputs":"    ### System: Please translate the following Golang codes into  Python codes.    ### Original codes:    '\'''\'''\''Golang    \npackage main\n\nimport \"fmt\"\nfunc main() {\n    fmt.Println(\"Hello, World!\");\n    '\'''\'''\''    ### Translated codes:","parameters":{"max_new_tokens":17, "do_sample": true}}' \
     -H 'Content-Type: application/json'
   ```

2. LLM Microservice

   ```bash
   curl http://${host_ip}:9000/v1/chat/completions\
     -X POST \
     -d '{"text":"    ### System: Please translate the following Golang codes into  Python codes.    ### Original codes:    '\'''\'''\''Golang    \npackage main\n\nimport \"fmt\"\nfunc main() {\n    fmt.Println(\"Hello, World!\");\n    '\'''\'''\''    ### Translated codes:"}' \
     -H 'Content-Type: application/json'
   ```

3. MegaService

   ```bash
   curl http://${host_ip}:7777/v1/codetrans \
       -H "Content-Type: application/json" \
       -d '{"language_from": "Golang","language_to": "Python","source_code": "package main\n\nimport \"fmt\"\nfunc main() {\n    fmt.Println(\"Hello, World!\");\n}"}'
   ```

4. Nginx Service

   ```bash
   curl http://${host_ip}:${NGINX_PORT}/v1/codetrans \
       -H "Content-Type: application/json" \
       -d '{"language_from": "Golang","language_to": "Python","source_code": "package main\n\nimport \"fmt\"\nfunc main() {\n    fmt.Println(\"Hello, World!\");\n}"}'
   ```

## 🚀 Launch the UI

### Launch with origin port

Open this URL `http://{host_ip}:5173` in your browser to access the frontend.

### Launch with Nginx

If you want to launch the UI using Nginx, open this URL: `http://{host_ip}:{NGINX_PORT}` in your browser to access the frontend.

![image](https://github.com/intel-ai-tce/GenAIExamples/assets/21761437/71214938-819c-4979-89cb-c03d937cd7b5)

Here is an example for summarizing a article.

![image](https://github.com/intel-ai-tce/GenAIExamples/assets/21761437/be543e96-ddcd-4ee0-9f2c-4e99fee77e37)
