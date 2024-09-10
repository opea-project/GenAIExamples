# Dataprep Microservice with Pinecone

## 🚀Start Microservice with Python

### Install Requirements

```bash
pip install -r requirements.txt
```

### Start Pinecone Server

Please refer to this [readme](../../../vectorstores/pinecone/README.md).

### Setup Environment Variables

```bash
export http_proxy=${your_http_proxy}
export https_proxy=${your_http_proxy}
export PINECONE_API_KEY=${PINECONE_API_KEY}
export PINECONE_INDEX_NAME=${PINECONE_INDEX_NAME}
```

### Start Document Preparation Microservice for Pinecone with Python Script

Start document preparation microservice for Pinecone with below command.

```bash
python prepare_doc_pinecone.py
```

## 🚀Start Microservice with Docker

### Build Docker Image

```bash
cd ../../../../
docker build -t opea/dataprep-pinecone:latest --build-arg https_proxy=$https_proxy --build-arg http_proxy=$http_proxy -f comps/dataprep/pinecone/langchain/Dockerfile .
```

### Run Docker with CLI

```bash
docker run -d --name="dataprep-pinecone-server" -p 6000:6000 --ipc=host -e http_proxy=$http_proxy -e https_proxy=$https_proxy opea/dataprep-pinecone:latest
```

### Setup Environment Variables

```bash
export http_proxy=${your_http_proxy}
export https_proxy=${your_http_proxy}
export PINECONE_API_KEY=${PINECONE_API_KEY}
export PINECONE_INDEX_NAME=${PINECONE_INDEX_NAME}
```

### Run Docker with Docker Compose

```bash
cd comps/dataprep/pinecone/langchain
docker compose -f docker-compose-dataprep-pinecone.yaml up -d
```

## Invoke Microservice

Once document preparation microservice for Pinecone is started, user can use below command to invoke the microservice to convert the document to embedding and save to the database.

```bash
curl -X POST -H "Content-Type: application/json" -d '{"path":"/path/to/document"}' http://localhost:6000/v1/dataprep
```
