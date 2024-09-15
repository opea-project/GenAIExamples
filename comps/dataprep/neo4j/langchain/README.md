# Dataprep Microservice with Neo4J

## 🚀Start Microservice with Python

### Install Requirements

```bash
pip install -r requirements.txt
apt-get install libtesseract-dev -y
apt-get install poppler-utils -y
```

### Start Neo4J Server

To launch Neo4j locally, first ensure you have docker installed. Then, you can launch the database with the following docker command.

```bash
docker run \
    -p 7474:7474 -p 7687:7687 \
    -v $PWD/data:/data -v $PWD/plugins:/plugins \
    --name neo4j-apoc \
    -d \
    -e NEO4J_AUTH=neo4j/password \
    -e NEO4J_PLUGINS=\[\"apoc\"\]  \
    neo4j:latest
```

### Setup Environment Variables

```bash
export no_proxy=${your_no_proxy}
export http_proxy=${your_http_proxy}
export https_proxy=${your_http_proxy}
export NEO4J_URI=${your_neo4j_url}
export NEO4J_USERNAME=${your_neo4j_username}
export NEO4J_PASSWORD=${your_neo4j_password}
export PYTHONPATH=${path_to_comps}
```

### Start Document Preparation Microservice for Neo4J with Python Script

Start document preparation microservice for Neo4J with below command.

```bash
python prepare_doc_neo4j.py
```

## 🚀Start Microservice with Docker

### Build Docker Image

```bash
cd ../../../../
docker build -t opea/dataprep-neo4j:latest --build-arg https_proxy=$https_proxy --build-arg http_proxy=$http_proxy -f comps/dataprep/neo4j/langchain/Dockerfile .
```

### Run Docker with CLI

```bash
docker run -d --name="dataprep-neo4j-server" -p 6007:6007 --ipc=host -e http_proxy=$http_proxy -e https_proxy=$https_proxy opea/dataprep-neo4j:latest
```

### Setup Environment Variables

```bash
export no_proxy=${your_no_proxy}
export http_proxy=${your_http_proxy}
export https_proxy=${your_http_proxy}
export NEO4J_URI=${your_neo4j_url}
export NEO4J_USERNAME=${your_neo4j_username}
export NEO4J_PASSWORD=${your_neo4j_password}
```

### Run Docker with Docker Compose

```bash
cd comps/dataprep/neo4j/langchain
docker compose -f docker-compose-dataprep-neo4j.yaml up -d
```

## Invoke Microservice

Once document preparation microservice for Neo4J is started, user can use below command to invoke the microservice to convert the document to embedding and save to the database.

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

For ensure the quality and comprehensiveness of the extracted entities, we recommend to use `gpt-4o` as the default model for parsing the document. To enable the openai service, please `export OPENAI_KEY=xxxx` before using this services.

```bash
curl -X POST \
    -H "Content-Type: multipart/form-data" \
    -F "files=@./your_file.pdf" \
    -F "process_table=true" \
    -F "table_strategy=hq" \
    http://localhost:6007/v1/dataprep
```
