# Dataprep Microservice with Qdrant

## 🚀Start Microservice with Python

### Install Requirements

```bash
pip install -r requirements.txt
apt-get install tesseract-ocr -y
apt-get install libtesseract-dev -y
apt-get install poppler-utils -y
```

### Start Qdrant Server

Please refer to this [readme](../../vectorstores/langchain/qdrant/README.md).

### Setup Environment Variables

```bash
export no_proxy=${your_no_proxy}
export http_proxy=${your_http_proxy}
export https_proxy=${your_http_proxy}
export QDRANT=${host_ip}
export QDRANT_PORT=6333
export COLLECTION_NAME=${your_collection_name}
export PYTHONPATH=${path_to_comps}
```

### Start Document Preparation Microservice for Qdrant with Python Script

Start document preparation microservice for Qdrant with below command.

```bash
python prepare_doc_qdrant.py
```

## 🚀Start Microservice with Docker

### Build Docker Image

```bash
cd ../../../../
docker build -t opea/dataprep-qdrant:latest --build-arg https_proxy=$https_proxy --build-arg http_proxy=$http_proxy -f comps/dataprep/qdrant/docker/Dockerfile .
```

### Run Docker with CLI

```bash
docker run -d --name="dataprep-qdrant-server" -p 6007:6007 --ipc=host -e http_proxy=$http_proxy -e https_proxy=$https_proxy opea/dataprep-qdrant:latest
```

### Setup Environment Variables

```bash
export http_proxy=${your_http_proxy}
export https_proxy=${your_http_proxy}
export QDRANT_HOST=${host_ip}
export QDRANT_PORT=6333
export COLLECTION_NAME=${your_collection_name}
```

### Run Docker with Docker Compose

```bash
cd comps/dataprep/qdrant/docker
docker compose -f docker-compose-dataprep-qdrant.yaml up -d
```

## Invoke Microservice

Once document preparation microservice for Qdrant is started, user can use below command to invoke the microservice to convert the document to embedding and save to the database.

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
