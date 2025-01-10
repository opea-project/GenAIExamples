# TGI LLM Microservice

[Text Generation Inference](https://github.com/huggingface/text-generation-inference) (TGI) is a toolkit for deploying and serving Large Language Models (LLMs). TGI enables high-performance text generation for the most popular open-source LLMs, including Llama, Falcon, StarCoder, BLOOM, GPT-NeoX, and more.

## 🚀1. Start Microservice with Python (Option 1)

To start the LLM microservice, you need to install python packages first.

### 1.1 Install Requirements

```bash
pip install -r requirements.txt
```

### 1.2 Start 3rd-party TGI Service

Please refer to [3rd-party TGI](../../../third_parties/tgi/deployment/docker_compose/) to start a LLM endpoint and verify.

### 1.3 Start LLM Service with Python Script

```bash
export TGI_LLM_ENDPOINT="http://${your_ip}:8008"
python llm.py
```

## 🚀2. Start Microservice with Docker (Option 2)

If you start an LLM microservice with docker, the `docker_compose_llm.yaml` file will automatically start a TGI/vLLM service with docker.

### 2.1 Setup Environment Variables

In order to start TGI and LLM services, you need to setup the following environment variables first.

```bash
export HF_TOKEN=${your_hf_api_token}
export TGI_LLM_ENDPOINT="http://${your_ip}:8008"
export LLM_MODEL_ID=${your_hf_llm_model}
```

### 2.2 Build Docker Image

```bash
cd ../../../../
docker build -t opea/llm-textgen:latest --build-arg https_proxy=$https_proxy --build-arg http_proxy=$http_proxy -f comps/llms/src/text-generation/Dockerfile .
```

To start a docker container, you have two options:

- A. Run Docker with CLI
- B. Run Docker with Docker Compose

You can choose one as needed.

### 2.3 Run Docker with CLI (Option A)

```bash
docker run -d --name="llm-tgi-server" -p 9000:9000 --ipc=host -e http_proxy=$http_proxy -e https_proxy=$https_proxy -e TGI_LLM_ENDPOINT=$TGI_LLM_ENDPOINT -e HF_TOKEN=$HF_TOKEN opea/llm-textgen:latest
```

### 2.4 Run Docker with Docker Compose (Option B)

```bash
cd comps/llms/deployment/docker_compose/
docker compose -f text-generation_tgi.yaml up -d
```

## 🚀3. Consume LLM Service

### 3.1 Check Service Status

```bash
curl http://${your_ip}:9000/v1/health_check\
  -X GET \
  -H 'Content-Type: application/json'
```

### 3.2 Consume LLM Service

You can set the following model parameters according to your actual needs, such as `max_tokens`, `stream`.

The `stream` parameter determines the format of the data returned by the API. It will return text string with `stream=false`, return text stream flow with `stream=true`.

```bash
# stream mode
curl http://${your_ip}:9000/v1/chat/completions \
    -X POST \
    -d '{"model": "${LLM_MODEL_ID}", "messages": "What is Deep Learning?", "max_tokens":17}' \
    -H 'Content-Type: application/json'

curl http://${your_ip}:9000/v1/chat/completions \
    -X POST \
    -d '{"model": "${LLM_MODEL_ID}", "messages": [{"role": "user", "content": "What is Deep Learning?"}], "max_tokens":17}' \
    -H 'Content-Type: application/json'

#Non-stream mode
curl http://${your_ip}:9000/v1/chat/completions \
    -X POST \
    -d '{"model": "${LLM_MODEL_ID}", "messages": "What is Deep Learning?", "max_tokens":17, "stream":false}' \
    -H 'Content-Type: application/json'
```

For parameters in Chat mode, please refer to [OpenAI API](https://platform.openai.com/docs/api-reference/chat/create)

### 4. Validated Model

| Model                     | TGI |
| ------------------------- | --- |
| Intel/neural-chat-7b-v3-3 | ✓   |
| Llama-2-7b-chat-hf        | ✓   |
| Llama-2-70b-chat-hf       | ✓   |
| Meta-Llama-3-8B-Instruct  | ✓   |
| Meta-Llama-3-70B-Instruct | ✓   |
| Phi-3                     | ✓   |
