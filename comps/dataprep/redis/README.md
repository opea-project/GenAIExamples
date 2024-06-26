# Dataprep Microservice with Redis

For dataprep microservice, we provide two frameworks: `Langchain` and `LlamaIndex`. We also provide `Langchain_ray` which uses ray to parallel the data prep for multi-file performance improvement(observed 5x - 15x speedup by processing 1000 files/links.).

We organized these two folders in the same way, so you can use either framework for dataprep microservice with the following constructions.

# 🚀1. Start Microservice with Python（Option 1）

## 1.1 Install Requirements

- option 1: Install Single-process version (for 1-10 files processing)

```bash
apt update
apt install default-jre
apt-get install tesseract-ocr -y
apt-get install libtesseract-dev -y
apt-get install poppler-utils -y
# for langchain
cd langchain
# for llama_index
cd llama_index
pip install -r requirements.txt
```

- option 2: Install multi-process version (for >10 files processing)

```bash
cd langchain_ray; pip install -r requirements_ray.txt
```

## 1.2 Start Redis Stack Server

Please refer to this [readme](../../../vectorstores/langchain/redis/README.md).

## 1.3 Setup Environment Variables

```bash
export REDIS_URL="redis://${your_ip}:6379"
export INDEX_NAME=${your_index_name}
export LANGCHAIN_TRACING_V2=true
export LANGCHAIN_API_KEY=${your_langchain_api_key}
export LANGCHAIN_PROJECT="opea/gen-ai-comps:dataprep"
```

## 1.4 Start Document Preparation Microservice for Redis with Python Script

Start document preparation microservice for Redis with below command.

- option 1: Start single-process version (for 1-10 files processing)

```bash
python prepare_doc_redis.py
```

- option 2: Start multi-process version (for >10 files processing)

```bash
python prepare_doc_redis_on_ray.py
```

# 🚀2. Start Microservice with Docker (Option 2)

## 2.1 Start Redis Stack Server

Please refer to this [readme](../../../vectorstores/langchain/redis/README.md).

## 2.2 Setup Environment Variables

```bash
export REDIS_URL="redis://${your_ip}:6379"
export INDEX_NAME=${your_index_name}
export LANGCHAIN_TRACING_V2=true
export LANGCHAIN_API_KEY=${your_langchain_api_key}
export LANGCHAIN_PROJECT="opea/dataprep"
```

## 2.3 Build Docker Image

- Build docker image with langchain

* option 1: Start single-process version (for 1-10 files processing)

```bash
cd ../../../../
docker build -t opea/dataprep-redis:latest --build-arg https_proxy=$https_proxy --build-arg http_proxy=$http_proxy -f comps/dataprep/redis/langchain/docker/Dockerfile .
```

- Build docker image with llama_index

```bash
cd ../../../../
docker build -t opea/dataprep-redis:latest --build-arg https_proxy=$https_proxy --build-arg http_proxy=$http_proxy -f comps/dataprep/redis/llama_index/docker/Dockerfile .
```

- option 2: Start multi-process version (for >10 files processing)

```bash
cd ../../../../
docker build -t opea/dataprep-on-ray-redis:latest --build-arg https_proxy=$https_proxy --build-arg http_proxy=$http_proxy -f comps/dataprep/redis/langchain_ray/docker/Dockerfile .
```

## 2.4 Run Docker with CLI (Option A)

- option 1: Start single-process version (for 1-10 files processing)

```bash
docker run -d --name="dataprep-redis-server" -p 6007:6007 --runtime=runc --ipc=host -e http_proxy=$http_proxy -e https_proxy=$https_proxy -e REDIS_URL=$REDIS_URL -e INDEX_NAME=$INDEX_NAME -e TEI_ENDPOINT=$TEI_ENDPOINT opea/dataprep-redis:latest
```

- option 2: Start multi-process version (for >10 files processing)

```bash
docker run -d --name="dataprep-redis-server" -p 6007:6007 --runtime=runc --ipc=host -e http_proxy=$http_proxy -e https_proxy=$https_proxy -e REDIS_URL=$REDIS_URL -e INDEX_NAME=$INDEX_NAME -e TEI_ENDPOINT=$TEI_ENDPOINT -e TIMEOUT_SECONDS=600 opea/dataprep-on-ray-redis:latest
```

## 2.5 Run with Docker Compose (Option B - deprecated, will move to genAIExample in future)

```bash
# for langchain
cd comps/dataprep/redis/langchain/docker
# for llama_index
cd comps/dataprep/redis/llama_index/docker
docker compose -f docker-compose-dataprep-redis.yaml up -d
```

# 🚀3. Status Microservice

```bash
docker container logs -f dataprep-redis-server
```

# 🚀4. Consume Microservice

Once document preparation microservice for Redis is started, user can use below command to invoke the microservice to convert the document to embedding and save to the database.

Make sure the file path after `files=@` is correct.

- Single file upload

```bash
curl -X POST \
    -H "Content-Type: multipart/form-data" \
    -F "files=@./file1.txt" \
    http://localhost:6007/v1/dataprep
```

You can specify chunk_size and chunk_size by the following commands.

```bash
curl -X POST \
    -H "Content-Type: multipart/form-data" \
    -F "files=@./file1.txt" \
    -F "chunk_size=1500" \
    -F "chunk_overlap=100" \
    http://localhost:6007/v1/dataprep
```

We support table extraction from pdf documents. You can specify process_table and table_strategy by the following commands. "table_strategy" refers to the strategies to understand tables for table retrieval. As the setting progresses from "fast" to "hq" to "llm," the focus shifts towards deeper table understanding at the expense of processing speed. The default strategy is "fast".

Note: If you specify "table_strategy=llm", You should first start TGI Service, please refer to 1.2.1, 1.3.1 in https://github.com/opea-project/GenAIComps/tree/main/comps/llms/README.md, and then `export TGI_LLM_ENDPOINT="http://${your_ip}:8008"`.

```bash
curl -X POST \
    -H "Content-Type: multipart/form-data" \
    -F "files=@./your_file.pdf" \
    -F "process_table=true" \
    -F "table_strategy=hq" \
    http://localhost:6007/v1/dataprep
```

- Multiple file upload

```bash
curl -X POST \
    -H "Content-Type: multipart/form-data" \
    -F "files=@./file1.txt" \
    -F "files=@./file2.txt" \
    -F "files=@./file3.txt" \
    http://localhost:6007/v1/dataprep
```

- Links upload (not supported for llama_index now)

```bash
curl -X POST \
    -F 'link_list=["https://www.ces.tech/"]' \
    http://localhost:6007/v1/dataprep
```

or

```python
import requests
import json

proxies = {"http": ""}
url = "http://localhost:6007/v1/dataprep"
urls = [
    "https://towardsdatascience.com/no-gpu-no-party-fine-tune-bert-for-sentiment-analysis-with-vertex-ai-custom-jobs-d8fc410e908b?source=rss----7f60cf5620c9---4"
]
payload = {"link_list": json.dumps(urls)}

try:
    resp = requests.post(url=url, data=payload, proxies=proxies)
    print(resp.text)
    resp.raise_for_status()  # Raise an exception for unsuccessful HTTP status codes
    print("Request successful!")
except requests.exceptions.RequestException as e:
    print("An error occurred:", e)
```
