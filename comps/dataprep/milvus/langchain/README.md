# Dataprep Microservice with Milvus

## 🚀1. Start Microservice with Python (Option 1)

### 1.1 Requirements

```bash
pip install -r requirements.txt
apt-get install tesseract-ocr -y
apt-get install libtesseract-dev -y
apt-get install poppler-utils -y
```

### 1.2 Start Milvus Server

Please refer to this [readme](../../../vectorstores/milvus/README.md).

### 1.3 Setup Environment Variables

```bash
export no_proxy=${your_no_proxy}
export http_proxy=${your_http_proxy}
export https_proxy=${your_http_proxy}
export MILVUS=${your_milvus_host_ip}
export MILVUS_PORT=19530
export COLLECTION_NAME=${your_collection_name}
export MOSEC_EMBEDDING_ENDPOINT=${your_embedding_endpoint}
```

### 1.4 Start Mosec Embedding Service

First, you need to build a mosec embedding serving docker image.

```bash
cd ../../..
docker build --build-arg http_proxy=$http_proxy --build-arg https_proxy=$https_proxy -t opea/embedding-mosec-endpoint:latest -f comps/embeddings/mosec/langchain/dependency/Dockerfile .
```

Then start the mosec embedding server.

```bash
your_port=6010
docker run -d --name="embedding-mosec-endpoint" -p $your_port:8000  opea/embedding-mosec-endpoint:latest
```

Setup environment variables:

```bash
export MOSEC_EMBEDDING_ENDPOINT="http://localhost:$your_port"
export MILVUS=${your_host_ip}
```

### 1.5 Start Document Preparation Microservice for Milvus with Python Script

Start document preparation microservice for Milvus with below command.

```bash
python prepare_doc_milvus.py
```

## 🚀2. Start Microservice with Docker (Option 2)

### 2.1 Start Milvus Server

Please refer to this [readme](../../../vectorstores/milvus/README.md).

### 2.2 Build Docker Image

```bash
cd ../../..
# build mosec embedding docker image
docker build --build-arg http_proxy=$http_proxy --build-arg https_proxy=$https_proxy -t opea/embedding-langchain-mosec-endpoint:latest -f comps/embeddings/mosec/langchain/dependency/Dockerfile .
# build dataprep milvus docker image
docker build -t opea/dataprep-milvus:latest --build-arg https_proxy=$https_proxy --build-arg http_proxy=$http_proxy --build-arg no_proxy=$no_proxy -f comps/dataprep/milvus/langchain/Dockerfile .
```

### 2.3 Setup Environment Variables

```bash
export MOSEC_EMBEDDING_ENDPOINT="http://localhost:$your_port"
export MILVUS=${your_host_ip}
```

### 2.3 Run Docker with CLI (Option A)

```bash
docker run -d --name="dataprep-milvus-server" -p 6010:6010 --ipc=host -e http_proxy=$http_proxy -e https_proxy=$https_proxy -e no_proxy=$no_proxy -e MOSEC_EMBEDDING_ENDPOINT=${MOSEC_EMBEDDING_ENDPOINT} -e MILVUS=${MILVUS} opea/dataprep-milvus:latest
```

### 2.4 Run with Docker Compose (Option B)

```bash
cd docker
docker compose -f docker-compose-dataprep-milvus.yaml up -d
```

## 🚀3. Consume Microservice

### 3.1 Consume Upload API

Once document preparation microservice for Milvus is started, user can use below command to invoke the microservice to convert the document to embedding and save to the database.

Make sure the file path after `files=@` is correct.

- Single file upload

```bash
curl -X POST \
    -H "Content-Type: multipart/form-data" \
    -F "files=@./file.pdf" \
    http://localhost:6010/v1/dataprep
```

You can specify chunk_size and chunk_size by the following commands. To avoid big chunks, pass a small chun_size like 500 as below (default 1500).

```bash
curl -X POST \
    -H "Content-Type: multipart/form-data" \
    -F "files=@./file.pdf" \
    -F "chunk_size=500" \
    -F "chunk_overlap=100" \
    http://localhost:6010/v1/dataprep
```

- Multiple file upload

```bash
curl -X POST \
    -H "Content-Type: multipart/form-data" \
    -F "files=@./file1.pdf" \
    -F "files=@./file2.pdf" \
    -F "files=@./file3.pdf" \
    http://localhost:6010/v1/dataprep
```

- Links upload (not supported for llama_index now)

```bash
curl -X POST \
    -F 'link_list=["https://www.ces.tech/"]' \
    http://localhost:6010/v1/dataprep
```

or

```python
import requests
import json

proxies = {"http": ""}
url = "http://localhost:6010/v1/dataprep"
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

We support table extraction from pdf documents. You can specify process_table and table_strategy by the following commands. "table_strategy" refers to the strategies to understand tables for table retrieval. As the setting progresses from "fast" to "hq" to "llm," the focus shifts towards deeper table understanding at the expense of processing speed. The default strategy is "fast".

Note: If you specify "table_strategy=llm", You should first start TGI Service, please refer to 1.2.1, 1.3.1 in https://github.com/opea-project/GenAIComps/tree/main/comps/llms/README.md, and then `export TGI_LLM_ENDPOINT="http://${your_ip}:8008"`.

```bash
curl -X POST -H "Content-Type: application/json" -d '{"path":"/home/user/doc/your_document_name","process_table":true,"table_strategy":"hq"}' http://localhost:6010/v1/dataprep
```

We support table extraction from pdf documents. You can specify process_table and table_strategy by the following commands. "table_strategy" refers to the strategies to understand tables for table retrieval. As the setting progresses from "fast" to "hq" to "llm," the focus shifts towards deeper table understanding at the expense of processing speed. The default strategy is "fast".

Note: If you specify "table_strategy=llm", You should first start TGI Service, please refer to 1.2.1, 1.3.1 in https://github.com/opea-project/GenAIComps/tree/main/comps/llms/README.md, and then `export TGI_LLM_ENDPOINT="http://${your_ip}:8008"`.

```bash
curl -X POST -H "Content-Type: application/json" -d '{"path":"/home/user/doc/your_document_name","process_table":true,"table_strategy":"hq"}' http://localhost:6010/v1/dataprep
```

### 3.2 Consume get_file API

To get uploaded file structures, use the following command:

```bash
curl -X POST \
    -H "Content-Type: application/json" \
    http://localhost:6010/v1/dataprep/get_file
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

### 3.3 Consume delete_file API

To delete uploaded file/link, use the following command.

The `file_path` here should be the `id` get from `/v1/dataprep/get_file` API.

```bash
# delete link
curl -X POST \
    -H "Content-Type: application/json" \
    -d '{"file_path": "https://www.ces.tech/.txt"}' \
    http://localhost:6010/v1/dataprep/delete_file

# delete file
curl -X POST \
    -H "Content-Type: application/json" \
    -d '{"file_path": "uploaded_file_1.txt"}' \
    http://localhost:6010/v1/dataprep/delete_file

# delete all files and links, will drop the entire db collection
curl -X POST \
    -H "Content-Type: application/json" \
    -d '{"file_path": "all"}' \
    http://localhost:6010/v1/dataprep/delete_file
```

## 🚀4. Troubleshooting

1. If you get errors from Mosec Embedding Endpoint like `cannot find this task, maybe it has expired` while uploading files, try to reduce the `chunk_size` in the curl command like below (the default chunk_size=1500).

   ```bash
   curl -X POST \
       -H "Content-Type: multipart/form-data" \
       -F "files=@./file.pdf" \
       -F "chunk_size=500" \
       http://localhost:6010/v1/dataprep
   ```
