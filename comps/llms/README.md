# LLM Microservice

This microservice, designed for Language Model Inference (LLM), processes input consisting of a query string and associated reranked documents. It constructs a prompt based on the query and documents, which is then used to perform inference with a large language model. The service delivers the inference results as output.

A prerequisite for using this microservice is that users must have a Text Generation Inference (TGI) service already running. Users need to set the TGI service's endpoint into an environment variable. The microservice utilizes this endpoint to create an LLM object, enabling it to communicate with the TGI service for executing language model operations.

Overall, this microservice offers a streamlined way to integrate large language model inference into applications, requiring minimal setup from the user beyond initiating a TGI service and configuring the necessary environment variables. This allows for the seamless processing of queries and documents to generate intelligent, context-aware responses.

# 🚀Start Microservice with Python

To start the LLM microservice, you need to install python packages first.

## Install Requirements

```bash
pip install -r requirements.txt
```

## Start TGI Service Manually

```bash
export HUGGINGFACEHUB_API_TOKEN=${your_hf_api_token}
docker run -p 8008:80 -v ./data:/data --name tgi_service --shm-size 1g ghcr.io/huggingface/text-generation-inference:1.4 --model-id ${your_hf_llm_model}
```

## Verify the TGI Service

```bash
curl http://${your_ip}:8008/generate \
  -X POST \
  -d '{"inputs":"What is Deep Learning?","parameters":{"max_new_tokens":17, "do_sample": true}}' \
  -H 'Content-Type: application/json'
```

## Start LLM Service with Python Script

```bash
export TGI_LLM_ENDPOINT="http://${your_ip}:8008"
python langchain/llm.py
```

# 🚀Start Microservice with Docker

If you start an LLM microservice with docker, the `docker_compose_llm.yaml` file will automatically start a TGI service with docker.

## Setup Environment Variables

In order to start TGI and LLM services, you need to setup the following environment variables first.

```bash
export HUGGINGFACEHUB_API_TOKEN=${your_hf_api_token}
export TGI_LLM_ENDPOINT="http://${your_ip}:8008"
export LLM_MODEL_ID=${your_hf_llm_model}
```

## Build Docker Image

```bash
cd ../../
docker build -t opea/gen-ai-comps:llm-tgi-server --build-arg https_proxy=$https_proxy --build-arg http_proxy=$http_proxy -f comps/llms/langchain/docker/Dockerfile .
```

## Run Docker with CLI

```bash
docker run -d --name="llm-tgi-server" -p 9000:9000 --ipc=host -e http_proxy=$http_proxy -e https_proxy=$https_proxy -e TGI_LLM_ENDPOINT=$TGI_LLM_ENDPOINT -e HUGGINGFACEHUB_API_TOKEN=$HUGGINGFACEHUB_API_TOKEN opea/gen-ai-comps:llm-tgi-server
```

## Run Docker with Docker Compose

```bash
cd langchain/docker
docker compose -f docker_compose_llm.yaml up -d
```

# 🚀Consume LLM Service

## Check Service Status

```bash
curl http://${your_ip}:9000/v1/health_check\
  -X GET \
  -H 'Content-Type: application/json'
```

## Consume LLM Service

You can set the following model parameters according to your actual needs, such as `max_new_tokens`, `streaming`.

The `streaming` parameter determines the format of the data returned by the API. It will return text string with `streaming=false`, return text streaming flow with `streaming=true`.

```bash
# non-streaming mode
curl http://${your_ip}:9000/v1/chat/completions\
  -X POST \
  -d '{"query":"What is Deep Learning?","max_new_tokens":17,"top_k":10,"top_p":0.95,"typical_p":0.95,"temperature":0.01,"repetition_penalty":1.03,"streaming":false}' \
  -H 'Content-Type: application/json'

# streaming mode
curl http://${your_ip}:9000/v1/chat/completions\
  -X POST \
  -d '{"query":"What is Deep Learning?","max_new_tokens":17,"top_k":10,"top_p":0.95,"typical_p":0.95,"temperature":0.01,"repetition_penalty":1.03,"streaming":true}' \
  -H 'Content-Type: application/json'
```
