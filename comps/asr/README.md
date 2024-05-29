# ASR Microservice

ASR (Audio-Speech-Recognition) microservice helps users convert speech to text. When building a talking bot with LLM, users will need to convert their audio inputs (What they talk, or Input audio from other sources) to text, so the LLM is able to tokenize the text and generate an answer. This microservice is built for that conversion stage.

# 🚀Start Microservice with Python

To start the ASR microservice with Python, you need to first install python packages.

## Install Requirements

```bash
pip install -r requirements.txt
```

## Start ASR Service with Python Script

```bash
python asr.py
```

# 🚀Start Microservice with Docker

Alternatively, you can also start the ASR microservice with Docker.

## Build Docker Image

```bash
cd ../../
docker build -t opea/gen-ai-comps:asr --build-arg https_proxy=$https_proxy --build-arg http_proxy=$http_proxy -f comps/asr/Dockerfile .
```

## Run Docker with CLI

```bash
docker run -p 9099:9099 --network=host --ipc=host -e http_proxy=$http_proxy -e https_proxy=$https_proxy opea/gen-ai-comps:asr
```

# Test

You can use the following `curl` command to test whether the service is up. Notice that the first request can be slow because it needs to download the models.

```bash
curl http://localhost:9099/v1/audio/transcriptions -H "Content-Type: application/json" -d '{"url": "https://github.com/intel/intel-extension-for-transformers/raw/main/intel_extension_for_transformers/neural_chat/assets/audio/sample_2.wav"}'
```
