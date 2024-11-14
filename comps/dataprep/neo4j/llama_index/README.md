# Dataprep Microservice with Neo4J

This Dataprep microservice performs:

- Graph extraction (entities, relationships and descripttions) using LLM
- Performs hierarchical_leiden clustering to identify communities in the knowledge graph
- Generates a community symmary for each community
- Stores all of the above in Neo4j Graph DB

This microservice follows the graphRAG approached defined by Microsoft paper ["From Local to Global: A Graph RAG Approach to Query-Focused Summarization"](https://www.microsoft.com/en-us/research/publication/from-local-to-global-a-graph-rag-approach-to-query-focused-summarization/) with some differences such as: 1) only level zero cluster summaries are leveraged, 2) The input context to the final answer generation is trimmed to fit maximum context length.

This dataprep microservice ingests the input files and uses LLM (TGI or OpenAI model when OPENAI_API_KEY is set) to extract entities, relationships and descriptions of those to build a graph-based text index.

## Setup Environment Variables

```bash
# Manually set private environment settings
export host_ip=${your_hostname IP}  # local IP
export no_proxy=$no_proxy,${host_ip}  # important to add {host_ip} for containers communication
export http_proxy=${your_http_proxy}
export https_proxy=${your_http_proxy}
export NEO4J_URI=${your_neo4j_url}
export NEO4J_USERNAME=${your_neo4j_username}
export NEO4J_PASSWORD=${your_neo4j_password}  # should match what was used in NEO4J_AUTH when running the neo4j-apoc
export PYTHONPATH=${path_to_comps}
export OPENAI_KEY=${your_openai_api_key}  # optional, when not provided will use smaller models TGI/TEI
export HUGGINGFACEHUB_API_TOKEN=${your_hf_token}
# set additional environment settings
source ./set_env.sh
```

## 🚀Start Microservice with Docker

### 1. Build Docker Image

```bash
cd ../../../../
docker build -t opea/dataprep-neo4j-llamaindex:latest --build-arg no_proxy=$no_proxy --build-arg https_proxy=$https_proxy --build-arg http_proxy=$http_proxy -f comps/dataprep/neo4j/llama_index/Dockerfile .
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

Docker compose will start 4 microservices: dataprep-neo4j-llamaindex, neo4j-apoc, tgi-gaudi-service and tei-embedding-service. The reason TGI and TEI are needed is because dataprep relies on LLM to extract entities and relationships from text to build the graph and Neo4j Property Graph Index. Neo4j database supports embeddings natively so we do not need a separate vector store. Checkout the blog [Introducing the Property Graph Index: A Powerful New Way to Build Knowledge Graphs with LLMs](https://www.llamaindex.ai/blog/introducing-the-property-graph-index-a-powerful-new-way-to-build-knowledge-graphs-with-llms) for a better understanding of Property Graph Store and Index.

```bash
cd comps/dataprep/neo4j/llama_index
docker compose -f compose.yaml up -d
```

## Invoke Microservice

Once document preparation microservice for Neo4J is started, user can use below command to invoke the microservice to convert the document to embedding and save to the database.

```bash
curl -X POST \
    -H "Content-Type: multipart/form-data" \
    -F "files=@./file1.txt" \
    http://${host_ip}:6004/v1/dataprep
```

You can specify chunk_size and chunk_size by the following commands.

```bash
curl -X POST \
    -H "Content-Type: multipart/form-data" \
    -F "files=@./file1.txt" \
    -F "chunk_size=1500" \
    -F "chunk_overlap=100" \
    http://${host_ip}:6004/v1/dataprep
```

Please note that clustering of extracted entities and summarization happens in this data preparation step. The result of this is:

- Large processing time for large dataset. An LLM call is done to summarize each cluster which may result in large volume of LLM calls
- Need to clean graph GB entity_info and Cluster if dataprep is run multiple times since the resulting cluster numbering will differ between consecutive calls and will corrupt the results.

We support table extraction from pdf documents. You can specify process_table and table_strategy by the following commands. "table_strategy" refers to the strategies to understand tables for table retrieval. As the setting progresses from "fast" to "hq" to "llm," the focus shifts towards deeper table understanding at the expense of processing speed. The default strategy is "fast".

Note: If you specify "table_strategy=llm" TGI service will be used.

For ensure the quality and comprehensiveness of the extracted entities, we recommend to use `gpt-4o` as the default model for parsing the document. To enable the openai service, please `export OPENAI_KEY=xxxx` before using this services.

```bash
curl -X POST \
    -H "Content-Type: multipart/form-data" \
    -F "files=@./your_file.pdf" \
    -F "process_table=true" \
    -F "table_strategy=hq" \
    http://localhost:6004/v1/dataprep
```
