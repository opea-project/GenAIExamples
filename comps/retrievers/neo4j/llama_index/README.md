# Retriever Microservice with Neo4J

This retrieval microservice is intended for use in GraphRAG pipeline and assumes a GraphRAGStore containing document graph, entity_info and Community Symmaries already exist. Please refer to the GenAIExamples/GraphRAG example.

Retrieval follows these steps:

- Uses similarty to find the relevant entities to the input query. Retrieval is done over the neo4j index that natively supports embeddings.
- Uses Cypher queries to retrieve the community summaries for all the communities the entities belong to.
- Generates a partial answer to the query for each community summary. This will later be used as context to generate a final query response. Please refer to [GenAIExamples/GraphRAG](https://github.com/opea-project/GenAIExamples).

## 🚀Start Microservice with Docker

### 1. Build Docker Image

```bash
cd ../../
docker build -t opea/retriever-community-answers-neo4j:latest --build-arg https_proxy=$https_proxy --build-arg http_proxy=$http_proxy -f comps/retrievers/neo4j/llama_index/Dockerfile .
```

### 2. Setup Environment Variables

```bash
# Set private environment settings
export host_ip=${your_hostname IP}  # local IP
export no_proxy=$no_proxy,${host_ip}  # important to add {host_ip} for containers communication
export http_proxy=${your_http_proxy}
export https_proxy=${your_http_proxy}
export NEO4J_URI=${your_neo4j_url}
export NEO4J_USERNAME=${your_neo4j_username}
export NEO4J_PASSWORD=${your_neo4j_password}
export PYTHONPATH=${path_to_comps}
export OPENAI_KEY=${your_openai_api_key}  # optional, when not provided will use smaller models TGI/TEI
export HUGGINGFACEHUB_API_TOKEN=${your_hf_token}
# set additional environment settings
source ./set_env.sh
```

### 3. Run Docker with Docker Compose

Docker compose will start 5 microservices: retriever-neo4j-llamaindex, dataprep-neo4j-llamaindex, neo4j-apoc, tgi-gaudi-service and tei-embedding-service. Neo4j database supports embeddings natively so we do not need a separate vector store. Checkout the blog [Introducing the Property Graph Index: A Powerful New Way to Build Knowledge Graphs with LLMs](https://www.llamaindex.ai/blog/introducing-the-property-graph-index-a-powerful-new-way-to-build-knowledge-graphs-with-llms) for a better understanding of Property Graph Store and Index.

```bash
cd comps/retrievers/neo4j/llama_index
docker compose -f compose.yaml up -d
```

## Invoke Microservice

### 3.1 Check Service Status

```bash
curl http://${host_ip}:6009/v1/health_check \
  -X GET \
  -H 'Content-Type: application/json'
```

### 3.2 Consume Retriever Service

If OPEN_AI_KEY is provided it will use OPENAI endpoints for LLM and Embeddings otherwise will use TGI and TEI endpoints. If a model name not provided in the request it will use the default specified by the set_env.sh script.

```bash
curl -X POST http://${host_ip}:6009/v1/retrieval \
  -H "Content-Type: application/json" \
  -d '{"model": "gpt-3.5-turbo","messages": [{"role": "user","content": "Who is John Brady and has he had any confrontations?"}]}'
```
