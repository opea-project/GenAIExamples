# Edge Craft Retrieval-Augmented Generation API guide

## Pipeline Management

### Create a pipeline

```bash
curl -X POST http://${HOST_IP}:16010/v1/settings/pipelines -H "Content-Type: application/json" -d @tests/test_pipeline_local_llm.json | jq '.'
```

### Update a pipeline

```bash
curl -X PATCH http://${HOST_IP}:16010/v1/settings/pipelines/rag_test_local_llm  -H "Content-Type: application/json" -d @tests/test_pipeline_local_llm.json | jq '.'
```

### Check all pipelines

```bash
curl -X GET http://${HOST_IP}:16010/v1/settings/pipelines -H "Content-Type: application/json" | jq '.'
```

### Activate a pipeline

```bash
curl -X PATCH http://${HOST_IP}:16010/v1/settings/pipelines/rag_test_local_llm -H "Content-Type: application/json" -d '{"active": "true"}' | jq '.'
```

### Remove a pipeline

```bash
# Firstly, deactivate the pipeline if the pipeline status is active
curl -X PATCH http://${HOST_IP}:16010/v1/settings/pipelines/rag_test_local_llm -H "Content-Type: application/json" -d '{"active": "false"}' | jq '.'
# Then delete the pipeline
curl -X DELETE http://${HOST_IP}:16010/v1/settings/pipelines/rag_test_local_llm -H "Content-Type: application/json" | jq '.'
```

### Get pipeline json

```bash
curl -X GET http://${HOST_IP}:16010/v1/settings/pipelines/{name}/json -H "Content-Type: application/json" | jq '.'
```

### Import pipeline from a json file

```bash
curl -X POST http://${HOST_IP}:16010/v1/settings/pipelines/import -H "Content-Type: multipart/form-data" -F "file=@your_test_pipeline_json_file.txt"| jq '.'
```

### Enable and check benchmark for pipelines

#### ⚠️ NOTICE ⚠️

Benchmarking activities may significantly reduce system performance.

**DO NOT** perform benchmarking in a production environment.

```bash
# Set ENABLE_BENCHMARK as true before launch services
export ENABLE_BENCHMARK="true"

# check the benchmark data for pipeline {pipeline_name}
curl -X GET http://${HOST_IP}:16010/v1/settings/pipelines/{pipeline_name}/benchmark -H "Content-Type: application/json" | jq '.'
```

## Model Management

### Load a model

```bash
curl -X POST http://${HOST_IP}:16010/v1/settings/models -H "Content-Type: application/json" -d '{"model_type": "reranker", "model_id": "BAAI/bge-reranker-large", "model_path": "./models/bge_ov_reranker", "device": "cpu", "weight": "INT4"}' | jq '.'
```

It will take some time to load the model.

### Check all models

```bash
curl -X GET http://${HOST_IP}:16010/v1/settings/models -H "Content-Type: application/json" | jq '.'
```

### Update a model

```bash
curl -X PATCH http://${HOST_IP}:16010/v1/settings/models/BAAI/bge-reranker-large -H "Content-Type: application/json" -d '{"model_type": "reranker", "model_id": "BAAI/bge-reranker-large", "model_path": "./models/bge_ov_reranker", "device": "gpu", "weight": "INT4"}' | jq '.'
```

### Check a certain model

```bash
curl -X GET http://${HOST_IP}:16010/v1/settings/models/BAAI/bge-reranker-large -H "Content-Type: application/json" | jq '.'
```

### Delete a model

```bash
curl -X DELETE http://${HOST_IP}:16010/v1/settings/models/BAAI/bge-reranker-large -H "Content-Type: application/json" | jq '.'
```

## Knowledge Base Management

### Create a knowledge base

```bash
curl -X POST http://${HOST_IP}:16010/v1/knowledge -H "Content-Type: application/json" -d '{"name": "default_kb","description": "Your knowledge base Description","active":true}' | jq '.'
```

### Update a knowledge base

```bash
curl -X PATCH http://${HOST_IP}:16010/v1/knowledge/patch -H "Content-Type: application/json" -d '{"name": "default_kb","active":"True","description": "Your knowledge base Description","active":"True"}' | jq '.'
```

