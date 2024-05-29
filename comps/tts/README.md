# TTS Microservice

TTS (Text-To-Speech) microservice helps users convert text to speech. When building a talking bot with LLM, users might need an LLM generated answer in audio format. This microservice is built for that conversion stage.

# 🚀Start Microservice with Python

To start the TTS microservice, you need to first install python packages.

## Install Requirements

```bash
pip install -r requirements.txt
```

## Start TTS Service with Python Script

```bash
python tts.py
```

# 🚀Start Microservice with Docker

Alternatively, you can start the ASR microservice with Docker.

## Build Docker Image

```bash
cd ../../
docker build -t opea/gen-ai-comps:tts --build-arg https_proxy=$https_proxy --build-arg http_proxy=$http_proxy -f comps/tts/Dockerfile .
```

## Run Docker with CLI

```bash
docker run -p 9999:9999 --network=host --ipc=host -e http_proxy=$http_proxy -e https_proxy=$https_proxy opea/gen-ai-comps:tts
```

# Test

You can use the following `curl` command to test whether the service is up. Notice that the first request can be slow because it needs to download the models.

```bash
curl http://localhost:9999/v1/audio/speech -H "Content-Type: application/json"   -d '{"text":"Hello there."}'
```
