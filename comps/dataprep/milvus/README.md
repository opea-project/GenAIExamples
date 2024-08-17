# Dataprep Microservice with Milvus

## 🚀Start Microservice with Python

### Install Requirements

```bash
pip install -r requirements.txt
apt-get install tesseract-ocr -y
apt-get install libtesseract-dev -y
apt-get install poppler-utils -y
```

### Start Milvus Server

Please refer to this [readme](../../../vectorstores/langchain/milvus/README.md).

### Setup Environment Variables

```bash
export no_proxy=${your_no_proxy}
export http_proxy=${your_http_proxy}
export https_proxy=${your_http_proxy}
export MILVUS=${your_milvus_host_ip}
export MILVUS_PORT=19530
export COLLECTION_NAME=${your_collection_name}
export MOSEC_EMBEDDING_ENDPOINT=${your_embedding_endpoint}
```

### Start Document Preparation Microservice for Milvus with Python Script

Start document preparation microservice for Milvus with below command.

```bash
python prepare_doc_milvus.py
```

## 🚀Start Microservice with Docker

### Build Docker Image

```bash
cd ../../../../
docker build -t opea/dataprep-milvus:latest --build-arg https_proxy=$https_proxy --build-arg http_proxy=$http_proxy --build-arg no_proxy=$no_proxy -f comps/dataprep/milvus/docker/Dockerfile .
```

### Run Docker with CLI

```bash
docker run -d --name="dataprep-milvus-server" -p 6010:6010 --ipc=host -e http_proxy=$http_proxy -e https_proxy=$https_proxy -e no_proxy=$no_proxy -e MOSEC_EMBEDDING_ENDPOINT=${your_embedding_endpoint} -e MILVUS=${your_milvus_host_ip} opea/dataprep-milvus:latest
```

## Invoke Microservice

Once document preparation microservice for Milvus is started, user can use below command to invoke the microservice to convert the document to embedding and save to the database.

Make sure the file path after `files=@` is correct.

- Single file upload

```bash
curl -X POST \
    -H "Content-Type: multipart/form-data" \
    -F "files=@./file.pdf" \
    http://localhost:6010/v1/dataprep
```

You can specify chunk_size and chunk_size by the following commands.

```bash
curl -X POST \
    -H "Content-Type: multipart/form-data" \
    -F "files=@./file.pdf" \
    -F "chunk_size=1500" \
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
