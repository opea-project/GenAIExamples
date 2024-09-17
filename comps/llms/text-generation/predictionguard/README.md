# Introduction

[Prediction Guard](https://docs.predictionguard.com) allows you to utilize hosted open access LLMs, LVMs, and embedding functionality with seamlessly integrated safeguards. In addition to providing a scalable access to open models, Prediction Guard allows you to configure factual consistency checks, toxicity filters, PII filters, and prompt injection blocking. Join the [Prediction Guard Discord channel](https://discord.gg/TFHgnhAFKd) and request an API key to get started.

# Get Started

## Build Docker Image

```bash
cd ../../..
docker build -t opea/llm-textgen-predictionguard:latest -f comps/llms/text-generation/predictionguard/Dockerfile .
```

## Run the Predictionguard Microservice

```bash
docker run -d -p 9000:9000 -e PREDICTIONGUARD_API_KEY=$PREDICTIONGUARD_API_KEY  --name llm-textgen-predictionguard opea/llm-textgen-predictionguard:latest
```

# Consume the Prediction Guard Microservice

See the [Prediction Guard docs](https://docs.predictionguard.com/) for available model options.

## Without streaming

```bash
curl -X POST http://localhost:9000/v1/chat/completions \
    -H "Content-Type: application/json" \
    -d '{
        "model": "Hermes-2-Pro-Llama-3-8B",
        "query": "Tell me a joke.",
        "max_new_tokens": 100,
        "temperature": 0.7,
        "top_p": 0.9,
        "top_k": 50,
        "stream": false
    }'
```

## With streaming

```bash
curl -N -X POST http://localhost:9000/v1/chat/completions \
    -H "Content-Type: application/json" \
    -d '{
        "model": "Hermes-2-Pro-Llama-3-8B",
        "query": "Tell me a joke.",
        "max_new_tokens": 100,
        "temperature": 0.7,
        "top_p": 0.9,
        "top_k": 50,
        "stream": true
    }'
```
