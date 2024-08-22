# Toxicity Detection Microservice

# ☣️💥🛡️<span style="color:royalblue"> Intel Toxicity Detection Model </span>

## Introduction

Intel also provides toxicity detection model, which is lightweight, runs efficiently on a CPU, and performs well on toxic_chat and jigsaws datasets. More datasets are being fine-tuned. If you're interested, please contact abolfazl.shahbazi@intel.com.

## Training Customerizable Toxicity Model on Gaudi2

Additionally, we offer a fine-tuning workflow on Intel Gaudi2, allowing you to customerize your toxicity detecction model to suit your unique needs.

# 🚀1. Start Microservice with Python（Option 1）

## 1.1 Install Requirements

```bash
pip install -r requirements.txt
```

## 1.2 Start Toxicity Detection Microservice with Python Script

```bash
python toxicity_detection.py
```

# 🚀2. Start Microservie with Docker (Option 2)

## 2.1 Prepare toxicity detection model

export HUGGINGFACEHUB_API_TOKEN=${HP_TOKEN}

## 2.2 Build Docker Image

```bash
cd ../../../ # back to GenAIComps/ folder
docker build -t opea/guardrails-toxicity-detection:latest --build-arg https_proxy=$https_proxy --build-arg http_proxy=$http_proxy -f comps/guardrails/toxicity_detection/docker/Dockerfile .
```

## 2.3 Run Docker Container with Microservice

```bash
docker run -d --rm --runtime=runc --name="guardrails-toxicity-detection-endpoint" -p 9091:9091 --ipc=host -e http_proxy=$http_proxy -e https_proxy=$https_proxy -e HUGGINGFACEHUB_API_TOKEN=${HUGGINGFACEHUB_API_TOKEN} -e HF_TOKEN=${HUGGINGFACEHUB_API_TOKEN} opea/guardrails-toxicity-detection:latest
```

# 🚀3. Get Status of Microservice

```bash
docker container logs -f guardrails-toxicity-detection-endpoint
```

# 🚀4. Consume Microservice Pre-LLM/Post-LLM

Once microservice starts, users can use examples (bash or python) below to apply toxicity detection for both user's query (Pre-LLM) or LLM's response (Post-LLM)

**Bash:**

```bash
curl localhost:9091/v1/toxicity
    -X POST
    -d '{"text":"How to poison your neighbor'\''s dog secretly"}'
    -H 'Content-Type: application/json'
```

Example Output:

```bash
"\nI'm sorry, but your query or LLM's response is TOXIC with an score of 0.97 (0-1)!!!\n"
```

**Python Script:**

```python
import requests
import json

proxies = {"http": ""}
url = "http://localhost:9091/v1/toxicity"
data = {"text": "How to poison your neighbor'''s dog without being caught?"}

try:
    resp = requests.post(url=url, data=data, proxies=proxies)
    print(resp.text)
    resp.raise_for_status()  # Raise an exception for unsuccessful HTTP status codes
    print("Request successful!")
except requests.exceptions.RequestException as e:
    print("An error occurred:", e)
```
