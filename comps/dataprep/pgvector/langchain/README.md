# Dataprep Microservice with PGVector

## 🚀1. Start Microservice with Python（Option 1）

### 1.1 Install Requirements

```bash
pip install -r requirements.txt
```

### 1.2 Setup Environment Variables

```bash
export PG_CONNECTION_STRING=postgresql+psycopg2://testuser:testpwd@${your_ip}:5432/vectordb
export INDEX_NAME=${your_index_name}
```

### 1.3 Start PGVector

Please refer to this [readme](../../../vectorstores/pgvector/README.md).

### 1.4 Start Document Preparation Microservice for PGVector with Python Script

Start document preparation microservice for PGVector with below command.

```bash
python prepare_doc_pgvector.py
```

## 🚀2. Start Microservice with Docker (Option 2)

### 2.1 Start PGVector

Please refer to this [readme](../../../vectorstores/pgvector/README.md).

### 2.2 Setup Environment Variables

```bash
export PG_CONNECTION_STRING=postgresql+psycopg2://testuser:testpwd@${your_ip}:5432/vectordb
export INDEX_NAME=${your_index_name}
```

### 2.3 Build Docker Image

```bash
cd GenAIComps
docker build -t opea/dataprep-pgvector:latest --build-arg https_proxy=$https_proxy --build-arg http_proxy=$http_proxy -f comps/dataprep/pgvector/langchain/Dockerfile .
```

### 2.4 Run Docker with CLI (Option A)

```bash
docker run  --name="dataprep-pgvector" -p 6007:6007 --ipc=host -e http_proxy=$http_proxy -e https_proxy=$https_proxy -e PG_CONNECTION_STRING=$PG_CONNECTION_STRING  -e INDEX_NAME=$INDEX_NAME -e TEI_ENDPOINT=$TEI_ENDPOINT opea/dataprep-pgvector:latest
```

### 2.5 Run with Docker Compose (Option B)

```bash
cd comps/dataprep/pgvector/langchain
docker compose -f docker-compose-dataprep-pgvector.yaml up -d
```

## 🚀3. Consume Microservice

### 3.1 Consume Upload API

Once document preparation microservice for PGVector is started, user can use below command to invoke the microservice to convert the document to embedding and save to the database.

```bash
curl -X POST \
    -H "Content-Type: application/json" \
    -d '{"path":"/path/to/document"}' \
    http://localhost:6007/v1/dataprep
```

### 3.2 Consume get_file API

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
