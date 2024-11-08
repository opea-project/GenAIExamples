# Build Mega Service of Document Summarization on Intel Xeon Processor

This document outlines the deployment process for a Document Summarization application utilizing the [GenAIComps](https://github.com/opea-project/GenAIComps.git) microservice pipeline on an Intel Xeon server. The steps include Docker image creation, container deployment via Docker Compose, and service execution to integrate microservices such as `llm`. We will publish the Docker images to Docker Hub soon, which will simplify the deployment process for this service.

## 🚀 Apply Intel Xeon Server on AWS

To apply a Intel Xeon server on AWS, start by creating an AWS account if you don't have one already. Then, head to the [EC2 Console](https://console.aws.amazon.com/ec2/v2/home) to begin the process. Within the EC2 service, select the Amazon EC2 M7i or M7i-flex instance type to leverage 4th Generation Intel Xeon Scalable processors. These instances are optimized for high-performance computing and demanding workloads.

For detailed information about these instance types, you can refer to this [link](https://aws.amazon.com/ec2/instance-types/m7i/). Once you've chosen the appropriate instance type, proceed with configuring your instance settings, including network configurations, security groups, and storage options.

After launching your instance, you can connect to it using SSH (for Linux instances) or Remote Desktop Protocol (RDP) (for Windows instances). From there, you'll have full access to your Xeon server, allowing you to install, configure, and manage your applications as needed.

## 🚀 Build Docker Images

### 1. Build MicroService Docker Image

First of all, you need to build Docker Images locally and install the python package of it.

```bash
git clone https://github.com/opea-project/GenAIComps.git
cd GenAIComps
```

#### Whisper Service

The Whisper Service converts audio files to text. Follow these steps to build and run the service:

```bash
docker build -t opea/whisper:latest --build-arg https_proxy=$https_proxy --build-arg http_proxy=$http_proxy -f comps/asr/whisper/dependency/Dockerfile .
```

#### A2T Service

The A2T Service is another service for converting audio to text. Follow these steps to build and run the service:

```bash
docker build -t opea/a2t:latest --build-arg https_proxy=$https_proxy --build-arg http_proxy=$http_proxy -f comps/dataprep/multimedia2text/audio2text/Dockerfile .
```

#### Video to Audio Service

The Video to Audio Service extracts audio from video files. Follow these steps to build and run the service:

```bash
docker build -t opea/v2a:latest --build-arg https_proxy=$https_proxy --build-arg http_proxy=$http_proxy -f comps/dataprep/multimedia2text/video2audio/Dockerfile .
```

#### Multimedia2Text Service

The Multimedia2Text Service transforms multimedia data to text data. Follow these steps to build and run the service:

```bash
docker build -t opea/multimedia2text:latest --build-arg https_proxy=$https_proxy --build-arg http_proxy=$http_proxy -f comps/dataprep/multimedia2text/Dockerfile .
```

### 2. Build MegaService Docker Image

To construct the Mega Service, we utilize the [GenAIComps](https://github.com/opea-project/GenAIComps.git) microservice pipeline within the `docsum.py` Python script. Build the MegaService Docker image via below command:

```bash
git clone https://github.com/opea-project/GenAIExamples
cd GenAIExamples/DocSum/
docker build -t opea/docsum:latest --build-arg https_proxy=$https_proxy --build-arg http_proxy=$http_proxy -f Dockerfile .
```

### 3. Build UI Docker Image

Build the frontend Docker image via below command:

```bash
cd GenAIExamples/DocSum/ui/gradio
docker build -t opea/docsum-ui:latest --build-arg https_proxy=$https_proxy --build-arg http_proxy=$http_proxy -f Dockerfile .
```

## 🚀 Start Microservices and MegaService

### Required Models

We set default model as "Intel/neural-chat-7b-v3-3", change "LLM_MODEL_ID" in following Environment Variables setting if you want to use other models.
If use gated models, you also need to provide [huggingface token](https://huggingface.co/docs/hub/security-tokens) to "HUGGINGFACEHUB_API_TOKEN" environment variable.

### Setup Environment Variable

To set up environment variables for deploying Document Summarization services, follow these steps:

1. Set the required environment variables:

   ```bash
   # Example: host_ip="192.168.1.1"
   export host_ip="External_Public_IP"
   # Example: no_proxy="localhost, 127.0.0.1, 192.168.1.1"
   export no_proxy="Your_No_Proxy"
   export HUGGINGFACEHUB_API_TOKEN="Your_Huggingface_API_Token"
   ```

2. If you are in a proxy environment, also set the proxy-related environment variables:

   ```bash
   export http_proxy="Your_HTTP_Proxy"
   export https_proxy="Your_HTTPs_Proxy"
   ```

3. Set up other environment variables:

   ```bash
   source GenAIExamples/DocSum/docker_compose/set_env.sh
   ```

### Start Microservice Docker Containers

```bash
cd GenAIExamples/DocSum/docker_compose/intel/cpu/xeon
docker compose -f compose.yaml up -d
```

You will have the following Docker Images:

1. `opea/docsum-ui:latest`
2. `opea/docsum:latest`
3. `opea/llm-docsum-tgi:latest`
4. `opea/whisper:latest`
5. `opea/a2t:latest`
6. `opea/multimedia2text:latest`
7. `opea/v2a:latest`

### Validate Microservices

1. TGI Service

   ```bash
   curl http://${host_ip}:8008/generate \
     -X POST \
     -d '{"inputs":"What is Deep Learning?","parameters":{"max_new_tokens":17, "do_sample": true}}' \
     -H 'Content-Type: application/json'
   ```

2. LLM Microservice

   ```bash
   curl http://${host_ip}:9000/v1/chat/docsum \
     -X POST \
     -d '{"query":"Text Embeddings Inference (TEI) is a toolkit for deploying and serving open source text embeddings and sequence classification models. TEI enables high-performance extraction for the most popular models, including FlagEmbedding, Ember, GTE and E5."}' \
     -H 'Content-Type: application/json'
   ```

3. Whisper Microservice

   ```bash
    curl http://${host_ip}:7066/v1/asr \
        -X POST \
        -d '{"audio":"UklGRigAAABXQVZFZm10IBIAAAABAAEARKwAAIhYAQACABAAAABkYXRhAgAAAAEA"}' \
        -H 'Content-Type: application/json'
   ```

   Expected output:

   ```bash
     {"asr_result":"you"}
   ```

4. Audio2Text Microservice

   ```bash
    curl http://${host_ip}:9099/v1/audio/transcriptions \
        -X POST \
        -d '{"byte_str":"UklGRigAAABXQVZFZm10IBIAAAABAAEARKwAAIhYAQACABAAAABkYXRhAgAAAAEA"}' \
        -H 'Content-Type: application/json'
   ```

   Expected output:

   ```bash
     {"downstream_black_list":[],"id":"--> this will be different id number for each run <--","query":"you"}
   ```

5. Multimedia2text Microservice

   ```bash
    curl http://${host_ip}:7079/v1/multimedia2text \
        -X POST \
        -d '{"audio":"UklGRigAAABXQVZFZm10IBIAAAABAAEARKwAAIhYAQACABAAAABkYXRhAgAAAAEA"}' \
        -H 'Content-Type: application/json'
   ```

   Expected output:

   ```bash
     {"downstream_black_list":[],"id":"--> this will be different id number for each run <--","query":"you"}
   ```

6. MegaService

   ```bash
   curl -X POST http://${host_ip}:8888/v1/docsum \
        -H "Content-Type: application/json" \
        -d '{"type": "text", "messages": "Text Embeddings Inference (TEI) is a toolkit for deploying and serving open source text embeddings and sequence classification models. TEI enables high-performance extraction for the most popular models, including FlagEmbedding, Ember, GTE and E5."}'
   ```

> More detailed tests can be found here `cd GenAIExamples/DocSum/test`

## 🚀 Launch the UI

Open this URL `http://{host_ip}:5173` in your browser to access the Gradio based frontend.

### Gradio UI

![project-screenshot](../../../../assets/img/docSum_ui_text.png)
