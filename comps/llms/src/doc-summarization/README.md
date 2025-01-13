# Document Summary LLM Microservice

This microservice leverages LangChain to implement summarization strategies and facilitate LLM inference using Text Generation Inference on Intel Xeon and Gaudi2 processors. You can set backend service either [TGI](../../../third_parties/tgi) or [vLLM](../../../third_parties/vllm).

## 🚀1. Start Microservice with Docker 🐳

### 1.1 Setup Environment Variables

In order to start DocSum services, you need to setup the following environment variables first.

```bash
export host_ip=${your_host_ip}
export LLM_ENDPOINT_PORT=8008
export DOCSUM_PORT=9000
export HUGGINGFACEHUB_API_TOKEN=${your_hf_api_token}
export LLM_ENDPOINT="http://${host_ip}:${LLM_ENDPOINT_PORT}"
export LLM_MODEL_ID=${your_hf_llm_model}
export MAX_INPUT_TOKENS=2048
export MAX_TOTAL_TOKENS=4096
export DocSum_COMPONENT_NAME="OPEADocSum_TGI" # or "OPEADocSum_vLLM"
```

Please make sure MAX_TOTAL_TOKENS should be larger than (MAX_INPUT_TOKENS + max_new_tokens + 50), 50 is reserved prompt length.

### 1.2 Build Docker Image

Step 1: Prepare backend LLM docker image.

If you want to use vLLM backend, refer to [vLLM](../../../third_parties/vllm/src) to build vLLM docker images first.

No need for TGI.

Step 2: Build FaqGen docker image.

```bash
cd ../../../../
docker build -t opea/llm-docsum:latest --build-arg https_proxy=$https_proxy --build-arg http_proxy=$http_proxy -f comps/llms/src/summarization/Dockerfile .
```

### 1.3 Run Docker

To start a docker container, you have two options:

- A. Run Docker with CLI
- B. Run Docker with Docker Compose

You can choose one as needed.

### 1.3.1 Run Docker with CLI (Option A)

Step 1: Start the backend LLM service
Please refer to [TGI](../../../third_parties/tgi/deployment/docker_compose/) or [vLLM](../../../third_parties/vllm/deployment/docker_compose/) guideline to start a backend LLM service.

Step 2: Start the DocSum microservices

```bash
docker run -d \
    --name="llm-docsum-server" \
    -p 9000:9000 \
    --ipc=host \
    -e http_proxy=$http_proxy \
    -e https_proxy=$https_proxy \
    -e LLM_MODEL_ID=$LLM_MODEL_ID \
    -e LLM_ENDPOINT=$LLM_ENDPOINT \
    -e HUGGINGFACEHUB_API_TOKEN=$HUGGINGFACEHUB_API_TOKEN \
    -e DocSum_COMPONENT_NAME=$DocSum_COMPONENT_NAME \
    -e MAX_INPUT_TOKENS=${MAX_INPUT_TOKENS} \
    -e MAX_TOTAL_TOKENS=${MAX_TOTAL_TOKENS} \
    opea/llm-docsum:latest
```

### 1.3.2 Run Docker with Docker Compose (Option B)

```bash
cd ../../deployment/docker_compose/

# Backend is TGI on xeon
docker compose -f doc-summarization_tgi.yaml up -d

# Backend is TGI on gaudi
# docker compose -f doc-summarization_tgi_on_intel_hpu.yaml up -d

# Backend is vLLM on xeon
# docker compose -f doc-summarization_vllm.yaml up -d

# Backend is vLLM on gaudi
# docker compose -f doc-summarization_vllm_on_intel_hpu.yaml up -d
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

- "summary_type": can be "auto", "stuff", "truncate", "map_reduce", "refine", default is "auto"
- "chunk_size": max token length for each chunk. Set to be different default value according to "summary_type".
- "chunk_overlap": overlap token length between each chunk, default is 0.1\*chunk_size

#### 3.2.1 Basic usage

```bash
# Enable stream to receive a stream response. By default, this is set to True.
curl http://${your_ip}:9000/v1/docsum \
  -X POST \
  -d '{"query":"Text Embeddings Inference (TEI) is a toolkit for deploying and serving open source text embeddings and sequence classification models. TEI enables high-performance extraction for the most popular models, including FlagEmbedding, Ember, GTE and E5.", "max_tokens":32, "language":"en"}' \
  -H 'Content-Type: application/json'

