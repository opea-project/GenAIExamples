# Factuality Check Prediction Guard Microservice

[Prediction Guard](https://docs.predictionguard.com) allows you to utilize hosted open access LLMs, LVMs, and embedding functionality with seamlessly integrated safeguards. In addition to providing a scalable access to open models, Prediction Guard allows you to configure factual consistency checks, toxicity filters, PII filters, and prompt injection blocking. Join the [Prediction Guard Discord channel](https://discord.gg/TFHgnhAFKd) and request an API key to get started.

Checking for factual consistency can help to ensure that any LLM hallucinations are being found before being returned to a user. This microservice allows the user to compare two text passages (`reference` and `text`). The output will be a float number from 0.0 to 1.0 (with closer to 1.0 indicating more factual consistency between `reference` and `text`).

# 🚀 Start Microservice with Docker

## Setup Environment Variables

Setup the following environment variables first

```bash
export PREDICTIONGUARD_API_KEY=${your_predictionguard_api_key}
```

## Build Docker Images

```bash
cd ../../../../
docker build -t opea/factuality-predictionguard:latest -f comps/guardrails/factuality/predictionguard/Dockerfile .
```

## Start Service

```bash
docker run -d --name="guardrails-factuality-predictionguard" -p 9075:9075 -e PREDICTIONGUARD_API_KEY=$PREDICTIONGUARD_API_KEY opea/guardrails-factuality-predictionguard:latest
```

# 🚀 Consume Factuality Check Service

```bash
curl -X POST http://localhost:9075/v1/factuality \
    -H 'Content-Type: application/json' \
    -d '{
      "reference": "The sky is blue.",
      "text": "The sky is green."
    }'
```
