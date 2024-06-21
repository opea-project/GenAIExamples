# ASR Microservice

ASR (Audio-Speech-Recognition) microservice helps users convert speech to text. When building a talking bot with LLM, users will need to convert their audio inputs (What they talk, or Input audio from other sources) to text, so the LLM is able to tokenize the text and generate an answer. This microservice is built for that conversion stage.

# 🚀1. Start Microservice with Python (Option 1)

To start the ASR microservice with Python, you need to first install python packages.

## 1.1 Install Requirements

```bash
pip install -r requirements.txt
```

## 1.2 Start Whisper Service/Test

- Xeon CPU

```bash
cd whisper/
nohup python whisper_server.py --device=cpu &
python check_whisper_server.py
```

- Gaudi2 HPU

```bash
pip install optimum[habana]

cd whisper/
nohup python whisper_server.py --device=hpu &
python check_whisper_server.py
```

## 1.3 Start ASR Service/Test

```bash
python asr.py
python check_asr_server.py
```

# 🚀2. Start Microservice with Docker (Option 2)

Alternatively, you can also start the ASR microservice with Docker.

## 2.1 Build Images

### 2.1.1 Whisper Server Image

- Xeon CPU

```bash
cd ../..
docker build -t opea/whisper:latest --build-arg https_proxy=$https_proxy --build-arg http_proxy=$http_proxy -f comps/asr/whisper/Dockerfile .
```

- Gaudi2 HPU

```bash
cd ../..
docker build -t opea/whisper:latest --build-arg https_proxy=$https_proxy --build-arg http_proxy=$http_proxy -f comps/asr/whisper/Dockerfile_hpu .
```

### 2.1.2 ASR Service Image

```bash
docker build -t opea/asr:latest --build-arg https_proxy=$https_proxy --build-arg http_proxy=$http_proxy -f comps/asr/Dockerfile .
```

## 2.2 Start Whisper and ASR Service

### 2.2.1 Start Whisper Server

- Xeon

```bash
docker run -p 7066:7066 --ipc=host -e http_proxy=$http_proxy -e https_proxy=$https_proxy opea/whisper:latest
```

- Gaudi2 HPU

```bash
docker run -p 7066:7066 --runtime=habana -e HABANA_VISIBLE_DEVICES=all -e OMPI_MCA_btl_vader_single_copy_mechanism=none --cap-add=sys_nice --ipc=host -e http_proxy=$http_proxy -e https_proxy=$https_proxy opea/whisper:latest
```

### 2.2.2 Start ASR service

```bash
ip_address=$(hostname -I | awk '{print $1}')

docker run -d -p 9099:9099 --ipc=host -e http_proxy=$http_proxy -e https_proxy=$https_proxy -e ASR_ENDPOINT=http://$ip_address:7066 opea/asr:latest
```

### 2.2.3 Test

```bash
# Use curl or python

# curl
http_proxy="" curl http://localhost:9099/v1/audio/transcriptions -XPOST -d '{"byte_str": "UklGRigAAABXQVZFZm10IBIAAAABAAEARKwAAIhYAQACABAAAABkYXRhAgAAAAEA"}' -H 'Content-Type: application/json'

# python
python check_asr_server.py
```
