# Build Mega Service of AudioQnA on Gaudi

This document outlines the deployment process for a AudioQnA application utilizing the [GenAIComps](https://github.com/opea-project/GenAIComps.git) microservice pipeline on Intel Gaudi server.

## 🚀 Build Docker images

### 1. Source Code install GenAIComps

```bash
git clone https://github.com/opea-project/GenAIComps.git
cd GenAIComps
```

### 2. Build ASR Image

```bash
docker build -t opea/whisper:latest --build-arg https_proxy=$https_proxy --build-arg http_proxy=$http_proxy -f comps/asr/whisper/Dockerfile_hpu .


docker build -t opea/asr:latest --build-arg https_proxy=$https_proxy --build-arg http_proxy=$http_proxy -f comps/asr/Dockerfile .
```

### 3. Build LLM Image

```bash
docker build --no-cache -t opea/llm-tgi:latest --build-arg https_proxy=$https_proxy --build-arg http_proxy=$http_proxy -f comps/llms/text-generation/tgi/Dockerfile .
```

### 4. Build TTS Image

```bash
docker build -t opea/speecht5:latest --build-arg https_proxy=$https_proxy --build-arg http_proxy=$http_proxy -f comps/tts/speecht5/Dockerfile_hpu .

docker build -t opea/tts:latest --build-arg https_proxy=$https_proxy --build-arg http_proxy=$http_proxy -f comps/tts/Dockerfile .
```

### 6. Build MegaService Docker Image

To construct the Mega Service, we utilize the [GenAIComps](https://github.com/opea-project/GenAIComps.git) microservice pipeline within the `audioqna.py` Python script. Build the MegaService Docker image using the command below:

```bash
git clone https://github.com/opea-project/GenAIExamples.git
cd GenAIExamples/AudioQnA/docker
docker build --no-cache -t opea/audioqna:latest --build-arg https_proxy=$https_proxy --build-arg http_proxy=$http_proxy -f Dockerfile .
```

Then run the command `docker images`, you will have following images ready:

1. `opea/whisper:latest`
2. `opea/asr:latest`
3. `opea/llm-tgi:latest`
4. `opea/speecht5:latest`
5. `opea/tts:latest`
6. `opea/audioqna:latest`

## 🚀 Set the environment variables

Before starting the services with `docker compose`, you have to recheck the following environment variables.

```bash
export host_ip=<your External Public IP>    # export host_ip=$(hostname -I | awk '{print $1}')
export HUGGINGFACEHUB_API_TOKEN=<your HF token>

export TGI_LLM_ENDPOINT=http://$host_ip:3006
export LLM_MODEL_ID=Intel/neural-chat-7b-v3-3

export ASR_ENDPOINT=http://$host_ip:7066
export TTS_ENDPOINT=http://$host_ip:7055

export MEGA_SERVICE_HOST_IP=${host_ip}
export ASR_SERVICE_HOST_IP=${host_ip}
export TTS_SERVICE_HOST_IP=${host_ip}
export LLM_SERVICE_HOST_IP=${host_ip}

export ASR_SERVICE_PORT=3001
export TTS_SERVICE_PORT=3002
export LLM_SERVICE_PORT=3007
```

## 🚀 Start the MegaService

```bash
cd GenAIExamples/AudioQnA/docker/gaudi/
docker compose -f docker_compose.yaml up -d
```

## 🚀 Test MicroServices

```bash
# whisper service
curl http://${host_ip}:7066/v1/asr \
  -X POST \
  -d '{"audio": "UklGRigAAABXQVZFZm10IBIAAAABAAEARKwAAIhYAQACABAAAABkYXRhAgAAAAEA"}' \
  -H 'Content-Type: application/json'

# asr microservice
curl http://${host_ip}:3001/v1/audio/transcriptions \
  -X POST \
  -d '{"byte_str": "UklGRigAAABXQVZFZm10IBIAAAABAAEARKwAAIhYAQACABAAAABkYXRhAgAAAAEA"}' \
  -H 'Content-Type: application/json'

# tgi service
curl http://${host_ip}:3006/generate \
  -X POST \
  -d '{"inputs":"What is Deep Learning?","parameters":{"max_new_tokens":17, "do_sample": true}}' \
  -H 'Content-Type: application/json'

# llm microservice
curl http://${host_ip}:3007/v1/chat/completions\
  -X POST \
  -d '{"query":"What is Deep Learning?","max_new_tokens":17,"top_k":10,"top_p":0.95,"typical_p":0.95,"temperature":0.01,"repetition_penalty":1.03,"streaming":false}' \
  -H 'Content-Type: application/json'

# speecht5 service
curl http://${host_ip}:7055/v1/tts \
  -X POST \
  -d '{"text": "Who are you?"}' \
  -H 'Content-Type: application/json'

# tts microservice
curl http://${host_ip}:3002/v1/audio/speech \
  -X POST \
  -d '{"text": "Who are you?"}' \
  -H 'Content-Type: application/json'

```

## 🚀 Test MegaService

```bash
curl http://${host_ip}:3008/v1/audioqna \
  -X POST \
  -d '{"audio": "UklGRigAAABXQVZFZm10IBIAAAABAAEARKwAAIhYAQACABAAAABkYXRhAgAAAAEA", "max_tokens":64}' \
  -H 'Content-Type: application/json'
```
