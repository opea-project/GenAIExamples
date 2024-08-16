# LLM Microservice

This microservice, designed for Language Model Inference (LLM), processes input consisting of a query string and associated reranked documents. It constructs a prompt based on the query and documents, which is then used to perform inference with a large language model. The service delivers the inference results as output.

A prerequisite for using this microservice is that users must have a LLM text generation service (etc., TGI, vLLM and Ray) already running. Users need to set the LLM service's endpoint into an environment variable. The microservice utilizes this endpoint to create an LLM object, enabling it to communicate with the LLM service for executing language model operations.

Overall, this microservice offers a streamlined way to integrate large language model inference into applications, requiring minimal setup from the user beyond initiating a TGI/vLLM/Ray service and configuring the necessary environment variables. This allows for the seamless processing of queries and documents to generate intelligent, context-aware responses.

# 🚀1. Start Microservice with Python (Option 1)

To start the LLM microservice, you need to install python packages first.

## 1.1 Install Requirements

```bash
pip install -r requirements.txt
```

## 1.2 Start LLM Service

### 1.2.1 Start TGI Service

```bash
export HF_TOKEN=${your_hf_api_token}
export LANGCHAIN_TRACING_V2=true
export LANGCHAIN_API_KEY=${your_langchain_api_key}
export LANGCHAIN_PROJECT="opea/gen-ai-comps:llms"
docker run -p 8008:80 -v ./data:/data --name tgi_service --shm-size 1g ghcr.io/huggingface/text-generation-inference:1.4 --model-id ${your_hf_llm_model}
```

### 1.2.2 Start vLLM Service

```bash
export HUGGINGFACEHUB_API_TOKEN=${your_hf_api_token}
docker run -it --name vllm_service -p 8008:80 -e HF_TOKEN=${HUGGINGFACEHUB_API_TOKEN} -v ./data:/data opea/vllm:cpu /bin/bash -c "cd / && export VLLM_CPU_KVCACHE_SPACE=40 && python3 -m vllm.entrypoints.openai.api_server --model ${your_hf_llm_model} --port 80"
```

## 1.2.3 Start Ray Service

```bash
export HUGGINGFACEHUB_API_TOKEN=${your_hf_api_token}
export TRUST_REMOTE_CODE=True
docker run -it --runtime=habana --name ray_serve_service -e OMPI_MCA_btl_vader_single_copy_mechanism=none --cap-add=sys_nice --ipc=host -p 8008:80 -e HUGGINGFACEHUB_API_TOKEN=$HUGGINGFACEHUB_API_TOKEN -e TRUST_REMOTE_CODE=$TRUST_REMOTE_CODE opea/llm-ray:latest /bin/bash -c "ray start --head && python api_server_openai.py --port_number 80 --model_id_or_path ${your_hf_llm_model} --chat_processor ${your_hf_chatprocessor}"
```

## 1.3 Verify the LLM Service

### 1.3.1 Verify the TGI Service

```bash
curl http://${your_ip}:8008/generate \
  -X POST \
  -d '{"inputs":"What is Deep Learning?","parameters":{"max_new_tokens":17, "do_sample": true}}' \
  -H 'Content-Type: application/json'
```

### 1.3.2 Verify the vLLM Service

```bash
curl http://${your_ip}:8008/v1/completions \
  -H "Content-Type: application/json" \
  -d '{
  "model": ${your_hf_llm_model},
  "prompt": "What is Deep Learning?",
  "max_tokens": 32,
  "temperature": 0
  }'
```

### 1.3.3 Verify the Ray Service

```bash
curl http://${your_ip}:8008/v1/chat/completions \
  -H "Content-Type: application/json" \
  -d '{
  "model": ${your_hf_llm_model},
  "messages": [
        {"role": "assistant", "content": "You are a helpful assistant."},
        {"role": "user", "content": "What is Deep Learning?"},
    ],
  "max_tokens": 32,
  "stream": True
  }'
```

## 1.4 Start LLM Service with Python Script

### 1.4.1 Start the TGI Service

```bash
export TGI_LLM_ENDPOINT="http://${your_ip}:8008"
python text-generation/tgi/llm.py
```

### 1.4.2 Start the vLLM Service

```bash
export vLLM_LLM_ENDPOINT="http://${your_ip}:8008"
python text-generation/vllm/llm.py
```

### 1.4.3 Start the Ray Service

```bash
export RAY_Serve_ENDPOINT="http://${your_ip}:8008"
python text-generation/ray_serve/llm.py
```

# 🚀2. Start Microservice with Docker (Option 2)

If you start an LLM microservice with docker, the `docker_compose_llm.yaml` file will automatically start a TGI/vLLM service with docker.

## 2.1 Setup Environment Variables

In order to start TGI and LLM services, you need to setup the following environment variables first.

```bash
export HF_TOKEN=${your_hf_api_token}
export TGI_LLM_ENDPOINT="http://${your_ip}:8008"
export LLM_MODEL_ID=${your_hf_llm_model}
export LANGCHAIN_TRACING_V2=true
export LANGCHAIN_API_KEY=${your_langchain_api_key}
export LANGCHAIN_PROJECT="opea/llms"
```

In order to start vLLM and LLM services, you need to setup the following environment variables first.

```bash
export HUGGINGFACEHUB_API_TOKEN=${your_hf_api_token}
export vLLM_LLM_ENDPOINT="http://${your_ip}:8008"
export LLM_MODEL_ID=${your_hf_llm_model}
export LANGCHAIN_TRACING_V2=true
export LANGCHAIN_PROJECT="opea/llms"
```

In order to start Ray serve and LLM services, you need to setup the following environment variables first.

