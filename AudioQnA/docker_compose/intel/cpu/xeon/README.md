# Build Mega Service of AudioQnA on Xeon

This document outlines the deployment process for a AudioQnA application utilizing the [GenAIComps](https://github.com/opea-project/GenAIComps.git) microservice pipeline on Intel Xeon server.

## 🚀 Build Docker images

### 1. Source Code install GenAIComps

```bash
git clone https://github.com/opea-project/GenAIComps.git
cd GenAIComps
```

### 2. Build ASR Image

```bash
docker build -t opea/whisper:latest --build-arg https_proxy=$https_proxy --build-arg http_proxy=$http_proxy -f comps/asr/src/integrations/dependency/whisper/Dockerfile .
```

### 3. Build LLM Image

Intel Xeon optimized image hosted in huggingface repo will be used for TGI service: ghcr.io/huggingface/text-generation-inference:2.4.0-intel-cpu (https://github.com/huggingface/text-generation-inference)

### 4. Build TTS Image

```bash
docker build -t opea/speecht5:latest --build-arg https_proxy=$https_proxy --build-arg http_proxy=$http_proxy -f comps/tts/src/integrations/dependency/speecht5/Dockerfile .

# multilang tts (optional)
docker build -t opea/gpt-sovits:latest --build-arg http_proxy=$http_proxy --build-arg https_proxy=$https_proxy -f comps/tts/src/integrations/dependency/gpt-sovits/Dockerfile .
```

### 5. Build MegaService Docker Image

To construct the Mega Service, we utilize the [GenAIComps](https://github.com/opea-project/GenAIComps.git) microservice pipeline within the `audioqna.py` Python script. Build the MegaService Docker image using the command below:

```bash
git clone https://github.com/opea-project/GenAIExamples.git
cd GenAIExamples/AudioQnA/
docker build --no-cache -t opea/audioqna:latest --build-arg https_proxy=$https_proxy --build-arg http_proxy=$http_proxy -f Dockerfile .
```

Then run the command `docker images`, you will have following images ready:

1. `opea/whisper:latest`
2. `opea/speecht5:latest`
3. `opea/audioqna:latest`
4. `opea/gpt-sovits:latest` (optional)

## 🚀 Set the environment variables

Before starting the services with `docker compose`, you have to recheck the following environment variables.

```bash
export host_ip=<your External Public IP>    # export host_ip=$(hostname -I | awk '{print $1}')
export HUGGINGFACEHUB_API_TOKEN=<your HF token>

export LLM_MODEL_ID=Intel/neural-chat-7b-v3-3

export MEGA_SERVICE_HOST_IP=${host_ip}
export WHISPER_SERVER_HOST_IP=${host_ip}
export SPEECHT5_SERVER_HOST_IP=${host_ip}
export LLM_SERVER_HOST_IP=${host_ip}
export GPT_SOVITS_SERVER_HOST_IP=${host_ip}

export WHISPER_SERVER_PORT=7066
export SPEECHT5_SERVER_PORT=7055
export GPT_SOVITS_SERVER_PORT=9880
export LLM_SERVER_PORT=3006

export BACKEND_SERVICE_ENDPOINT=http://${host_ip}:3008/v1/audioqna
```

or use set_env.sh file to setup environment variables.

Note: Please replace with host_ip with your external IP address, do not use localhost.

## 🚀 Start the MegaService

```bash
cd GenAIExamples/AudioQnA/docker_compose/intel/cpu/xeon/
docker compose up -d

# multilang tts (optional)
docker compose -f compose_multilang.yaml up -d
```

## 🚀 Test MicroServices

```bash
# whisper service
wget https://github.com/intel/intel-extension-for-transformers/raw/main/intel_extension_for_transformers/neural_chat/assets/audio/sample.wav
curl http://${host_ip}:7066/v1/audio/transcriptions \
  -H "Content-Type: multipart/form-data" \
  -F file="@./sample.wav" \
  -F model="openai/whisper-small"

# tgi service
curl http://${host_ip}:3006/generate \
  -X POST \
  -d '{"inputs":"What is Deep Learning?","parameters":{"max_new_tokens":17, "do_sample": true}}' \
  -H 'Content-Type: application/json'

# speecht5 service
curl http://${host_ip}:7055/v1/audio/speech -XPOST -d '{"input": "Who are you?"}' -H 'Content-Type: application/json' --output speech.mp3

# gpt-sovits service (optional)
curl http://${host_ip}:9880/v1/audio/speech -XPOST -d '{"input": "Who are you?"}' -H 'Content-Type: application/json' --output speech.mp3
```

## 🚀 Test MegaService

Test the AudioQnA megaservice by recording a .wav file, encoding the file into the base64 format, and then sending the
base64 string to the megaservice endpoint. The megaservice will return a spoken response as a base64 string. To listen
to the response, decode the base64 string and save it as a .wav file.

```bash
# if you are using speecht5 as the tts service, voice can be "default" or "male"
# if you are using gpt-sovits for the tts service, you can set the reference audio following https://github.com/opea-project/GenAIComps/blob/main/comps/tts/src/integrations/dependency/gpt-sovits/README.md
curl http://${host_ip}:3008/v1/audioqna \
  -X POST \
  -d '{"audio": "UklGRigAAABXQVZFZm10IBIAAAABAAEARKwAAIhYAQACABAAAABkYXRhAgAAAAEA", "max_tokens":64, "voice":"default"}' \
  -H 'Content-Type: application/json' | sed 's/^"//;s/"$//' | base64 -d > output.wav
```
