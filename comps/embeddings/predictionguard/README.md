# Embedding Generation Prediction Guard Microservice

[Prediction Guard](https://docs.predictionguard.com) allows you to utilize hosted open access LLMs, LVMs, and embedding functionality with seamlessly integrated safeguards. In addition to providing a scalable access to open models, Prediction Guard allows you to configure factual consistency checks, toxicity filters, PII filters, and prompt injection blocking. Join the [Prediction Guard Discord channel](https://discord.gg/TFHgnhAFKd) and request an API key to get started.

This embedding microservice is designed to efficiently convert text into vectorized embeddings using the [BridgeTower model](https://huggingface.co/BridgeTower/bridgetower-large-itm-mlm-itc). Thus, it is ideal for both RAG or semantic search applications.

**Note** - The BridgeTower model implemented in Prediction Guard can actually embed text, images, or text + images (jointly). For now this service only embeds text, but a follow on contribution will enable the multimodal functionality.

## 🚀 Start Microservice with Docker

### Setup Environment Variables

Setup the following environment variables first

```bash
export PREDICTIONGUARD_API_KEY=${your_predictionguard_api_key}
```

### Build Docker Images

```bash
cd ../../..
docker build -t opea/embedding-predictionguard:latest -f comps/embeddings/predictionguard/Dockerfile .
```

### Start Service

```bash
docker run -d --name="embedding-predictionguard" -p 6000:6000 -e PREDICTIONGUARD_API_KEY=$PREDICTIONGUARD_API_KEY opea/embedding-predictionguard:latest
```

## 🚀 Consume Embeddings Service

Use our basic API.

```bash
## query with single text
curl http://localhost:6000/v1/embeddings\
  -X POST \
  -d '{"text":"Hello, world!"}' \
  -H 'Content-Type: application/json'

## query with multiple texts
curl http://localhost:6000/v1/embeddings\
  -X POST \
  -d '{"text":["Hello, world!","How are you?"]}' \
  -H 'Content-Type: application/json'
```

We are also compatible with [OpenAI API](https://platform.openai.com/docs/api-reference/embeddings).

```bash
## Input single text
curl http://localhost:6000/v1/embeddings\
  -X POST \
  -d '{"input":"Hello, world!"}' \
  -H 'Content-Type: application/json'

## Input multiple texts with parameters
curl http://localhost:6000/v1/embeddings\
  -X POST \
  -d '{"input":["Hello, world!","How are you?"], "dimensions":100}' \
  -H 'Content-Type: application/json'
```
