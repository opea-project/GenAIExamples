# Build Mega Service of Translation on Xeon

This document outlines the deployment process for a Translation application utilizing the [GenAIComps](https://github.com/opea-project/GenAIComps.git) microservice pipeline on Intel Xeon server. The steps include Docker image creation, container deployment via Docker Compose, and service execution to integrate microservices such as `llm`. We will publish the Docker images to Docker Hub soon, it will simplify the deployment process for this service.

## 🚀 Apply Xeon Server on AWS

To apply a Xeon server on AWS, start by creating an AWS account if you don't have one already. Then, head to the [EC2 Console](https://console.aws.amazon.com/ec2/v2/home) to begin the process. Within the EC2 service, select the Amazon EC2 M7i or M7i-flex instance type to leverage 4th Generation Intel Xeon Scalable processors. These instances are optimized for high-performance computing and demanding workloads.

For detailed information about these instance types, you can refer to this [link](https://aws.amazon.com/ec2/instance-types/m7i/). Once you've chosen the appropriate instance type, proceed with configuring your instance settings, including network configurations, security groups, and storage options.

After launching your instance, you can connect to it using SSH (for Linux instances) or Remote Desktop Protocol (RDP) (for Windows instances). From there, you'll have full access to your Xeon server, allowing you to install, configure, and manage your applications as needed.

## 🚀 Prepare Docker Images

For Docker Images, you have two options to prepare them.

1. Pull the docker images from docker hub.

   - More stable to use.
   - Will be automatically downloaded when using docker compose command.

2. Build the docker images from source.

   - Contain the latest new features.

   - Need to be manually build.

If you choose to pull docker images form docker hub, skip this section and go to [Start Microservices](#start-microservices) part directly.

Follow the instructions below to build the docker images from source.

### 1. Build LLM Image

```bash
git clone https://github.com/opea-project/GenAIComps.git
cd GenAIComps
docker build -t opea/llm-textgen:latest --build-arg https_proxy=$https_proxy --build-arg http_proxy=$http_proxy -f comps/llms/src/text-generation/Dockerfile .
```

### 2. Build MegaService Docker Image

To construct the Mega Service, we utilize the [GenAIComps](https://github.com/opea-project/GenAIComps.git) microservice pipeline within the `translation.py` Python script. Build MegaService Docker image via below command:

```bash
git clone https://github.com/opea-project/GenAIExamples
cd GenAIExamples/Translation/
docker build -t opea/translation:latest --build-arg https_proxy=$https_proxy --build-arg http_proxy=$http_proxy -f Dockerfile .
```

### 3. Build UI Docker Image

Build frontend Docker image via below command:

```bash
cd GenAIExamples/Translation/ui
docker build -t opea/translation-ui:latest --build-arg https_proxy=$https_proxy --build-arg http_proxy=$http_proxy -f docker/Dockerfile .
```

### 4. Build Nginx Docker Image

```bash
cd GenAIComps
docker build -t opea/nginx:latest --build-arg https_proxy=$https_proxy --build-arg http_proxy=$http_proxy -f comps/third_parties/nginx/src/Dockerfile .
```

Then run the command `docker images`, you will have the following Docker Images:

1. `opea/llm-textgen:latest`
2. `opea/translation:latest`
3. `opea/translation-ui:latest`
4. `opea/nginx:latest`

## 🚀 Start Microservices

### Required Models

By default, the LLM model is set to a default value as listed below:

| Service | Model             |
| ------- | ----------------- |
| LLM     | haoranxu/ALMA-13B |

Change the `LLM_MODEL_ID` below for your needs.

For users in China who are unable to download models directly from Huggingface, you can use [ModelScope](https://www.modelscope.cn/models) or a Huggingface mirror to download models. The vLLM/TGI can load the models either online or offline as described below:

1. Online

   ```bash
   export HF_TOKEN=${your_hf_token}
   export HF_ENDPOINT="https://hf-mirror.com"
   model_name="haoranxu/ALMA-13B"
   # Start vLLM LLM Service
   docker run -p 8008:80 -v ./data:/root/.cache/huggingface/hub --name vllm-service -e HF_ENDPOINT=$HF_ENDPOINT -e http_proxy=$http_proxy -e https_proxy=$https_proxy --shm-size 128g opea/vllm:latest --model $model_name --host 0.0.0.0 --port 80
   # Start TGI LLM Service
   docker run -p 8008:80 -v ./data:/data --name tgi-service -e HF_ENDPOINT=$HF_ENDPOINT -e http_proxy=$http_proxy -e https_proxy=$https_proxy --shm-size 1g ghcr.io/huggingface/text-generation-inference:2.4.0-intel-cpu --model-id $model_name
   ```

2. Offline

   - Search your model name in ModelScope. For example, check [this page](https://www.modelscope.cn/models/rubraAI/Mistral-7B-Instruct-v0.3/files) for model `haoranxu/ALMA-13B`.

   - Click on `Download this model` button, and choose one way to download the model to your local path `/path/to/model`.

   - Run the following command to start the LLM service.

     ```bash
     export HF_TOKEN=${your_hf_token}
     export model_path="/path/to/model"
     # Start vLLM LLM Service
     docker run -p 8008:80 -v $model_path:/root/.cache/huggingface/hub --name vllm-service --shm-size 128g opea/vllm:latest --model /root/.cache/huggingface/hub --host 0.0.0.0 --port 80
     # Start TGI LLM Service
     docker run -p 8008:80 -v $model_path:/data --name tgi-service --shm-size 1g ghcr.io/huggingface/text-generation-inference:2.4.0-intel-cpu --model-id /data
     ```

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

   If you want to start a code translation service (instead of text translation), change the `LLM_MODEL_ID` to "mistralai/Mistral-7B-Instruct-v0.3" in `set_env.sh`.

   ```bash
   cd ../../../
   source set_env.sh
   ```

### Start Microservice Docker Containers

```bash
cd GenAIExamples/Translation/docker_compose/intel/cpu/xeon
```

If use vLLM as the LLM serving backend.

```bash
docker compose -f compose.yaml up -d
```

If use TGI as the LLM serving backend.

```bash
docker compose -f compose_tgi.yaml up -d
```

> Note: The docker images will be automatically downloaded from `docker hub`:

```bash
docker pull opea/llm-textgen:latest
docker pull opea/translation:latest
docker pull opea/translation-ui:latest
docker pull opea/nginx:latest
```

### Validate Microservices

1. LLM backend Service

   In the first startup, this service will take more time to download, load and warm up the model. After it's finished, the service will be ready.

   Try the command below to check whether the LLM serving is ready.

   ```bash
   # vLLM service
   docker logs translation-xeon-vllm-service 2>&1 | grep complete
   # If the service is ready, you will get the response like below.
   INFO:     Application startup complete.
   ```

   ```bash
   # TGI service
   docker logs translation-xeon-tgi-service | grep Connected
   # If the service is ready, you will get the response like below.
   2024-09-03T02:47:53.402023Z  INFO text_generation_router::server: router/src/server.rs:2311: Connected
   ```

   Then try the `cURL` command below to validate services.

   ```bash
   # either vLLM or TGI service
   # text translation
   curl http://${host_ip}:8008/generate \
     -X POST \
     -d '{"inputs":"What is Deep Learning?","parameters":{"max_new_tokens":17, "do_sample": true}}' \
     -H 'Content-Type: application/json'
   # code translation
   curl http://${host_ip}:8008/v1/chat/completions \
     -X POST \
     -d '{"inputs":"    ### System: Please translate the following Golang codes into  Python codes.    ### Original codes:    '\'''\'''\''Golang    \npackage main\n\nimport \"fmt\"\nfunc main() {\n    fmt.Println(\"Hello, World!\");\n    '\'''\'''\''    ### Translated codes:","parameters":{"max_new_tokens":17, "do_sample": true}}' \
     -H 'Content-Type: application/json'
   ```

2. LLM Microservice

   ```bash
   # text translation
   curl http://${host_ip}:9000/v1/chat/completions \
     -X POST \
     -d '{"query":"Translate this from Chinese to English:\nChinese: 我爱机器翻译。\nEnglish:"}' \
     -H 'Content-Type: application/json'
   # code translation
   curl http://${host_ip}:9000/v1/chat/completions\
     -X POST \
     -d '{"query":"    ### System: Please translate the following Golang codes into  Python codes.    ### Original codes:    '\'''\'''\''Golang    \npackage main\n\nimport \"fmt\"\nfunc main() {\n    fmt.Println(\"Hello, World!\");\n    '\'''\'''\''    ### Translated codes:"}' \
     -H 'Content-Type: application/json'
   ```

3. MegaService

   ```bash
   # text translation
   curl http://${host_ip}:8888/v1/translation -H "Content-Type: application/json" -d '{
        "language_from": "Chinese","language_to": "English","source_language": "我爱机器翻译。","translate_type":"text"}'
   # code translation
   curl http://${host_ip}:8888/v1/translation \
       -H "Content-Type: application/json" \
       -d '{"language_from": "Golang","language_to": "Python","source_code": "package main\n\nimport \"fmt\"\nfunc main() {\n    fmt.Println(\"Hello, World!\");\n}","translate_type":"code"}'
   ```

4. Nginx Service

   ```bash
   # text translation
   curl http://${host_ip}:${NGINX_PORT}/v1/translation \
       -H "Content-Type: application/json" \
       -d '{"language_from": "Chinese","language_to": "English","source_language": "我爱机器翻译。","translate_type":"text"}'
   # code translation
   curl http://${host_ip}:${NGINX_PORT}/v1/translation \
       -H "Content-Type: application/json" \
       -d '{"language_from": "Golang","language_to": "Python","source_code": "package main\n\nimport \"fmt\"\nfunc main() {\n    fmt.Println(\"Hello, World!\");\n}","translate_type":"code"}'
   ```

Following the validation of all aforementioned microservices, we are now prepared to construct a mega-service.

## 🚀 Launch the UI

### Launch with origin port

Open this URL `http://{host_ip}:5173` in your browser to access the frontend.

![project-screenshot](../../../../assets/img/trans_ui_init.png)
![project-screenshot](../../../../assets/img/trans_ui_select.png)

### Launch with Nginx

If you want to launch the UI using Nginx, open this URL: `http://{host_ip}:{NGINX_PORT}` in your browser to access the frontend.

![image](https://github.com/intel-ai-tce/GenAIExamples/assets/21761437/71214938-819c-4979-89cb-c03d937cd7b5)

![image](https://github.com/intel-ai-tce/GenAIExamples/assets/21761437/be543e96-ddcd-4ee0-9f2c-4e99fee77e37)
