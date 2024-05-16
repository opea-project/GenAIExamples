# 🚀Start Microservice with Python

## Install Requirements

```bash
pip install -r requirements.txt
```

## Start Qdrant server

Please refer to this [readme](../../../vectorstores/langchain/qdrant/README.md).

## Start document preparation microservice for Qdrant with Python Script

Start document preparation microservice for Qdrant with below command.

```bash
python prepare_doc_qdrant.py
```

# 🚀Start Microservice with Docker

## Build Docker Image

```bash
cd ../../
docker build -t opea/gen-ai-comps:dataprep-qdrant-xeon-server --build-arg https_proxy=$https_proxy --build-arg http_proxy=$http_proxy -f comps/dataprep/langchain/qdrant/docker/Dockerfile .
```

## Run Docker with CLI

```bash
docker run -d --name="dataprep-qdrant-server" -p 8000:8000 --ipc=host -e http_proxy=$http_proxy -e https_proxy=$https_proxy opea/gen-ai-comps:dataprep-qdrant-xeon-server
```

## Run Docker with Docker Compose

```bash
cd docker
docker compose -f docker-compose-dataprep-qdrant.yaml up -d
```

# Invoke Microservices

Once document preparation microservice for Qdrant is started, user can use below command to invoke the microservice to convert the document to embedding and save to the database.

```bash
curl -X POST -H "Content-Type: application/json" -d '{"path":"/path/to/document"}' http://localhost:6000/v1/dataprep
```
