# Retriever Microservice with Neo4J

## 🚀Start Microservice with Python

### Install Requirements

```bash
pip install -r requirements.txt
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
```

### Start Retriever Service

```bash
python retriever_neo4j.py
```

## 🚀Start Microservice with Docker

### Build Docker Image

```bash
cd ../../
docker build -t opea/retriever-neo4j:latest --build-arg https_proxy=$https_proxy --build-arg http_proxy=$http_proxy -f comps/retrievers/neo4j/langchain/Dockerfile .
```

### Run Docker with CLI

```bash
docker run -d --name="retriever-neo4j-server" -p 7000:7000 --ipc=host -e http_proxy=$http_proxy -e https_proxy=$https_proxy -e NEO4J_URI=${your_neo4j_host_ip}  opea/retriever-neo4j:latest
```

## 🚀3. Consume Retriever Service

### 3.1 Check Service Status

```bash
curl http://${your_ip}:7000/v1/health_check \
  -X GET \
  -H 'Content-Type: application/json'
```

### 3.2 Consume Embedding Service

To consume the Retriever Microservice, you can generate a mock embedding vector of length 768 with Python.

```bash
export your_embedding=$(python -c "import random; embedding = [random.uniform(-1, 1) for _ in range(768)]; print(embedding)")
curl http://${your_ip}:7000/v1/retrieval \
  -X POST \
  -d "{\"text\":\"What is the revenue of Nike in 2023?\",\"embedding\":${your_embedding}}" \
  -H 'Content-Type: application/json'
```

You can set the parameters for the retriever.

```bash
export your_embedding=$(python -c "import random; embedding = [random.uniform(-1, 1) for _ in range(768)]; print(embedding)")
curl http://localhost:7000/v1/retrieval \
  -X POST \
  -d "{\"text\":\"What is the revenue of Nike in 2023?\",\"embedding\":${your_embedding},\"search_type\":\"similarity\", \"k\":4}" \
  -H 'Content-Type: application/json'
```

```bash
export your_embedding=$(python -c "import random; embedding = [random.uniform(-1, 1) for _ in range(768)]; print(embedding)")
curl http://localhost:7000/v1/retrieval \
  -X POST \
  -d "{\"text\":\"What is the revenue of Nike in 2023?\",\"embedding\":${your_embedding},\"search_type\":\"similarity_distance_threshold\", \"k\":4, \"distance_threshold\":1.0}" \
  -H 'Content-Type: application/json'
```

```bash
export your_embedding=$(python -c "import random; embedding = [random.uniform(-1, 1) for _ in range(768)]; print(embedding)")
curl http://localhost:7000/v1/retrieval \
  -X POST \
  -d "{\"text\":\"What is the revenue of Nike in 2023?\",\"embedding\":${your_embedding},\"search_type\":\"similarity_score_threshold\", \"k\":4, \"score_threshold\":0.2}" \
  -H 'Content-Type: application/json'
```

```bash
export your_embedding=$(python -c "import random; embedding = [random.uniform(-1, 1) for _ in range(768)]; print(embedding)")
curl http://localhost:7000/v1/retrieval \
  -X POST \
  -d "{\"text\":\"What is the revenue of Nike in 2023?\",\"embedding\":${your_embedding},\"search_type\":\"mmr\", \"k\":4, \"fetch_k\":20, \"lambda_mult\":0.5}" \
  -H 'Content-Type: application/json'
```
