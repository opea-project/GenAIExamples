# Build Mega Service of AudioQnA on Xeon

This document outlines the deployment process for a AudioQnA application utilizing the [GenAIComps](https://github.com/opea-project/GenAIComps.git) microservice pipeline on Intel Xeon server. The steps include Docker image creation, container deployment via Docker Compose, and service execution to integrate microservices such as `asr`, `llm`, `tts`. We will publish the Docker images to Docker Hub soon, it will simplify the deployment process for this service.

## 🚀 Apply Xeon Server on AWS

To apply a Xeon server on AWS, start by creating an AWS account if you don't have one already. Then, head to the [EC2 Console](https://console.aws.amazon.com/ec2/v2/home) to begin the process. Within the EC2 service, select the Amazon EC2 M7i or M7i-flex instance type to leverage the power of 4th Generation Intel Xeon Scalable processors. These instances are optimized for high-performance computing and demanding workloads.

For detailed information about these instance types, you can refer to this [link](https://aws.amazon.com/ec2/instance-types/m7i/). Once you've chosen the appropriate instance type, proceed with configuring your instance settings, including network configurations, security groups, and storage options.

After launching your instance, you can connect to it using SSH (for Linux instances) or Remote Desktop Protocol (RDP) (for Windows instances). From there, you'll have full access to your Xeon server, allowing you to install, configure, and manage your applications as needed.

## 🚀 Build Docker Images

First of all, you need to build Docker Images locally and install the python package of it.

```bash
git clone https://github.com/opea-project/GenAIComps.git
cd GenAIComps
pip install -r requirements.txt
pip install .
```

### 1. Build/Run/Test ASR Image

```bash
docker build -t opea/gen-ai-comps:asr --build-arg https_proxy=$https_proxy --build-arg http_proxy=$http_proxy -f comps/asr/Dockerfile .
docker run -d -p 9099:9099 --ipc=host -e http_proxy=$http_proxy -e https_proxy=$https_proxy opea/gen-ai-comps:asr
curl http://localhost:9099/v1/audio/transcriptions -H "Content-Type: application/json" -d '{"url": "https://github.com/intel/intel-extension-for-transformers/raw/main/intel_extension_for_transformers/neural_chat/assets/audio/sample_2.wav"}'
```

### 2. Build/Run/Test TTS Image

```bash
docker build -t opea/gen-ai-comps:tts --build-arg https_proxy=$https_proxy --build-arg http_proxy=$http_proxy -f comps/tts/Dockerfile .
docker run -d -p 9999:9999 --ipc=host -e http_proxy=$http_proxy -e https_proxy=$https_proxy opea/gen-ai-comps:tts
curl http://localhost:9999/v1/audio/speech -H "Content-Type: application/json"   -d '{"text":"Hello there."}'
```

### 3. Build/Run/Test LLM Image

#### 3.1 Launch TGI

```bash
export LLM_MODEL_ID="Intel/neural-chat-7b-v3-3"
docker run -d -p 8009:80 -v ./data:/data ghcr.io/huggingface/text-generation-inference:1.4 --model-id ${LLM_MODEL_ID}
curl http://localhost:8009/generate -X POST -d '{"inputs":"What is Deep Learning?"}' -H 'Content-Type: application/json'
```

#### 3.2 Launch LLM-TGI component

```bash
export TGI_LLM_ENDPOINT="http://${your_ip}:8009"
export HUGGINGFACEHUB_API_TOKEN=${your_hf_api_token}
docker build -t opea/gen-ai-comps:llm-tgi-server --build-arg https_proxy=$https_proxy --build-arg http_proxy=$http_proxy -f comps/llms/langchain/docker/Dockerfile .
docker run -d -e HUGGINGFACEHUB_API_TOKEN=${HUGGINGFACEHUB_API_TOKEN} -e TGI_LLM_ENDPOINT=${TGI_LLM_ENDPOINT} -p 9001:9000 --ipc=host -e http_proxy=$http_proxy -e https_proxy=$https_proxy opea/gen-ai-comps:llm-tgi-server
curl http://localhost:9001/v1/chat/completions -X POST -d '{"text":"What is Deep Learning?"}' -H 'Content-Type: application/json'
```

### 4. Build/Run Telemetry Image (Optional)

You can check the log of the following container to obtain the telemetry information.

```bash
docker run -p 4317:4317 -p 4318:4318 --rm -v $(pwd)/comps/cores/telemetry/collector-config.yaml:/etc/otelcol/config.yaml otel/opentelemetry-collector
```

## Wrap Up

You can use `docker-compose` to start all the above service with one YamL file, if you have already built the images.

```bash
export LLM_MODEL_ID="intel/neural-chat-7b-v3-3"
export TGI_LLM_ENDPOINT="http://${your_ip}:8008"
export HUGGINGFACEHUB_API_TOKEN=${your_hf_api_token}
docker compose -f docker_compose_xeon.yaml up -d
```

## Define the data flow

Considering the AudioQnA example's data flow is `ASR >> LLM+TGI >> TTS`, you can build the flow with `GenAIComps` through Python API or Yaml. We've prepare the Python script and the Yaml for you. Please check the `audioqna.py` or `audioqna.yaml` for details.

```
python audioqna.py
```

The other way is to start the flow with Yaml

```
python audioqna_with_yaml.py
```
