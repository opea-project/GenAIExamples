# Edge Craft Retrieval-Augmented Generation API Guide

> **Base URLs**
>
> - EC-RAG Server: `http://${HOST_IP}:16010`
> - EC-RAG Mega Service: `http://${HOST_IP}:16011`

---

## Pipeline Management

### Create a pipeline

```bash
curl -X POST http://${HOST_IP}:16010/v1/settings/pipelines \
  -H "Content-Type: application/json" \
  -d @tests/test_pipeline_local_llm.json | jq '.'
```

### Update a pipeline

```bash
curl -X PATCH http://${HOST_IP}:16010/v1/settings/pipelines/{name} \
  -H "Content-Type: application/json" \
  -d @tests/test_pipeline_local_llm.json | jq '.'
```

### Check all pipelines

```bash
curl -X GET http://${HOST_IP}:16010/v1/settings/pipelines \
  -H "Content-Type: application/json" | jq '.'
```

### Check a specific pipeline

```bash
curl -X GET http://${HOST_IP}:16010/v1/settings/pipelines/{name} \
  -H "Content-Type: application/json" | jq '.'
```

### Activate a pipeline

```bash
curl -X PATCH http://${HOST_IP}:16010/v1/settings/pipelines/{name} \
  -H "Content-Type: application/json" \
  -d '{"active": "true"}' | jq '.'
```

### Remove a pipeline

```bash
# Firstly, deactivate the pipeline if the pipeline status is active
curl -X PATCH http://${HOST_IP}:16010/v1/settings/pipelines/{name} \
  -H "Content-Type: application/json" \
  -d '{"active": "false"}' | jq '.'

# Then delete the pipeline
curl -X DELETE http://${HOST_IP}:16010/v1/settings/pipelines/{name} \
  -H "Content-Type: application/json" | jq '.'
```

### Get pipeline JSON

```bash
curl -X GET http://${HOST_IP}:16010/v1/settings/pipelines/{name}/json \
  -H "Content-Type: application/json" | jq '.'
```

### Import pipeline from a JSON file

```bash
curl -X POST http://${HOST_IP}:16010/v1/settings/pipelines/import \
  -H "Content-Type: multipart/form-data" \
  -F "file=@your_pipeline.json" | jq '.'
```

### Enable and check benchmark for pipelines

#### ⚠️ NOTICE ⚠️

Benchmarking activities may significantly reduce system performance.

**DO NOT** perform benchmarking in a production environment.

```bash
# Set ENABLE_BENCHMARK as true before launching services
export ENABLE_BENCHMARK="true"

# Check the benchmark data for the active pipeline
curl -X GET http://${HOST_IP}:16010/v1/settings/pipeline/benchmark \
  -H "Content-Type: application/json" | jq '.'

# Check the benchmark data for a specific pipeline
curl -X GET http://${HOST_IP}:16010/v1/settings/pipelines/{pipeline_name}/benchmarks \
  -H "Content-Type: application/json" | jq '.'
```

---

## Model Management

### Load a model

```bash
curl -X POST http://${HOST_IP}:16010/v1/settings/models \
  -H "Content-Type: application/json" \
  -d '{"model_type": "reranker", "model_id": "BAAI/bge-reranker-large", "model_path": "./models/bge_ov_reranker", "device": "cpu", "weight": "INT4"}' | jq '.'
```

It will take some time to load the model.

### Check all models

```bash
curl -X GET http://${HOST_IP}:16010/v1/settings/models \
  -H "Content-Type: application/json" | jq '.'
```

### Check a specific model

```bash
curl -X GET http://${HOST_IP}:16010/v1/settings/models/BAAI/bge-reranker-large \
  -H "Content-Type: application/json" | jq '.'
```

### Update a model

```bash
curl -X PATCH http://${HOST_IP}:16010/v1/settings/models/BAAI/bge-reranker-large \
  -H "Content-Type: application/json" \
  -d '{"model_type": "reranker", "model_id": "BAAI/bge-reranker-large", "model_path": "./models/bge_ov_reranker", "device": "gpu", "weight": "INT4"}' | jq '.'
```

