# Intent Detection Microservice by TGI

## 🚀1. Start Microservice with Python（Option 1）

### 1.1 Install Requirements

```bash
pip install -r requirements.txt
```

### 1.2 Start TGI Service

```bash
export HUGGINGFACEHUB_API_TOKEN=${your_hf_api_token}
docker run -p 8008:80 -v ./data:/data --name tgi_service --shm-size 1g ghcr.io/huggingface/text-generation-inference:1.4 --model-id ${your_hf_llm_model}
```

### 1.3 Verify the TGI Service

```bash
curl http://${your_ip}:8008/generate \
  -X POST \
  -d '{"inputs":"What is Deep Learning?","parameters":{"max_new_tokens":17, "do_sample": true}}' \
  -H 'Content-Type: application/json'
```

### 1.4 Setup Environment Variables

```bash
export TGI_LLM_ENDPOINT="http://${your_ip}:8008"
```

### 1.5 Start Intent Detection Microservice with Python Script

Start intent detection microservice with below command.

```bash
cd /your_project_path/GenAIComps/
cp comps/intent_detection/langchain/intent_detection.py .
python intent_detection.py
```

## 🚀2. Start Microservice with Docker (Option 2)

### 2.1 Start TGI Service

Please refer to 1.2.

### 2.2 Setup Environment Variables

```bash
export TGI_LLM_ENDPOINT="http://${your_ip}:8008"
```

### 2.3 Build Docker Image

```bash
cd /your_project_path/GenAIComps
docker build --no-cache -t opea/llm-tgi:latest -f comps/intent_detection/langchain/Dockerfile .
```

### 2.4 Run Docker with CLI (Option A)

```bash
docker run -it --name="intent-tgi-server" --net=host --ipc=host -e http_proxy=$http_proxy -e https_proxy=$https_proxy -e TGI_LLM_ENDPOINT=$TGI_LLM_ENDPOINT -e HUGGINGFACEHUB_API_TOKEN=$HUGGINGFACEHUB_API_TOKEN opea/llm-tgi:latest
```

### 2.5 Run with Docker Compose (Option B)

```bash
cd /your_project_path/GenAIComps/comps/intent_detection/langchain
export LLM_MODEL_ID=${your_hf_llm_model}
export http_proxy=${your_http_proxy}
export https_proxy=${your_http_proxy}
export TGI_LLM_ENDPOINT="http://tgi-service:80"
export HUGGINGFACEHUB_API_TOKEN=${your_hf_api_token}
docker compose -f docker_compose_intent.yaml up -d
```

## 🚀3. Consume Microservice

Once intent detection microservice is started, user can use below command to invoke the microservice.

```bash
curl http://${your_ip}:9000/v1/chat/intent\
  -X POST \
  -d '{"query":"What is Deep Learning?","max_new_tokens":10,"top_k":1,"temperature":0.001,"streaming":false}' \
  -H 'Content-Type: application/json'
```
