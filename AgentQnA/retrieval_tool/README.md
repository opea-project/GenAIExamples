# Retrieval tool for agent

The retrieval tool in this example is an OPEA megaservice that is comprised of a query embedder, a document retriever and a document reranker.

## Launch microservices
```
bash launch_retrieval_tool.sh
```

## Index data into vector database

In this example, we use an example jsonl file to ingest example documents into the vector database. For more ways to ingest data and the type of documents supported by OPEA dataprep microservices, please refer to the documentation in the opea-project/GenAIComps repo.

1. create a conda env
2. Run commands below

```
bash run_ingest_data.sh
```

## Validate services

```
export ip_address=$(hostname -I | awk '{print $1}')
curl http://${ip_address}:8889/v1/retrievaltool -X POST -H "Content-Type: application/json" -d '{
     "text": "Taylor Swift hometown"
    }'
```

## Consume retrieval tool

The endpoint for the retrieval tool is

```
http://${ip_address}:8889/v1/retrievaltool
```