### Delete a model

```bash
curl -X DELETE http://${HOST_IP}:16010/v1/settings/models/BAAI/bge-reranker-large \
  -H "Content-Type: application/json" | jq '.'
```

### Get available model weights

Query the available compression weights (INT4 / INT8 / FP16) for a given model path:

```bash
curl -X GET "http://${HOST_IP}:16010/v1/settings/weight/BAAI/bge-reranker-large" \
  -H "Content-Type: application/json" | jq '.'
```

### Get available model IDs by type

Supported `model_type` values: `LLM`, `vLLM`, `reranker`, `embedding`, `vLLM_embedding`, `kbadmin_embedding_model`

```bash
# List available local LLM models
curl -X GET "http://${HOST_IP}:16010/v1/settings/avail-models/LLM" \
  -H "Content-Type: application/json" | jq '.'

# List models served by a vLLM server (optional server_address parameter)
curl -X GET "http://${HOST_IP}:16010/v1/settings/avail-models/vLLM?server_address=http://localhost:8086" \
  -H "Content-Type: application/json" | jq '.'

# List available embedding models
curl -X GET "http://${HOST_IP}:16010/v1/settings/avail-models/embedding" \
  -H "Content-Type: application/json" | jq '.'
```

### Get available models from a vLLM server

```bash
curl -X GET "http://${HOST_IP}:16010/v1/available_models?server_address=http://localhost:8086" \
  -H "Content-Type: application/json" | jq '.'
```

---

## Knowledge Base Management

### Create a knowledge base

```bash
curl -X POST http://${HOST_IP}:16010/v1/knowledge \
  -H "Content-Type: application/json" \
  -d @tests/configs/test_kb.json | jq '.'
```

### Check all knowledge bases

```bash
curl -X GET http://${HOST_IP}:16010/v1/knowledge \
  -H "Content-Type: application/json" | jq '.'
```

### Check a specific knowledge base

```bash
curl -X GET http://${HOST_IP}:16010/v1/knowledge/default_kb \
  -H "Content-Type: application/json" | jq '.'
```

### Get knowledge base JSON

```bash
curl -X GET http://${HOST_IP}:16010/v1/knowledge/default_kb/json \
  -H "Content-Type: application/json" | jq '.'
```

### Get knowledge base file map (paginated)

```bash
curl -X GET "http://${HOST_IP}:16010/v1/knowledge/default_kb/filemap?page_num=1&page_size=20" \
  -H "Content-Type: application/json" | jq '.'
```

### Update a knowledge base

```bash
curl -X PATCH http://${HOST_IP}:16010/v1/knowledge/patch \
  -H "Content-Type: application/json" \
  -d '{"name": "default_kb", "active": "True", "description": "Your knowledge base description"}' | jq '.'
```

### Activate a knowledge base

```bash
curl -X PATCH http://${HOST_IP}:16010/v1/knowledge/patch \
  -H "Content-Type: application/json" \
  -d '{"name": "default_kb", "active": true}' | jq '.'
```

### Remove a knowledge base

```bash
curl -X DELETE http://${HOST_IP}:16010/v1/knowledge/default_kb \
  -H "Content-Type: application/json" | jq '.'
```

### Add file to knowledge base

```bash
curl -X POST http://${HOST_IP}:16010/v1/knowledge/default_kb/files \
  -H "Content-Type: application/json" \
  -d '{"local_path": "/home/user/ui_cache/#REPLACE WITH YOUR FILE OR DIR PATH#"}' | jq '.'
```

### Delete file from knowledge base

```bash
curl -X DELETE http://${HOST_IP}:16010/v1/knowledge/default_kb/files \
  -H "Content-Type: application/json" \
  -d '{"local_path": "/home/user/ui_cache/#REPLACE WITH YOUR FILE PATH#"}' | jq '.'
```

---

## Experience Knowledge Base Management

