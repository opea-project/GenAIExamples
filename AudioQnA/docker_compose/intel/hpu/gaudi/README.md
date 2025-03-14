# Build Mega Service of AudioQnA on Gaudi

This document outlines the deployment process for a AudioQnA application utilizing the [GenAIComps](https://github.com/opea-project/GenAIComps.git) microservice pipeline on Intel Gaudi server.

The default pipeline deploys with vLLM as the LLM serving component. It also provides options of using TGI backend for LLM microservice, please refer to [Start the MegaService](#-start-the-megaservice) section in this page.

Note: The default LLM is `meta-llama/Meta-Llama-3-8B-Instruct`. Before deploying the application, please make sure either you've requested and been granted the access to it on [Huggingface](https://huggingface.co/meta-llama/Meta-Llama-3-8B-Instruct) or you've downloaded the model locally from [ModelScope](https://www.modelscope.cn/models).

## 🚀 Build Docker images

### 1. Source Code install GenAIComps

```bash
git clone https://github.com/opea-project/GenAIComps.git
cd GenAIComps
```

### 2. Build ASR Image

```bash
docker build -t opea/whisper-gaudi:latest --build-arg https_proxy=$https_proxy --build-arg http_proxy=$http_proxy -f comps/asr/src/integrations/dependency/whisper/Dockerfile.intel_hpu .
```

### 3. Build vLLM Image

git clone https://github.com/HabanaAI/vllm-fork.git
cd vllm-fork/
VLLM_VER=$(git describe --tags "$(git rev-list --tags --max-count=1)")
git checkout ${VLLM_VER}
docker build --no-cache --build-arg https_proxy=$https_proxy --build-arg http_proxy=$http_proxy -f Dockerfile.hpu -t opea/vllm-gaudi:latest --shm-size=128g .

### 4. Build TTS Image

```bash
docker build -t opea/speecht5-gaudi:latest --build-arg https_proxy=$https_proxy --build-arg http_proxy=$http_proxy -f comps/tts/src/integrations/dependency/speecht5/Dockerfile.intel_hpu .
```

### 5. Build MegaService Docker Image

To construct the Mega Service, we utilize the [GenAIComps](https://github.com/opea-project/GenAIComps.git) microservice pipeline within the `audioqna.py` Python script. Build the MegaService Docker image using the command below:

```bash
git clone https://github.com/opea-project/GenAIExamples.git
cd GenAIExamples/AudioQnA/
docker build --no-cache -t opea/audioqna:latest --build-arg https_proxy=$https_proxy --build-arg http_proxy=$http_proxy -f Dockerfile .
```

Then run the command `docker images`, you will have following images ready:

1. `opea/whisper-gaudi:latest`
2. `opea/vllm-gaudi:latest`
3. `opea/speecht5-gaudi:latest`
4. `opea/audioqna:latest`

## 🚀 Set the environment variables

Before starting the services with `docker compose`, you have to recheck the following environment variables.

```bash
export host_ip=<your External Public IP>    # export host_ip=$(hostname -I | awk '{print $1}')
export HUGGINGFACEHUB_API_TOKEN=<your HF token>

export LLM_MODEL_ID="meta-llama/Meta-Llama-3-8B-Instruct"
# set vLLM parameters
export NUM_CARDS=1
export BLOCK_SIZE=128
export MAX_NUM_SEQS=256
export MAX_SEQ_LEN_TO_CAPTURE=2048

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

Note:

- Please replace with host_ip with your external IP address, do not use localhost.
- If you are in a proxy environment, also set the proxy-related environment variables:

```
export http_proxy="Your_HTTP_Proxy"
export https_proxy="Your_HTTPs_Proxy"
# Example: no_proxy="localhost, 127.0.0.1, 192.168.1.1"
export no_proxy="Your_No_Proxy",${host_ip},whisper-service,speecht5-service,tgi-service,vllm-service,audioqna-gaudi-backend-server,audioqna-gaudi-ui-server
```

## 🚀 Start the MegaService

> **_NOTE:_** Users will need at least three Gaudi cards for AudioQnA.

```bash
cd GenAIExamples/AudioQnA/docker_compose/intel/hpu/gaudi/
```

If use vLLM as the LLM serving backend:

```
docker compose up -d
```

If use TGI as the LLM serving backend:

```
docker compose -f compose_tgi.yaml up -d
```

## 🚀 Test MicroServices

1. Whisper Service

   ```bash
   curl http://${host_ip}:${WHISPER_SERVER_PORT}/v1/asr \
     -X POST \
     -d '{"audio": "UklGRigAAABXQVZFZm10IBIAAAABAAEARKwAAIhYAQACABAAAABkYXRhAgAAAAEA"}' \
     -H 'Content-Type: application/json'
   ```

2. LLM backend Service

   In the first startup, this service will take more time to download, load and warm up the model. After it's finished, the service will be ready and the container (`vllm-gaudi-service` or `tgi-gaudi-service`) status shown via `docker ps` will be `healthy`. Before that, the status will be `health: starting`.

   Or try the command below to check whether the LLM serving is ready.

   ```bash
   # vLLM service
   docker logs vllm-gaudi-service 2>&1 | grep complete
   # If the service is ready, you will get the response like below.
   INFO:     Application startup complete.
   ```

   ```bash
   # TGI service
   docker logs tgi-gaudi-service | grep Connected
   # If the service is ready, you will get the response like below.
   2024-09-03T02:47:53.402023Z  INFO text_generation_router::server: router/src/server.rs:2311: Connected
   ```

   Then try the `cURL` command below to validate services.

   ```bash
   # either vLLM or TGI service
   curl http://${host_ip}:${LLM_SERVER_PORT}/v1/chat/completions \
     -X POST \
     -d '{"model": "meta-llama/Meta-Llama-3-8B-Instruct", "messages": [{"role": "user", "content": "What is Deep Learning?"}], "max_tokens":17}' \
     -H 'Content-Type: application/json'
   ```

3. TTS Service

   ```
   # speecht5 service
   curl http://${host_ip}:${SPEECHT5_SERVER_PORT}/v1/tts
     -X POST \
     -d '{"text": "Who are you?"}' \
     -H 'Content-Type: application/json'
   ```

## 🚀 Test MegaService

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
