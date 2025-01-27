# Build and deploy SearchQnA Application on AMD GPU (ROCm)

## Build images

### Build Embedding Image

```bash
git clone https://github.com/opea-project/GenAIComps.git
cd GenAIComps
docker build --no-cache -t opea/embedding-tei:latest --build-arg https_proxy=$https_proxy --build-arg http_proxy=$http_proxy -f comps/embeddings/src/Dockerfile .
```

### Build Retriever Image

```bash
docker build --no-cache -t opea/web-retriever-chroma:latest --build-arg https_proxy=$https_proxy --build-arg http_proxy=$http_proxy -f comps/web_retrievers/src/Dockerfile .
```

### Build Rerank Image

```bash
docker build --no-cache -t opea/reranking-tei:latest --build-arg https_proxy=$https_proxy --build-arg http_proxy=$http_proxy -f comps/rerankings/src/Dockerfile .
```

### Build the LLM Docker Image

```bash
docker build -t opea/llm-tgi:latest --build-arg https_proxy=$https_proxy --build-arg http_proxy=$http_proxy -f comps/llms/src/text-generation/Dockerfile .
```

### Build the MegaService Docker Image

```bash
git clone https://github.com/opea-project/GenAIExamples.git
cd GenAIExamples/SearchQnA
docker build --no-cache -t opea/searchqna:latest --build-arg https_proxy=$https_proxy --build-arg http_proxy=$http_proxy -f Dockerfile .
```

### Build the UI Docker Image

```bash
cd GenAIExamples/SearchQnA/ui
docker build --no-cache -t opea/opea/searchqna-ui:latest --build-arg https_proxy=$https_proxy --build-arg http_proxy=$http_proxy -f ./docker/Dockerfile .
```

## Deploy SearchQnA Application

### Features of Docker compose for AMD GPUs

1. Added forwarding of GPU devices to the container TGI service with instructions:

```yaml
shm_size: 1g
devices:
  - /dev/kfd:/dev/kfd
  - /dev/dri/:/dev/dri/
cap_add:
  - SYS_PTRACE
group_add:
  - video
security_opt:
  - seccomp:unconfined
```

In this case, all GPUs are thrown. To reset a specific GPU, you need to use specific device names cardN and renderN.

For example:

```yaml
shm_size: 1g
devices:
  - /dev/kfd:/dev/kfd
  - /dev/dri/card0:/dev/dri/card0
  - /dev/dri/render128:/dev/dri/render128
cap_add:
  - SYS_PTRACE
group_add:
  - video
security_opt:
  - seccomp:unconfined
```

To find out which GPU device IDs cardN and renderN correspond to the same GPU, use the GPU driver utility

### Go to the directory with the Docker compose file

```bash
cd GenAIExamples/SearchQnA/docker_compose/amd/gpu/rocm
```

### Set environments

In the file "GenAIExamples/SearchQnA/docker_compose/amd/gpu/rocm/set_env.sh " it is necessary to set the required values. Parameter assignments are specified in the comments for each variable setting command

```bash
chmod +x set_env.sh
. set_env.sh
```

### Run services

```
docker compose up -d
```

# Validate the MicroServices and MegaService

## Validate TEI service

```bash
curl http://${SEARCH_HOST_IP}:3001/embed \
    -X POST \
    -d '{"inputs":"What is Deep Learning?"}' \
    -H 'Content-Type: application/json'
```

## Validate Embedding service

```bash
curl http://${SEARCH_HOST_IP}:3002/v1/embeddings\
  -X POST \
  -d '{"text":"hello"}' \
  -H 'Content-Type: application/json'
```

## Validate Web Retriever service

```bash
export your_embedding=$(python3 -c "import random; embedding = [random.uniform(-1, 1) for _ in range(768)]; print(embedding)")
curl http://${SEARCH_HOST_IP}:3003/v1/web_retrieval \
  -X POST \
  -d "{\"text\":\"What is the 2024 holiday schedule?\",\"embedding\":${your_embedding}}" \
  -H 'Content-Type: application/json'
```

## Validate TEI Reranking service

```bash
curl http://${SEARCH_HOST_IP}:3004/rerank \
    -X POST \
    -d '{"query":"What is Deep Learning?", "texts": ["Deep Learning is not...", "Deep learning is..."]}' \
    -H 'Content-Type: application/json'
```

## Validate Reranking service

```bash
curl http://${SEARCH_HOST_IP}:3005/v1/reranking\
  -X POST \
  -d '{"initial_query":"What is Deep Learning?", "retrieved_docs": [{"text":"Deep Learning is not..."}, {"text":"Deep learning is..."}]}' \
  -H 'Content-Type: application/json'
```

## Validate TGI service

```bash
curl http://${SEARCH_HOST_IP}:3006/generate \
  -X POST \
  -d '{"inputs":"What is Deep Learning?","parameters":{"max_new_tokens":17, "do_sample": true}}' \
  -H 'Content-Type: application/json'
```

## Validate LLM service

```bash
curl http://${SEARCH_HOST_IP}:3007/v1/chat/completions\
  -X POST \
  -d '{"query":"What is Deep Learning?","max_tokens":17,"top_k":10,"top_p":0.95,"typical_p":0.95,"temperature":0.01,"repetition_penalty":1.03,"streaming":true}' \
  -H 'Content-Type: application/json'
```

## Validate MegaService

```bash
curl http://${SEARCH_HOST_IP}:3008/v1/searchqna -H "Content-Type: application/json" -d '{
     "messages": "What is the latest news? Give me also the source link.",
     "stream": "True"
     }'
```