Experience knowledge bases store curated Q&A pairs that can be retrieved to augment pipeline responses.

### Get all experiences

```bash
curl -X GET http://${HOST_IP}:16010/v1/experiences \
  -H "Content-Type: application/json" | jq '.'
```

### Get experience by ID or question

```bash
curl -X POST http://${HOST_IP}:16010/v1/experience \
  -H "Content-Type: application/json" \
  -d '{"idx": "your-experience-id"}' | jq '.'
```

### Update an experience

```bash
curl -X PATCH http://${HOST_IP}:16010/v1/experiences \
  -H "Content-Type: application/json" \
  -d '{"idx": "your-experience-id", "question": "Updated question?", "content": "Updated answer"}' | jq '.'
```

### Delete an experience

```bash
curl -X DELETE http://${HOST_IP}:16010/v1/experiences \
  -H "Content-Type: application/json" \
  -d '{"idx": "your-experience-id"}' | jq '.'
```

### Add experiences from a file

```bash
curl -X POST http://${HOST_IP}:16010/v1/experiences/files \
  -H "Content-Type: application/json" \
  -d '{"local_path": "/home/user/ui_cache/experiences.json"}' | jq '.'
```

### Check and add multiple experiences (duplicate check first)

```bash
# Step 1: Check for duplicates; if none, experiences are added automatically
curl -X POST http://${HOST_IP}:16010/v1/multiple_experiences/check \
  -H "Content-Type: application/json" \
  -d '[{"question": "What is EC-RAG?", "content": "EdgeCraft RAG is ..."}]' | jq '.'

# Step 2 (only if duplicates detected): Confirm with overwrite flag
# flag=true → overwrite duplicates; flag=false → append
curl -X POST "http://${HOST_IP}:16010/v1/multiple_experiences/confirm?flag=true" \
  -H "Content-Type: application/json" \
  -d '[{"question": "What is EC-RAG?", "content": "EdgeCraft RAG is ..."}]' | jq '.'
```

---

## Agent Management

### Check all agents

```bash
curl -X GET http://${HOST_IP}:16010/v1/agents \
  -H "Content-Type: application/json" | jq '.'
```

### Check a specific agent

```bash
curl -X GET http://${HOST_IP}:16010/v1/agents/{name} \
  -H "Content-Type: application/json" | jq '.'
```

### Get default configs for an agent type

```bash
curl -X GET http://${HOST_IP}:16010/v1/agents/configs/{agent_type} \
  -H "Content-Type: application/json" | jq '.'
```

### Create an agent

```bash
curl -X POST http://${HOST_IP}:16010/v1/agents \
  -H "Content-Type: application/json" \
  -d '{"name": "my_agent", "type": "react_llm", "pipeline_idx": "your-pipeline-idx"}' | jq '.'
```

### Update an agent

```bash
curl -X PATCH http://${HOST_IP}:16010/v1/agents/{name} \
  -H "Content-Type: application/json" \
  -d '{"name": "my_agent", "active": true}' | jq '.'
```

### Delete an agent

```bash
curl -X DELETE http://${HOST_IP}:16010/v1/agents/{name} \
  -H "Content-Type: application/json" | jq '.'
```

---

## System Prompt Management

### Get system prompt

```bash
curl -X GET http://${HOST_IP}:16010/v1/chatqna/prompt \
  -H "Content-Type: application/json" | jq '.'
```

### Get tagged system prompt

```bash
curl -X GET http://${HOST_IP}:16010/v1/chatqna/prompt/tagged \
  -H "Content-Type: application/json" | jq '.'
```

### Get default system prompt

```bash
curl -X GET http://${HOST_IP}:16010/v1/chatqna/prompt/default \
  -H "Content-Type: application/json" | jq '.'
```

### Update system prompt

```bash
curl -X POST http://${HOST_IP}:16010/v1/chatqna/prompt \
  -H "Content-Type: application/json" \
  -d '{"prompt": "This is a custom prompt template"}' | jq '.'
```