```bash
export HUGGINGFACEHUB_API_TOKEN=${your_hf_api_token}
export RAY_Serve_ENDPOINT="http://${your_ip}:8008"
export LLM_MODEL=${your_hf_llm_model}
export LANGCHAIN_TRACING_V2=true
export LANGCHAIN_PROJECT="opea/llms"
export CHAT_PROCESSOR="ChatModelLlama"
```

## 2.2 Build Docker Image

### 2.2.1 TGI

```bash
cd ../../
docker build -t opea/llm-tgi:latest --build-arg https_proxy=$https_proxy --build-arg http_proxy=$http_proxy -f comps/llms/text-generation/tgi/Dockerfile .
```

### 2.2.2 vLLM

Build vllm docker.

```bash
bash build_docker_vllm.sh
```

Build microservice docker.

```bash
cd ../../../../
docker build -t opea/llm-vllm:latest --build-arg https_proxy=$https_proxy --build-arg http_proxy=$http_proxy -f comps/llms/text-generation/vllm/docker/Dockerfile.microservice .
```

### 2.2.3 Ray Serve

Build Ray Serve docker.

```bash
bash build_docker_rayserve.sh
```

Build microservice docker.

```bash
cd ../../../../
docker build -t opea/llm-ray:latest --build-arg https_proxy=$https_proxy --build-arg http_proxy=$http_proxy -f comps/llms/text-generation/ray_serve/docker/Dockerfile.microservice .
```

To start a docker container, you have two options:

- A. Run Docker with CLI
- B. Run Docker with Docker Compose

You can choose one as needed.

## 2.3 Run Docker with CLI (Option A)

### 2.3.1 TGI

```bash
docker run -d --name="llm-tgi-server" -p 9000:9000 --ipc=host -e http_proxy=$http_proxy -e https_proxy=$https_proxy -e TGI_LLM_ENDPOINT=$TGI_LLM_ENDPOINT -e HF_TOKEN=$HF_TOKEN opea/llm-tgi:latest
```

### 2.3.2 vLLM

Start vllm endpoint.

```bash
bash launch_vllm_service.sh
```

Start vllm microservice.

```bash
docker run --name="llm-vllm-server" -p 9000:9000 --ipc=host -e http_proxy=$http_proxy -e https_proxy=$https_proxy -e no_proxy=${no_proxy} -e vLLM_LLM_ENDPOINT=$vLLM_LLM_ENDPOINT -e HUGGINGFACEHUB_API_TOKEN=$HUGGINGFACEHUB_API_TOKEN -e LLM_MODEL_ID=$LLM_MODEL_ID opea/llm-vllm:latest
```

### 2.3.3 Ray Serve

Start Ray Serve endpoint.

```bash
bash launch_ray_service.sh
```

Start Ray Serve microservice.

```bash
docker run -d --name="llm-ray-server" -p 9000:9000 --ipc=host -e http_proxy=$http_proxy -e https_proxy=$https_proxy -e RAY_Serve_ENDPOINT=$RAY_Serve_ENDPOINT -e HUGGINGFACEHUB_API_TOKEN=$HUGGINGFACEHUB_API_TOKEN -e LLM_MODEL=$LLM_MODEL opea/llm-ray:latest
```

## 2.4 Run Docker with Docker Compose (Option B)

### 2.4.1 TGI

```bash
cd text-generation/tgi
docker compose -f docker_compose_llm.yaml up -d
```

### 2.4.2 vLLM

```bash
cd text-generation/vllm
docker compose -f docker_compose_llm.yaml up -d
```

### 2.4.3 Ray Serve

```bash
cd text-genetation/ray_serve
docker compose -f docker_compose_llm.yaml up -d
```

# 🚀3. Consume LLM Service

## 3.1 Check Service Status

```bash
curl http://${your_ip}:9000/v1/health_check\
  -X GET \
  -H 'Content-Type: application/json'
```

## 3.2 Consume LLM Service

You can set the following model parameters according to your actual needs, such as `max_new_tokens`, `streaming`.

The `streaming` parameter determines the format of the data returned by the API. It will return text string with `streaming=false`, return text streaming flow with `streaming=true`.

```bash
# non-streaming mode
curl http://${your_ip}:9000/v1/chat/completions \
  -X POST \
  -d '{"query":"What is Deep Learning?","max_new_tokens":17,"top_k":10,"top_p":0.95,"typical_p":0.95,"temperature":0.01,"repetition_penalty":1.03,"streaming":false}' \
  -H 'Content-Type: application/json'

# streaming mode
curl http://${your_ip}:9000/v1/chat/completions \
  -X POST \
  -d '{"query":"What is Deep Learning?","max_new_tokens":17,"top_k":10,"top_p":0.95,"typical_p":0.95,"temperature":0.01,"repetition_penalty":1.03,"streaming":true}' \
  -H 'Content-Type: application/json'
```

## 4. Validated Model

| Model                     | TGI-Gaudi | vLLM-CPU | vLLM-Gaudi | Ray |
| ------------------------- | --------- | -------- | ---------- | --- |
| Intel/neural-chat-7b-v3-3 | ✓         | ✓        | ✓          | ✓   |
| Llama-2-7b-chat-hf        | ✓         | ✓        | ✓          | ✓   |
| Llama-2-70b-chat-hf       | ✓         | -        | ✓          | x   |
| Meta-Llama-3-8B-Instruct  | ✓         | ✓        | ✓          | ✓   |
| Meta-Llama-3-70B-Instruct | ✓         | -        | ✓          | x   |
| Phi-3                     | x         | Limit 4K | Limit 4K   | ✓   |
