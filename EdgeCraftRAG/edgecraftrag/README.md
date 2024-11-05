# Edge Craft Retrieval-Augmented Generation

Edge Craft RAG (EC-RAG) is a customizable, tunable and production-ready
Retrieval-Augmented Generation system for edge solutions. It is designed to
curate the RAG pipeline to meet hardware requirements at edge with garanteed
quality and performance.

## Quick Start Guide

### Run the server

```bash
pip install -r requirements.txt
python3 -m edgecraftrag.server
# Run Mega Service
python3 -m edgecraftrag.ecrag 
```

### ChatQnA with LLM Example (Command Line)

```bash
# Activate pipeline test_pipeline_education_case
curl -X POST http://127.0.0.1:16010/v1/settings/pipelines -H "Content-Type: application/json" -d @examples/test_pipeline_education_case.json | jq '.'

# Prepare data from directory
curl -X POST http://127.0.0.1:16010/v1/data -H "Content-Type: application/json" -d @examples/test_data_dir.json | jq '.'

# Query
curl -X POST http://127.0.0.1:16010/v1/chatqna -H "Content-Type: application/json" -d '{"messages":"最喜小儿亡赖，溪头卧剥莲蓬”中，亡赖的读音是什么？意思是什么？"}' | jq '.'

# Validate Mega Service
curl -X POST http://127.0.0.1:16011/v1/chatqna -H "Content-Type: application/json" -d '{"messages":"最喜小儿亡赖 ，溪头卧剥莲蓬”中，亡赖的读音是什么？意思是什么？","top_n":5, "max_tokens":512}' | jq '.'
```

### ChatQnA with LLM Example (UI)

```bash
cd edgecraftrag/ui
python3 -m ecragui
```

Open your browser, access [http://127.0.0.1:8082](http://127.0.0.1:8082)

> Your browser should be running on the same host of your console, otherwise you will need to access UI with your host domain name instead of 127.0.0.1.

## Pipeline Management

### Create a pipeline

```bash
curl -X POST http://127.0.0.1:16010/v1/settings/pipelines -H "Content-Type: application/json" -d @examples/test_pipeline.json | jq '.'
```
It will take some time to prepare the embedding model.

### Upload a text

```bash
curl -X POST http://127.0.0.1:16010/v1/data -H "Content-Type: application/json" -d @examples/test_data.json | jq '.'
```

### Provide a query to retrieve context with similarity search.

```bash
curl -X POST http://127.0.0.1:16010/v1/retrieval -H "Content-Type: application/json" -d @examples/test_query.json | jq '.'
```

### Create the second pipeline test2

```bash
curl -X POST http://127.0.0.1:16010/v1/settings/pipelines -H "Content-Type: application/json" -d @examples/test_pipeline2.json | jq '.'
```

### Check all pipelines

```bash
curl -X GET http://127.0.0.1:16010/v1/settings/pipelines -H "Content-Type: application/json" | jq '.'
```

### Compare similarity retrieval (test1) and keyword retrieval (test2)

```bash
# Activate pipeline test1
curl -X PATCH http://127.0.0.1:16010/v1/settings/pipelines/test1 -H "Content-Type: application/json" -d '{"active": "true"}' | jq '.'
# Similarity retrieval
curl -X POST http://127.0.0.1:16010/v1/retrieval -H "Content-Type: application/json" -d '{"messages":"number"}' | jq '.'

# Activate pipeline test2
curl -X PATCH http://127.0.0.1:16010/v1/settings/pipelines/test2 -H "Content-Type: application/json" -d '{"active": "true"}' | jq '.'
# Keyword retrieval
curl -X POST http://127.0.0.1:16010/v1/retrieval -H "Content-Type: application/json" -d '{"messages":"number"}' | jq '.'

```

## Model Management

### Load a model

```bash
curl -X POST http://127.0.0.1:16010/v1/settings/models -H "Content-Type: application/json" -d @examples/test_model_load.json | jq '.'
```
It will take some time to load the model.

### Check all models

```bash
curl -X GET http://127.0.0.1:16010/v1/settings/models -H "Content-Type: application/json" | jq '.'
```

### Update a model

```bash
curl -X PATCH http://127.0.0.1:16010/v1/settings/models/BAAI/bge-reranker-large -H "Content-Type: application/json" -d @examples/test_model_update.json | jq '.'
```

### Check a certain model

```bash
curl -X GET http://127.0.0.1:16010/v1/settings/models/BAAI/bge-reranker-large -H "Content-Type: application/json" | jq '.'
```

### Delete a model

```bash
curl -X DELETE http://127.0.0.1:16010/v1/settings/models/BAAI/bge-reranker-large -H "Content-Type: application/json" | jq '.'
```

## File Management

### Add a text

```bash
curl -X POST http://127.0.0.1:16010/v1/data -H "Content-Type: application/json" -d @examples/test_data.json | jq '.'
```

### Add files from existed file path

```bash
curl -X POST http://127.0.0.1:16010/v1/data -H "Content-Type: application/json" -d @examples/test_data_dir.json | jq '.'
curl -X POST http://127.0.0.1:16010/v1/data -H "Content-Type: application/json" -d @examples/test_data_file.json | jq '.'
```

### Check all files

```bash
curl -X GET http://127.0.0.1:16010/v1/data/files -H "Content-Type: application/json" | jq '.'
```

### Check one file

```bash
curl -X GET http://127.0.0.1:16010/v1/data/files/test2.docx -H "Content-Type: application/json" | jq '.'
```

### Delete a file

```bash
curl -X DELETE http://127.0.0.1:16010/v1/data/files/test2.docx -H "Content-Type: application/json" | jq '.'
```

### Update a file

```bash
curl -X PATCH http://127.0.0.1:16010/v1/data/files/test.pdf -H "Content-Type: application/json" -d @examples/test_data_file.json | jq '.'
```
