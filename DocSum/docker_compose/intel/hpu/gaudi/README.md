# Build MegaService of Document Summarization on Gaudi

This document outlines the deployment process for a Document Summarization application utilizing the [GenAIComps](https://github.com/opea-project/GenAIComps.git) microservice pipeline on Intel Gaudi server. The steps include Docker image creation, container deployment via Docker Compose, and service execution to integrate microservices such as llm. We will publish the Docker images to Docker Hub, which will simplify the deployment process for this service.

## 🚀 Build Docker Images

First of all, you need to build Docker Images locally. This step can be ignored once the Docker images are published to Docker hub.

### 1. Pull TGI Gaudi Image

As TGI Gaudi has been officially published as a Docker image, we simply need to pull it:

```bash
docker pull ghcr.io/huggingface/tgi-gaudi:2.0.5
```

### 2. Build LLM Image

```bash
git clone https://github.com/opea-project/GenAIComps.git
cd GenAIComps
docker build -t opea/llm-docsum-tgi:latest --build-arg https_proxy=$https_proxy --build-arg http_proxy=$http_proxy -f comps/llms/summarization/tgi/langchain/Dockerfile .
```

### 3. Build MegaService Docker Image

To construct the Mega Service, we utilize the [GenAIComps](https://github.com/opea-project/GenAIComps.git) microservice pipeline within the `docsum.py` Python script. Build the MegaService Docker image using the command below:

```bash
git clone https://github.com/opea-project/GenAIExamples
cd GenAIExamples/DocSum/docker
docker build -t opea/docsum:latest --build-arg https_proxy=$https_proxy --build-arg http_proxy=$http_proxy -f Dockerfile .
```

### 4. Build UI Docker Image

Construct the frontend Docker image using the command below:

```bash
cd GenAIExamples/DocSum/
docker build -t opea/docsum-ui:latest --build-arg https_proxy=$https_proxy --build-arg http_proxy=$http_proxy -f ./docker/Dockerfile .
```

### 5. Build React UI Docker Image

Build the frontend Docker image via below command:

```bash
cd GenAIExamples/DocSum/ui
export BACKEND_SERVICE_ENDPOINT="http://${host_ip}:8888/v1/docsum"
docker build -t opea/docsum-react-ui:latest --build-arg BACKEND_SERVICE_ENDPOINT=$BACKEND_SERVICE_ENDPOINT -f ./docker/Dockerfile.react .
```

Then run the command `docker images`, you will have the following Docker Images:

1. `ghcr.io/huggingface/tgi-gaudi:2.0.5`
2. `opea/llm-docsum-tgi:latest`
3. `opea/docsum:latest`
4. `opea/docsum-ui:latest`
5. `opea/docsum-react-ui:latest`

## 🚀 Start Microservices and MegaService

### Required Models

We set default model as "Intel/neural-chat-7b-v3-3", change "LLM_MODEL_ID" in following setting if you want to use other models.
If use gated models, you also need to provide [huggingface token](https://huggingface.co/docs/hub/security-tokens) to "HUGGINGFACEHUB_API_TOKEN" environment variable.

### Setup Environment Variables

Since the `compose.yaml` will consume some environment variables, you need to setup them in advance as below.

```bash
export no_proxy=${your_no_proxy}
export http_proxy=${your_http_proxy}
export https_proxy=${your_http_proxy}
export LLM_MODEL_ID="Intel/neural-chat-7b-v3-3"
export TGI_LLM_ENDPOINT="http://${host_ip}:8008"
export HUGGINGFACEHUB_API_TOKEN=${your_hf_api_token}
export MEGA_SERVICE_HOST_IP=${host_ip}
export LLM_SERVICE_HOST_IP=${host_ip}
export BACKEND_SERVICE_ENDPOINT="http://${host_ip}:8888/v1/docsum"
```

Note: Please replace with `host_ip` with your external IP address, do not use localhost.

### Start Microservice Docker Containers

```bash
cd GenAIExamples/DocSum/docker_compose/intel/hpu/gaudi
docker compose up -d
```

### Validate Microservices

1. TGI Service

   ```bash
   curl http://${host_ip}:8008/generate \
     -X POST \
     -d '{"inputs":"What is Deep Learning?","parameters":{"max_new_tokens":64, "do_sample": true}}' \
     -H 'Content-Type: application/json'
   ```

2. LLM Microservice

   ```bash
   curl http://${host_ip}:9000/v1/chat/docsum \
     -X POST \
     -d '{"query":"Text Embeddings Inference (TEI) is a toolkit for deploying and serving open source text embeddings and sequence classification models. TEI enables high-performance extraction for the most popular models, including FlagEmbedding, Ember, GTE and E5."}' \
     -H 'Content-Type: application/json'
   ```

3. MegaService

   ```bash
   curl http://${host_ip}:8888/v1/docsum -H "Content-Type: application/json" -d '{
        "messages": "Text Embeddings Inference (TEI) is a toolkit for deploying and serving open source text embeddings and sequence classification models. TEI enables high-performance extraction for the most popular models, including FlagEmbedding, Ember, GTE and E5."
        }'
   ```

## 🚀 Launch the Svelte UI

Open this URL `http://{host_ip}:5173` in your browser to access the frontend.

![project-screenshot](https://github.com/intel-ai-tce/GenAIExamples/assets/21761437/93b1ed4b-4b76-4875-927e-cc7818b4825b)

Here is an example for summarizing a article.

![image](https://github.com/intel-ai-tce/GenAIExamples/assets/21761437/67ecb2ec-408d-4e81-b124-6ded6b833f55)

## 🚀 Launch the React UI (Optional)

To access the React-based frontend, modify the UI service in the `compose.yaml` file. Replace `docsum-xeon-ui-server` service with the `docsum-xeon-react-ui-server` service as per the config below:

```yaml
docsum-gaudi-react-ui-server:
  image: ${REGISTRY:-opea}/docsum-react-ui:${TAG:-latest}
  container_name: docsum-gaudi-react-ui-server
  depends_on:
    - docsum-gaudi-backend-server
  ports:
    - "5174:80"
  environment:
    - no_proxy=${no_proxy}
    - https_proxy=${https_proxy}
    - http_proxy=${http_proxy}
    - DOC_BASE_URL=${BACKEND_SERVICE_ENDPOINT}
```

Open this URL `http://{host_ip}:5175` in your browser to access the frontend.

![project-screenshot](../../../../assets/img/docsum-ui-react.png)
