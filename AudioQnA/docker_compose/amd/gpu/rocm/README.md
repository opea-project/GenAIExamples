# Build Mega Service of AudioQnA on AMD ROCm GPU

This document outlines the deployment process for a AudioQnA application utilizing the [GenAIComps](https://github.com/opea-project/GenAIComps.git) microservice
pipeline on server on AMD ROCm GPU platform.

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

For compose for ROCm example AMD optimized image hosted in huggingface repo will be used for TGI service: ghcr.io/huggingface/text-generation-inference:2.3.1-rocm (https://github.com/huggingface/text-generation-inference)

### 4. Build TTS Image

```bash
docker build -t opea/speecht5:latest --build-arg https_proxy=$https_proxy --build-arg http_proxy=$http_proxy -f comps/tts/src/integrations/dependency/speecht5/Dockerfile .
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

export WHISPER_SERVER_PORT=7066
export SPEECHT5_SERVER_PORT=7055
export LLM_SERVER_PORT=3006

export BACKEND_SERVICE_ENDPOINT=http://${host_ip}:3008/v1/audioqna
```

or use set_env.sh file to setup environment variables.

Note: Please replace with host_ip with your external IP address, do not use localhost.

Note: In order to limit access to a subset of GPUs, please pass each device individually using one or more -device /dev/dri/rendered, where is the card index, starting from 128. (https://rocm.docs.amd.com/projects/install-on-linux/en/latest/how-to/docker.html#docker-restrict-gpus)

Example for set isolation for 1 GPU

      - /dev/dri/card0:/dev/dri/card0
      - /dev/dri/renderD128:/dev/dri/renderD128

Example for set isolation for 2 GPUs

      - /dev/dri/card0:/dev/dri/card0
      - /dev/dri/renderD128:/dev/dri/renderD128
      - /dev/dri/card0:/dev/dri/card0
      - /dev/dri/renderD129:/dev/dri/renderD129

Please find more information about accessing and restricting AMD GPUs in the link (https://rocm.docs.amd.com/projects/install-on-linux/en/latest/how-to/docker.html#docker-restrict-gpus)

## 🚀 Start the MegaService

```bash
cd GenAIExamples/AudioQnA/docker_compose/amd/gpu/rocm/
docker compose up -d
```

In following cases, you could build docker image from source by yourself.

- Failed to download the docker image.
- If you want to use a specific version of Docker image.

Please refer to 'Build Docker Images' in below.

## 🚀 Consume the AudioQnA Service

Test the AudioQnA megaservice by recording a .wav file, encoding the file into the base64 format, and then sending the
base64 string to the megaservice endpoint. The megaservice will return a spoken response as a base64 string. To listen
to the response, decode the base64 string and save it as a .wav file.

```bash
# voice can be "default" or "male"
curl http://${host_ip}:3008/v1/audioqna \
  -X POST \
  -d '{"audio": "UklGRigAAABXQVZFZm10IBIAAAABAAEARKwAAIhYAQACABAAAABkYXRhAgAAAAEA", "max_tokens":64, "voice":"default"}' \
  -H 'Content-Type: application/json' | sed 's/^"//;s/"$//' | base64 -d > output.wav
```

## 🚀 Test MicroServices

```bash
# whisper service
curl http://${host_ip}:7066/v1/asr \
  -X POST \
  -d '{"audio": "UklGRigAAABXQVZFZm10IBIAAAABAAEARKwAAIhYAQACABAAAABkYXRhAgAAAAEA"}' \
  -H 'Content-Type: application/json'

# tgi service
curl http://${host_ip}:3006/generate \
  -X POST \
  -d '{"inputs":"What is Deep Learning?","parameters":{"max_new_tokens":17, "do_sample": true}}' \
  -H 'Content-Type: application/json'

# speecht5 service
curl http://${host_ip}:7055/v1/tts \
  -X POST \
  -d '{"text": "Who are you?"}' \
  -H 'Content-Type: application/json'
```
