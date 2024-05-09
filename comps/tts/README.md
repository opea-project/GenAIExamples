# TTS Microservice

TTS (Text-To-Speech) micro-service helps users convert text to speech. When building a talkingbot with LLM, users may need to get the LLM dgenerated answer in audio. This microservice is built for that conversion stage.

# 🚀Start Microservice with Python

To start the TTS microservice, you need to install python packages first.

## Install Requirements

```bash
pip install -r requirements.txt
```

## Start TTS Service with Python Script

```bash
python tts.py
```

# 🚀Start Microservice with Docker

The other way is to start the ASR microservice with Docker.

## Build Docker Image

```bash
cd ../../
docker build -t intel/gen-ai-comps:tts --build-arg https_proxy=$https_proxy --build-arg http_proxy=$http_proxy -f comps/tts/Dockerfile .
```

## Run Docker with CLI

```bash
docker run -p 9999:9999 --network=host --ipc=host -e http_proxy=$http_proxy -e https_proxy=$https_proxy intel/gen-ai-comps:tts
```

# Test

You can use the following `curl` command to test whether the service is up. Notice that the first request can be slow because it need to pre-download the models.

```bash
curl http://localhost:9999/v1/audio/speech -H "Content-Type: application/json"   -d '{"text":"Hello there."}'
```
