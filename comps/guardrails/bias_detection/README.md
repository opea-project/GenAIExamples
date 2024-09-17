# Bias Detection Microservice

## Introduction

Bias Detection Microservice allows AI Application developers to safeguard user input and LLM output from biased language in a RAG environment. By leveraging a smaller fine-tuned Transformer model for bias classification (e.g. DistilledBERT, RoBERTa, etc.), we maintain a lightweight guardrails microservice without significantly sacrificing performance making it readily deployable on both Intel Gaudi and Xeon.

Bias erodes our collective trust and fuels social conflict. Bias can be defined as inappropriate subjectivity in the form of one of the following:

- Framing bias -- using subjective words or phrases linked with a particular point of view
- Epistemological bias -- linguistic features that subtly modify the believability of a proposition
- Demographic bias -- text with presuppositions about particular genders, races, or other demographic categories

## Future Development

- Add a "neutralizing bias" microservice to neutralizing any detected bias in the RAG serving, guarding the RAG usage.

## 🚀1. Start Microservice with Python（Option 1）

### 1.1 Install Requirements

```bash
pip install -r requirements.txt
```

### 1.2 Start Bias Detection Microservice with Python Script

```bash
python bias_detection.py
```

## 🚀2. Start Microservice with Docker (Option 2)

### 2.1 Prepare bias detection model

export HUGGINGFACEHUB_API_TOKEN=${HP_TOKEN}

### 2.2 Build Docker Image

```bash
cd ../../../ # back to GenAIComps/ folder
docker build -t opea/guardrails-bias-detection:latest --build-arg https_proxy=$https_proxy --build-arg http_proxy=$http_proxy -f comps/guardrails/bias_detection/Dockerfile .
```

### 2.3 Run Docker Container with Microservice

```bash
docker run -d --rm --runtime=runc --name="guardrails-bias-detection" -p 9092:9092 --ipc=host -e http_proxy=$http_proxy -e https_proxy=$https_proxy -e HUGGINGFACEHUB_API_TOKEN=${HUGGINGFACEHUB_API_TOKEN} -e HF_TOKEN=${HUGGINGFACEHUB_API_TOKEN} opea/guardrails-bias-detection:latest
```

## 🚀3. Get Status of Microservice

```bash
docker container logs -f guardrails-bias-detection
```

## 🚀4. Consume Microservice Pre-LLM/Post-LLM

Once microservice starts, users can use examples (bash or python) below to apply bias detection for both user's query (Pre-LLM) or LLM's response (Post-LLM)

**Bash:**

```bash
curl localhost:9092/v1/bias
    -X POST
    -d '{"text":"John McCain exposed as an unprincipled politician"}'
    -H 'Content-Type: application/json'
```

Example Output:

```bash
"\nI'm sorry, but your query or LLM's response is BIASED with an score of 0.74 (0-1)!!!\n"
```

**Python Script:**

```python
import requests
import json

proxies = {"http": ""}
url = "http://localhost:9092/v1/bias"
data = {"text": "John McCain exposed as an unprincipled politician"}


try:
    resp = requests.post(url=url, data=data, proxies=proxies)
    print(resp.text)
    resp.raise_for_status()  # Raise an exception for unsuccessful HTTP status codes
    print("Request successful!")
except requests.exceptions.RequestException as e:
    print("An error occurred:", e)
```
