# PII Detection Prediction Guard Microservice

[Prediction Guard](https://docs.predictionguard.com) allows you to utilize hosted open access LLMs, LVMs, and embedding functionality with seamlessly integrated safeguards. In addition to providing a scalable access to open models, Prediction Guard allows you to configure factual consistency checks, toxicity filters, PII filters, and prompt injection blocking. Join the [Prediction Guard Discord channel](https://discord.gg/TFHgnhAFKd) and request an API key to get started.

Detecting Personal Identifiable Information (PII) is important in ensuring that users aren't sending out private data to LLMs. This service allows you to configurably:

1. Detect PII
2. Replace PII (with "faked" information)
3. Mask PII (with placeholders)

# 🚀 Start Microservice with Docker

## Setup Environment Variables

Setup the following environment variables first

```bash
export PREDICTIONGUARD_API_KEY=${your_predictionguard_api_key}
```

## Build Docker Images

```bash
cd ../../../../
docker build -t opea/guardrails-pii-predictionguard:latest -f comps/guardrails/pii_detection/predictionguard/Dockerfile .
```

## Start Service

```bash
docker run -d --name="guardrails-pii-predictionguard" -p 9080:9080 -e PREDICTIONGUARD_API_KEY=$PREDICTIONGUARD_API_KEY opea/guardrails-pii-predictionguard:latest
```

# 🚀 Consume PII Detection Service

```bash
curl -X POST http://localhost:9080/v1/pii \
    -H 'Content-Type: application/json' \
    -d '{
      "prompt": "My name is John Doe and my phone number is 555-555-5555.",
      "replace": true,
      "replace_method": "random"
    }'
```

API parameters:

- `prompt` (string, required): The text in which you want to detect PII (typically the prompt that you anticipate sending to an LLM)
- `replace` (boolean, optional, default is `false`): `true` if you want to replace the detected PII in the `prompt`
- `replace_method` (string, optional, default is `random`): The method you want to use to replace PII (set to either `random`, `fake`, `category`, `mask`)