### Upload system prompt from file

```bash
curl -X POST http://${HOST_IP}:16010/v1/chatqna/prompt-file \
  -H "Content-Type: multipart/form-data" \
  -F "file=@your_prompt_file.txt" | jq '.'
```

### Reset system prompt to default

```bash
curl -X POST http://${HOST_IP}:16010/v1/chatqna/prompt/reset \
  -H "Content-Type: application/json" | jq '.'
```

---

## Data Management

### Get all nodes (chunks) in the active knowledge base

```bash
curl -X GET http://${HOST_IP}:16010/v1/data/nodes \
  -H "Content-Type: application/json" | jq '.'
```

### Get nodes by document name

```bash
curl -X GET "http://${HOST_IP}:16010/v1/data/{document_name}/nodes" \
  -H "Content-Type: application/json" | jq '.'
```

### Get all document names in the active knowledge base

```bash
curl -X GET http://${HOST_IP}:16010/v1/data/documents \
  -H "Content-Type: application/json" | jq '.'
```

### Get all files

```bash
curl -X GET http://${HOST_IP}:16010/v1/data/files \
  -H "Content-Type: application/json" | jq '.'
```

### Get a specific file

```bash
curl -X GET http://${HOST_IP}:16010/v1/data/files/{name} \
  -H "Content-Type: application/json" | jq '.'
```

### Upload a file (from UI)

```bash
curl -X POST "http://${HOST_IP}:16010/v1/data/file/{file_name}" \
  -H "Content-Type: multipart/form-data" \
  -F "file=@/path/to/your/document.pdf" | jq '.'
```

---

## Session Management

### Get all sessions

```bash
curl -X GET http://${HOST_IP}:16010/v1/sessions \
  -H "Content-Type: application/json" | jq '.'
```

### Get a session by ID

```bash
curl -X GET http://${HOST_IP}:16010/v1/session/{session_id} \
  -H "Content-Type: application/json" | jq '.'
```

---

## System Information

### Get system status

Returns CPU usage, memory usage, disk usage, OS info, and current time.

```bash
curl -X GET http://${HOST_IP}:16010/v1/system/info \
  -H "Content-Type: application/json" | jq '.'
```

### Get available inference devices

Returns OpenVINO-available devices (e.g., CPU, GPU, AUTO).

```bash
curl -X GET http://${HOST_IP}:16010/v1/system/device \
  -H "Content-Type: application/json" | jq '.'
```

---

## ChatQnA

### Retrieval API

Retrieve relevant context chunks from the active knowledge base without running LLM generation.

```bash
curl -X POST http://${HOST_IP}:16010/v1/retrieval \
  -H "Content-Type: application/json" \
  -d '{"messages": "Your question here", "top_n": 5, "max_tokens": 512}' | jq '.'
```

### ChatQnA API (Mega Service)

Send a question through the full RAG pipeline (retrieval + LLM generation).

```bash
curl -X POST http://${HOST_IP}:16011/v1/chatqna \
  -H "Content-Type: application/json" \
  -d '{"messages": "Your question here", "top_n": 5, "max_tokens": 512}' | jq '.'
```

### RAGQnA API (with contexts in response)

Returns the LLM answer together with the retrieved context chunks.

```bash
# Non-streaming
curl -X POST http://${HOST_IP}:16010/v1/ragqna \
  -H "Content-Type: application/json" \
  -d '{"messages": "Your question here", "top_n": 5, "max_tokens": 512, "stream": false}' | jq '.'

# Streaming
curl -X POST http://${HOST_IP}:16010/v1/ragqna \
  -H "Content-Type: application/json" \
  -d '{"messages": "Your question here", "top_n": 5, "max_tokens": 512, "stream": true}'
```

### Check vLLM server connection

```bash
curl -X POST http://${HOST_IP}:16010/v1/check/vllm \
  -H "Content-Type: application/json" \
  -d '{"server_address": "http://localhost:8086", "model_name": "Qwen/Qwen3-8B"}' | jq '.'
```
