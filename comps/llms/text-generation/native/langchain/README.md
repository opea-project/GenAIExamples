# LLM Native Microservice

LLM Native microservice uses [optimum-habana](https://github.com/huggingface/optimum-habana) for model initialization and warm-up, focusing solely on large language models (LLMs). It operates without frameworks like TGI/VLLM, using PyTorch directly for inference, and supports only non-streaming formats. This streamlined approach optimizes performance on Habana hardware.

## 🚀1. Start Microservice

If you start an LLM microservice with docker, the `docker_compose_llm.yaml` file will automatically start a Native LLM service with docker.

### 1.1 Setup Environment Variables

In order to start Native LLM service, you need to setup the following environment variables first.

```bash
export LLM_NATIVE_MODEL="Qwen/Qwen2-7B-Instruct"
export HUGGINGFACEHUB_API_TOKEN="your_huggingface_token"
```

### 1.2 Build Docker Image

```bash
cd ../../../../../
docker build -t opea/llm-native:latest --build-arg https_proxy=$https_proxy --build-arg http_proxy=$http_proxy -f comps/llms/text-generation/native/langchain
Dockerfile .
```

To start a docker container, you have two options:

- A. Run Docker with CLI
- B. Run Docker with Docker Compose

You can choose one as needed.

### 1.3 Run Docker with CLI (Option A)

```bash
docker run -d --runtime=habana --name="llm-native-server" -p 9000:9000 -e https_proxy=$https_proxy -e http_proxy=$http_proxy -e TOKENIZERS_PARALLELISM=false -e HABANA_VISIBLE_DEVICES=all -e OMPI_MCA_btl_vader_single_copy_mechanism=none --cap-add=sys_nice --ipc=host -e LLM_NATIVE_MODEL=${LLM_NATIVE_MODEL} opea/llm-native:latest
```

### 1.4 Run Docker with Docker Compose (Option B)

```bash
docker compose -f docker_compose_llm.yaml up -d
```

## 🚀2. Consume LLM Service

### 2.1 Check Service Status

```bash
curl http://${your_ip}:9000/v1/health_check\
  -X GET \
  -H 'Content-Type: application/json'
```

### 2.2 Consume LLM Service

```bash
curl http://${your_ip}:9000/v1/chat/completions\
  -X POST \
  -d '{"query":"What is Deep Learning?"}' \
  -H 'Content-Type: application/json'
```