### Check all knowledge base

```bash
curl -X GET http://${HOST_IP}:16010/v1/knowledge -H "Content-Type: application/json" | jq '.'
```

### Activate knowledge base

```bash
curl -X PATCH http://${HOST_IP}:16010/v1/knowledge/patch -H "Content-Type: application/json" -d '{"name": "default_kb","active":true}' | jq '.'
```

### Remove a knowledge base

```bash
curl -X DELETE http://${HOST_IP}:16010/v1/knowledge/default_kb -H "Content-Type: application/json" | jq '.'
```

### Add file to knowledge base

```bash
curl -X POST http://${HOST_IP}:16010/v1/knowledge/default_kb/files -H "Content-Type: application/json" -d '{"local_path": "docs/#REPLACE WITH YOUR DIR WITHIN MOUNTED DOC PATH#"}' | jq '.'
```

### Delete file to knowledge base

```bash
curl -X DELETE http://${HOST_IP}:16010/v1/knowledge/default_kb/files -H "Content-Type: application/json" -d '{"local_path": "docs/#REPLACE WITH YOUR DIR WITHIN MOUNTED DOC PATH#"}' | jq '.'
```

## File Management

### Add a text

```bash
curl -X POST http://${HOST_IP}:16010/v1/data -H "Content-Type: application/json" -d '{"text":"#REPLACE WITH YOUR TEXT"}' | jq '.'
```

### Add files from existed file path

```bash
curl -X POST http://${HOST_IP}:16010/v1/data -H "Content-Type: application/json" -d '{"local_path":"docs/#REPLACE WITH YOUR DIR WITHIN MOUNTED DOC PATH#"}' | jq '.'
curl -X POST http://${HOST_IP}:16010/v1/data -H "Content-Type: application/json" -d '{"local_path":"docs/#REPLACE WITH YOUR FILE WITHIN MOUNTED DOC PATH#"}' | jq '.'
```

### Check all files

```bash
curl -X GET http://${HOST_IP}:16010/v1/data/files -H "Content-Type: application/json" | jq '.'
```

### Check one file

```bash
curl -X GET http://${HOST_IP}:16010/v1/data/files/test2.docx -H "Content-Type: application/json" | jq '.'
```

### Delete a file

```bash
curl -X DELETE http://${HOST_IP}:16010/v1/data/files/test2.docx -H "Content-Type: application/json" | jq '.'
```

### Update a file

```bash
curl -X PATCH http://${HOST_IP}:16010/v1/data/files/test.pdf -H "Content-Type: application/json" -d '{"local_path":"docs/#REPLACE WITH YOUR FILE WITHIN MOUNTED DOC PATH#"}' | jq '.'
```

## System Prompt Management

### Get system prompt

```bash
curl -X GET http://${HOST_IP}:16010/v1/chatqna/prompt -H "Content-Type: application/json" | jq '.'
```

### Update system prompt

```bash
curl -X POST http://${HOST_IP}:16010/v1/chatqna/prompt -H "Content-Type: application/json" -d '{"prompt":"This is a template prompt"}' | jq '.'
```

### Reset system prompt

```bash
curl -X POST http://${HOST_IP}:16010/v1/chatqna/prompt/reset -H "Content-Type: application/json" | jq '.'
```

### Use custom system prompt file

```bash
curl -X POST http://${HOST_IP}:16010/v1/chatqna/prompt-file -H "Content-Type: multipart/form-data" -F "file=@your_prompt_file.txt"
```

## ChatQnA

### Retrieval API

```bash
curl -X POST http://${HOST_IP}:16010/v1/retrieval -H "Content-Type: application/json" -d '{"messages":"#Please enter the question you need to retrieve here#", "top_n":5, "max_tokens":512}' | jq '.'

```

### ChatQnA API

```bash
curl -X POST http://${HOST_IP}:16011/v1/chatqna -H "Content-Type: application/json" -d '{"messages":"#REPLACE WITH YOUR QUESTION HERE#", "top_n":5, "max_tokens":512}' | jq '.'
```