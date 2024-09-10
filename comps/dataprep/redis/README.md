# Dataprep Microservice with Redis

We have provided dataprep microservice for multimodal data input (e.g., text and image) [here](../../multimodal/redis/langchain/README.md).

For dataprep microservice for text input, we provide here two frameworks: `Langchain` and `LlamaIndex`. We also provide `Langchain_ray` which uses ray to parallel the data prep for multi-file performance improvement(observed 5x - 15x speedup by processing 1000 files/links.).

We organized these two folders in the same way, so you can use either framework for dataprep microservice with the following constructions.

## 🚀1. Start Microservice with Python（Option 1）

### 1.1 Install Requirements

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

### 1.2 Start Redis Stack Server

Please refer to this [readme](../../../vectorstores/redis/README.md).

### 1.3 Setup Environment Variables

```bash
export REDIS_URL="redis://${your_ip}:6379"
export INDEX_NAME=${your_index_name}
export PYTHONPATH=${path_to_comps}
```

### 1.4 Start Embedding Service

First, you need to start a TEI service.

```bash
your_port=6006
model="BAAI/bge-base-en-v1.5"
docker run -p $your_port:80 -v ./data:/data --name tei_server -e http_proxy=$http_proxy -e https_proxy=$https_proxy --pull always ghcr.io/huggingface/text-embeddings-inference:cpu-1.5 --model-id $model
```

Then you need to test your TEI service using the following commands:

```bash
curl localhost:$your_port/embed \
    -X POST \
    -d '{"inputs":"What is Deep Learning?"}' \
    -H 'Content-Type: application/json'
```

After checking that it works, set up environment variables.

```bash
export TEI_ENDPOINT="http://localhost:$your_port"
```

### 1.4 Start Document Preparation Microservice for Redis with Python Script

Start document preparation microservice for Redis with below command.

- option 1: Start single-process version (for 1-10 files processing)

```bash
cd langchain
python prepare_doc_redis.py
```

- option 2: Start multi-process version (for >10 files processing)

```bash
cd langchain_ray
python prepare_doc_redis_on_ray.py
```

## 🚀2. Start Microservice with Docker (Option 2)

### 2.1 Start Redis Stack Server

Please refer to this [readme](../../../vectorstores/redis/README.md).

### 2.2 Setup Environment Variables

```bash
export EMBEDDING_MODEL_ID="BAAI/bge-base-en-v1.5"
export TEI_ENDPOINT="http://${your_ip}:6006"
export REDIS_URL="redis://${your_ip}:6379"
export INDEX_NAME=${your_index_name}
export HUGGINGFACEHUB_API_TOKEN=${your_hf_api_token}
```

### 2.3 Build Docker Image

- Build docker image with langchain

- option 1: Start single-process version (for 1-10 files processing)

```bash
cd ../../../
docker build -t opea/dataprep-redis:latest --build-arg https_proxy=$https_proxy --build-arg http_proxy=$http_proxy -f comps/dataprep/redis/langchain/Dockerfile .
```

- Build docker image with llama_index

```bash
cd ../../../
docker build -t opea/dataprep-redis:latest --build-arg https_proxy=$https_proxy --build-arg http_proxy=$http_proxy -f comps/dataprep/redis/llama_index/Dockerfile .
```

- option 2: Start multi-process version (for >10 files processing)

```bash
cd ../../../../
docker build -t opea/dataprep-on-ray-redis:latest --build-arg https_proxy=$https_proxy --build-arg http_proxy=$http_proxy -f comps/dataprep/redis/langchain_ray/Dockerfile .
```

### 2.4 Run Docker with CLI (Option A)

- option 1: Start single-process version (for 1-10 files processing)

```bash
docker run -d --name="dataprep-redis-server" -p 6007:6007 --runtime=runc --ipc=host -e http_proxy=$http_proxy -e https_proxy=$https_proxy -e REDIS_URL=$REDIS_URL -e INDEX_NAME=$INDEX_NAME -e TEI_ENDPOINT=$TEI_ENDPOINT -e HUGGINGFACEHUB_API_TOKEN=$HUGGINGFACEHUB_API_TOKEN opea/dataprep-redis:latest
```

- option 2: Start multi-process version (for >10 files processing)

```bash
docker run -d --name="dataprep-redis-server" -p 6007:6007 --runtime=runc --ipc=host -e http_proxy=$http_proxy -e https_proxy=$https_proxy -e REDIS_URL=$REDIS_URL -e INDEX_NAME=$INDEX_NAME -e TEI_ENDPOINT=$TEI_ENDPOINT -e HUGGINGFACEHUB_API_TOKEN=$HUGGINGFACEHUB_API_TOKEN -e TIMEOUT_SECONDS=600 opea/dataprep-on-ray-redis:latest
```

### 2.5 Run with Docker Compose (Option B - deprecated, will move to genAIExample in future)

```bash
# for langchain
cd comps/dataprep/redis/langchain
# for langchain_ray
cd comps/dataprep/redis/langchain_ray
# for llama_index
cd comps/dataprep/redis/llama_index
# common command
docker compose -f docker-compose-dataprep-redis.yaml up -d
```

## 🚀3. Status Microservice

```bash
docker container logs -f dataprep-redis-server
```

## 🚀4. Consume Microservice

### 4.1 Consume Upload API

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

### 4.2 Consume get_file API

To get uploaded file structures, use the following command:

```bash
curl -X POST \
    -H "Content-Type: application/json" \
    http://localhost:6007/v1/dataprep/get_file
```

Then you will get the response JSON like this:

```json
[
  {
    "name": "uploaded_file_1.txt",
    "id": "uploaded_file_1.txt",
    "type": "File",
    "parent": ""
  },
  {
    "name": "uploaded_file_2.txt",
    "id": "uploaded_file_2.txt",
    "type": "File",
    "parent": ""
  }
]
```

### 4.3 Consume delete_file API

To delete uploaded file/link, use the following command.

The `file_path` here should be the `id` get from `/v1/dataprep/get_file` API.

```bash
# delete link
curl -X POST \
    -H "Content-Type: application/json" \
    -d '{"file_path": "https://www.ces.tech/.txt"}' \
    http://localhost:6007/v1/dataprep/delete_file

# delete file
curl -X POST \
    -H "Content-Type: application/json" \
    -d '{"file_path": "uploaded_file_1.txt"}' \
    http://localhost:6007/v1/dataprep/delete_file

# delete all files and links
curl -X POST \
    -H "Content-Type: application/json" \
    -d '{"file_path": "all"}' \
    http://localhost:6007/v1/dataprep/delete_file
```
