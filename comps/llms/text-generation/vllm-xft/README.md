vLLM-xFT is a fork of vLLM to integrate the xfastertransformer backend, maintaining compatibility with most of the official vLLM's features.
For usage of vllm-xFT, please refer to [xFasterTransformer/vllm-xft](https://github.com/intel/xFasterTransformer/blob/main/serving/vllm-xft.md)

# 🚀 Start Microservice with Docker

## 1 Build Docker Image

```bash
cd ../../../
docker build -t opea/llm-vllm-xft:latest --build-arg https_proxy=$https_proxy --build-arg http_proxy=$http_proxy -f comps/llms/text-generation/vllm-xft/docker/Dockerfile .
```

## 2 Run Docker with CLI

```bash
docker run -it -p 9000:9000  -v /home/sdp/Qwen2-7B-Instruct/:/Qwen2-7B-Instruct/   -e vLLM_LLM_ENDPOINT="http://localhost:18688" -e HF_DATASET_DIR="/Qwen2-7B-Instruct/" -e OUTPUT_DIR="./output" -e TOKEN_PATH="/Qwen2-7B-Instruct/" -e https_proxy=$https_proxy -e http_proxy=$http_proxy -e no_proxy=$no_proxy --ipc=host opea/llm-vllm-xft:latest
```

# 🚀3. Consume LLM Service

## 3.1 Check Service Status

```bash
curl http://${your_ip}:9000/v1/health_check\
  -X GET \
  -H 'Content-Type: application/json'
```

## 3.2 Consume LLM Service

You can set the following model parameters according to your actual needs, such as `max_new_tokens`, `streaming`.

The `streaming` parameter determines the format of the data returned by the API. It will return text string with `streaming=false`, return text streaming flow with `streaming=true`.

```bash
# non-streaming mode
curl http://${your_ip}:9000/v1/chat/completions \
  -X POST \
  -d '{"query":"What is Deep Learning?","max_new_tokens":17,"top_k":10,"top_p":0.95,"typical_p":0.95,"temperature":0.01,"repetition_penalty":1.03,"streaming":false}' \
  -H 'Content-Type: application/json'

# streaming mode
curl http://${your_ip}:9000/v1/chat/completions \
  -X POST \
  -d '{"query":"What is Deep Learning?","max_new_tokens":17,"top_k":10,"top_p":0.95,"typical_p":0.95,"temperature":0.01,"repetition_penalty":1.03,"streaming":true}' \
  -H 'Content-Type: application/json'
```
