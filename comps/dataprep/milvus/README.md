# Dataprep Microservice with Milvus

# 🚀Start Microservice with Python

## Install Requirements

```bash
pip install -r requirements.txt
```

## Start Milvus Server

Please refer to this [readme](../../../vectorstores/langchain/milvus/README.md).

## Setup Environment Variables

```bash
export http_proxy=${your_http_proxy}
export https_proxy=${your_http_proxy}
export MILVUS=${your_milvus_host_ip}
export MILVUS_PORT=19530
export COLLECTION_NAME=${your_collection_name}
export TEI_EMBEDDING_ENDPOINT=${your_tei_endpoint}
```

## Start Document Preparation Microservice for Milvus with Python Script

Start document preparation microservice for Milvus with below command.

```bash
python prepare_doc_milvus.py
```

# 🚀Start Microservice with Docker

## Build Docker Image

```bash
cd ../../../../
docker build -t opea/dataprep-milvus:latest --build-arg https_proxy=$https_proxy --build-arg http_proxy=$http_proxy -f comps/dataprep/milvus/docker/Dockerfile .
```

## Run Docker with CLI

```bash
docker run -d --name="dataprep-milvus-server" -p 6010:6010 --ipc=host -v /your_document_path/:/home/user/doc -e http_proxy=$http_proxy -e https_proxy=$https_proxy -e TEI_EMBEDDING_ENDPOINT=${your_tei_endpoint} -e MILVUS=${your_milvus_host_ip} opea/dataprep-milvus:latest
```

# Invoke Microservice

Once document preparation microservice for Qdrant is started, user can use below command to invoke the microservice to convert the document to embedding and save to the database.

```bash
curl -X POST -H "Content-Type: application/json" -d '{"path":"/home/user/doc/your_document_name"}' http://localhost:6010/v1/dataprep
```