# Disable stream to receive a non-stream response.
curl http://${your_ip}:9000/v1/docsum \
  -X POST \
  -d '{"query":"Text Embeddings Inference (TEI) is a toolkit for deploying and serving open source text embeddings and sequence classification models. TEI enables high-performance extraction for the most popular models, including FlagEmbedding, Ember, GTE and E5.", "max_tokens":32, "language":"en", "stream":false}' \
  -H 'Content-Type: application/json'

# Use Chinese mode
curl http://${your_ip}:9000/v1/docsum \
  -X POST \
  -d '{"query":"2024年9月26日，北京——今日，英特尔正式发布英特尔® 至强® 6性能核处理器（代号Granite Rapids），为AI、数据分析、科学计算等计算密集型业务提供卓越性能。", "max_tokens":32, "language":"zh", "stream":false}' \
  -H 'Content-Type: application/json'
```

#### 3.2.2 Long context summarization with "summary_type"

**summary_type=auto**

"summary_type" is set to be "auto" by default, in this mode we will check input token length, if it exceed `MAX_INPUT_TOKENS`, `summary_type` will automatically be set to `refine` mode, otherwise will be set to `stuff` mode.

**summary_type=stuff**

In this mode LLM generate summary based on complete input text. In this case please carefully set `MAX_INPUT_TOKENS` and `MAX_TOTAL_TOKENS` according to your model and device memory, otherwise it may exceed LLM context limit and raise error when meet long context.

**summary_type=truncate**

Truncate mode will truncate the input text and keep only the first chunk, whose length is equal to `min(MAX_TOTAL_TOKENS - input.max_tokens - 50, MAX_INPUT_TOKENS)`

```bash
curl http://${your_ip}:9000/v1/docsum \
  -X POST \
  -d '{"query":"Text Embeddings Inference (TEI) is a toolkit for deploying and serving open source text embeddings and sequence classification models. TEI enables high-performance extraction for the most popular models, including FlagEmbedding, Ember, GTE and E5.", "max_tokens":32, "language":"en", "summary_type": "truncate", "chunk_size": 2000}' \
  -H 'Content-Type: application/json'
```

**summary_type=map_reduce**

Map_reduce mode will split the inputs into multiple chunks, map each document to an individual summary, then consolidate those summaries into a single global summary. `stream=True` is not allowed here.

In this mode, default `chunk_size` is set to be `min(MAX_TOTAL_TOKENS - input.max_tokens - 50, MAX_INPUT_TOKENS)`

```bash
curl http://${your_ip}:9000/v1/docsum \
  -X POST \
  -d '{"query":"Text Embeddings Inference (TEI) is a toolkit for deploying and serving open source text embeddings and sequence classification models. TEI enables high-performance extraction for the most popular models, including FlagEmbedding, Ember, GTE and E5.", "max_tokens":32, "language":"en", "summary_type": "map_reduce", "chunk_size": 2000, "stream":false}' \
  -H 'Content-Type: application/json'
```

**summary_type=refine**

Refin mode will split the inputs into multiple chunks, generate summary for the first one, then combine with the second, loops over every remaining chunks to get the final summary.

In this mode, default `chunk_size` is set to be `min(MAX_TOTAL_TOKENS - 2 * input.max_tokens - 128, MAX_INPUT_TOKENS)`.

```bash
curl http://${your_ip}:9000/v1/docsum \
  -X POST \
  -d '{"query":"Text Embeddings Inference (TEI) is a toolkit for deploying and serving open source text embeddings and sequence classification models. TEI enables high-performance extraction for the most popular models, including FlagEmbedding, Ember, GTE and E5.", "max_tokens":32, "language":"en", "summary_type": "refine", "chunk_size": 2000}' \
  -H 'Content-Type: application/json'
```
