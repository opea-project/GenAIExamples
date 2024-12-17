# Document Summary vLLM Microservice

This microservice leverages LangChain to implement summarization strategies and facilitate LLM inference using vLLM.
[vLLM](https://github.com/vllm-project/vllm) is a fast and easy-to-use library for LLM inference and serving, it delivers state-of-the-art serving throughput with a set of advanced features such as PagedAttention, Continuous batching and etc.. Besides GPUs, vLLM already supported [Intel CPUs](https://www.intel.com/content/www/us/en/products/overview.html) and [Gaudi accelerators](https://habana.ai/products).

## 🚀1. Start Microservice with Python 🐍 (Option 1)

To start the LLM microservice, you need to install python packages first.

### 1.1 Install Requirements

```bash
pip install -r requirements.txt
```

### 1.2 Start LLM Service

```bash
export HF_TOKEN=${your_hf_api_token}
export LLM_MODEL_ID=${your_hf_llm_model}
docker run -p 8008:80 -v ./data:/data --name llm-docsum-vllm --shm-size 1g opea/vllm-gaudi:latest --model-id ${LLM_MODEL_ID}
```

### 1.3 Verify the vLLM Service

```bash
curl http://${your_ip}:8008/v1/chat/completions \
    -X POST \
    -H "Content-Type: application/json" \
    -d '{"model": "meta-llama/Meta-Llama-3-8B-Instruct", "messages": [{"role": "user", "content": "What is Deep Learning? "}]}'
```

### 1.4 Start LLM Service with Python Script

```bash
export vLLM_ENDPOINT="http://${your_ip}:8008"
python llm.py
```

## 🚀2. Start Microservice with Docker 🐳 (Option 2)

If you start an LLM microservice with docker, the `docker_compose_llm.yaml` file will automatically start a vLLM/vLLM service with docker.

To setup or build the vLLM image follow the instructions provided in [vLLM Gaudi](https://github.com/opea-project/GenAIComps/tree/main/comps/llms/text-generation/vllm/langchain#22-vllm-on-gaudi)

### 2.1 Setup Environment Variables

In order to start vLLM and LLM services, you need to setup the following environment variables first.

```bash
export HF_TOKEN=${your_hf_api_token}
export vLLM_ENDPOINT="http://${your_ip}:8008"
export LLM_MODEL_ID=${your_hf_llm_model}
```

### 2.2 Build Docker Image

```bash
cd ../../../../../
docker build -t opea/llm-docsum-vllm:latest --build-arg https_proxy=$https_proxy --build-arg http_proxy=$http_proxy -f comps/llms/summarization/vllm/langchain/Dockerfile .
```

To start a docker container, you have two options:

- A. Run Docker with CLI
- B. Run Docker with Docker Compose

You can choose one as needed.

### 2.3 Run Docker with CLI (Option A)

```bash
docker run -d --name="llm-docsum-vllm-server" -p 9000:9000 --ipc=host -e http_proxy=$http_proxy -e https_proxy=$https_proxy -e vLLM_ENDPOINT=$vLLM_ENDPOINT -e HF_TOKEN=$HF_TOKEN opea/llm-docsum-vllm:latest
```

### 2.4 Run Docker with Docker Compose (Option B)

```bash
docker compose -f docker_compose_llm.yaml up -d
```

## 🚀3. Consume LLM Service

### 3.1 Check Service Status

```bash
curl http://${your_ip}:9000/v1/health_check\
  -X GET \
  -H 'Content-Type: application/json'
```

### 3.2 Consume LLM Service

In DocSum microservice, except for basic LLM parameters, we also support several optimization parameters setting.

- "language": specify the language, can be "auto", "en", "zh", default is "auto"

If you want to deal with long context, can select suitable summary type, details in section 3.2.2.

- "summary_type": can be "stuff", "truncate", "map_reduce", "refine", default is "stuff"
- "chunk_size": max token length for each chunk. Set to be different default value according to "summary_type".
- "chunk_overlap": overlap token length between each chunk, default is 0.1\*chunk_size

#### 3.2.1 Basic usage

```bash
# Enable streaming to receive a streaming response. By default, this is set to True.
curl http://${your_ip}:9000/v1/chat/docsum \
  -X POST \
  -d '{"query":"Text Embeddings Inference (TEI) is a toolkit for deploying and serving open source text embeddings and sequence classification models. TEI enables high-performance extraction for the most popular models, including FlagEmbedding, Ember, GTE and E5.", "max_tokens":32, "language":"en"}' \
  -H 'Content-Type: application/json'

# Disable streaming to receive a non-streaming response.
curl http://${your_ip}:9000/v1/chat/docsum \
  -X POST \
  -d '{"query":"Text Embeddings Inference (TEI) is a toolkit for deploying and serving open source text embeddings and sequence classification models. TEI enables high-performance extraction for the most popular models, including FlagEmbedding, Ember, GTE and E5.", "max_tokens":32, "language":"en", "streaming":false}' \
  -H 'Content-Type: application/json'

# Use Chinese mode
curl http://${your_ip}:9000/v1/chat/docsum \
  -X POST \
  -d '{"query":"2024年9月26日，北京——今日，英特尔正式发布英特尔® 至强® 6性能核处理器（代号Granite Rapids），为AI、数据分析、科学计算等计算密集型业务提供卓越性能。", "max_tokens":32, "language":"zh", "streaming":false}' \
  -H 'Content-Type: application/json'
```

#### 3.2.2 Long context summarization with "summary_type"

"summary_type" is set to be "stuff" by default, which will let LLM generate summary based on complete input text. In this case please carefully set `MAX_INPUT_TOKENS` and `MAX_TOTAL_TOKENS` according to your model and device memory, otherwise it may exceed LLM context limit and raise error when meet long context.

When deal with long context, you can set "summary_type" to one of "truncate", "map_reduce" and "refine" for better performance.

**summary_type=truncate**

Truncate mode will truncate the input text and keep only the first chunk, whose length is equal to `min(MAX_TOTAL_TOKENS - input.max_tokens - 50, MAX_INPUT_TOKENS)`

```bash
curl http://${your_ip}:9000/v1/chat/docsum \
  -X POST \
  -d '{"query":"Text Embeddings Inference (TEI) is a toolkit for deploying and serving open source text embeddings and sequence classification models. TEI enables high-performance extraction for the most popular models, including FlagEmbedding, Ember, GTE and E5.", "max_tokens":32, "language":"en", "summary_type": "truncate", "chunk_size": 2000}' \
  -H 'Content-Type: application/json'
```

**summary_type=map_reduce**

Map_reduce mode will split the inputs into multiple chunks, map each document to an individual summary, then consolidate those summaries into a single global summary. `streaming=True` is not allowed here.

In this mode, default `chunk_size` is set to be `min(MAX_TOTAL_TOKENS - input.max_tokens - 50, MAX_INPUT_TOKENS)`

```bash
curl http://${your_ip}:9000/v1/chat/docsum \
  -X POST \
  -d '{"query":"Text Embeddings Inference (TEI) is a toolkit for deploying and serving open source text embeddings and sequence classification models. TEI enables high-performance extraction for the most popular models, including FlagEmbedding, Ember, GTE and E5.", "max_tokens":32, "language":"en", "summary_type": "map_reduce", "chunk_size": 2000, "streaming":false}' \
  -H 'Content-Type: application/json'
```

**summary_type=refine**

Refin mode will split the inputs into multiple chunks, generate summary for the first one, then combine with the second, loops over every remaining chunks to get the final summary.

In this mode, default `chunk_size` is set to be `min(MAX_TOTAL_TOKENS - 2 * input.max_tokens - 128, MAX_INPUT_TOKENS)`.

```bash
curl http://${your_ip}:9000/v1/chat/docsum \
  -X POST \
  -d '{"query":"Text Embeddings Inference (TEI) is a toolkit for deploying and serving open source text embeddings and sequence classification models. TEI enables high-performance extraction for the most popular models, including FlagEmbedding, Ember, GTE and E5.", "max_tokens":32, "language":"en", "summary_type": "refine", "chunk_size": 2000}' \
  -H 'Content-Type: application/json'
```
