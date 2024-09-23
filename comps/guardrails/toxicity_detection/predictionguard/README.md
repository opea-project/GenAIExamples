# Toxicity Checking Prediction Guard Microservice

[Prediction Guard](https://docs.predictionguard.com) allows you to utilize hosted open access LLMs, LVMs, and embedding functionality with seamlessly integrated safeguards. In addition to providing a scalable access to open models, Prediction Guard allows you to configure factual consistency checks, toxicity filters, PII filters, and prompt injection blocking. Join the [Prediction Guard Discord channel](https://discord.gg/TFHgnhAFKd) and request an API key to get started.

Checking text for toxicity allows you to prevent toxic prompts from being sent to your LLM and toxic LLM outputs from being sent to your users (especially for open access models that might have unclear alignment). This microservice analyzes input text and returns a float number (from 0.0 to 1.0) indicating a level of toxicity (with closer to 1.0 being more toxic).

# 🚀 Start Microservice with Docker

## Setup Environment Variables

Setup the following environment variables first

```bash
export PREDICTIONGUARD_API_KEY=${your_predictionguard_api_key}
```

## Build Docker Images

```bash
cd ../../../..
docker build -t opea/guardrails-toxicity-predictionguard:latest -f comps/guardrails/toxicity_detection/predictionguard/Dockerfile .
```

## Start Service

```bash
docker run -d --name="guardrails-toxicity-predictionguard" -p 9090:9090 -e PREDICTIONGUARD_API_KEY=$PREDICTIONGUARD_API_KEY opea/guardrails-toxicity-predictionguard:latest
```

# 🚀 Consume Toxicity Check Service

```bash
curl -X POST http://localhost:9090/v1/toxicity \
    -H 'Content-Type: application/json' \
    -d '{
      "text": "I hate you!!"
    }'
```
