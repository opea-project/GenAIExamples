# PII Detection Microservice

PII Detection a method to detect Personal Identifiable Information in text. This microservice provides users a unified API to either upload your files or send a list of text, and return with a list following original sequence of labels marking if it contains PII or not.

# 🚀1. Start Microservice with Python（Option 1）

## 1.1 Install Requirements

```bash
pip install -r requirements.txt
```

## 1.2 Start PII Detection Microservice with Python Script

Start pii detection microservice with below command.

```bash
python pii_detection.py
```

# 🚀2. Start Microservice with Docker (Option 2)

## 2.1 Prepare PII detection model

export HUGGINGFACEHUB_API_TOKEN=${HP_TOKEN}

## 2.1.1 use LLM endpoint (will add later)

intro placeholder

## 2.2 Build Docker Image

```bash
cd ../../../ # back to GenAIComps/ folder
docker build -t opea/guardrails-pii-detection:latest --build-arg https_proxy=$https_proxy --build-arg http_proxy=$http_proxy -f comps/guardrails/pii_detection/docker/Dockerfile .
```

## 2.3 Run Docker with CLI

```bash
docker run -d --rm --runtime=runc --name="guardrails-pii-detection-endpoint" -p 6357:6357 --ipc=host -e http_proxy=$http_proxy -e https_proxy=$https_proxy -e HUGGINGFACEHUB_API_TOKEN=${HUGGINGFACEHUB_API_TOKEN} -e HF_TOKEN=${HUGGINGFACEHUB_API_TOKEN} opea/guardrails-pii-detection:latest
```

> debug mode

```bash
docker run --rm --runtime=runc --name="guardrails-pii-detection-endpoint" -p 6357:6357 -v ./comps/guardrails/pii_detection/:/home/user/comps/guardrails/pii_detection/ --ipc=host -e http_proxy=$http_proxy -e https_proxy=$https_proxy -e HUGGINGFACEHUB_API_TOKEN=${HUGGINGFACEHUB_API_TOKEN}  -e HF_TOKEN=${HUGGINGFACEHUB_API_TOKEN} opea/guardrails-pii-detection:latest
```

# 🚀3. Get Status of Microservice

```bash
docker container logs -f guardrails-pii-detection-endpoint
```

# 🚀4. Consume Microservice

Once microservice starts, user can use below script to invoke the microservice for pii detection.

```python
import requests
import json

proxies = {"http": ""}
url = "http://localhost:6357/v1/dataprep"
urls = [
    "https://towardsdatascience.com/no-gpu-no-party-fine-tune-bert-for-sentiment-analysis-with-vertex-ai-custom-jobs-d8fc410e908b?source=rss----7f60cf5620c9---4"
]
payload = {"link_list": json.dumps(urls)}

try:
    resp = requests.post(url=url, data=payload, proxies=proxies)
    print(resp.text)
    resp.raise_for_status()  # Raise an exception for unsuccessful HTTP status codes
    print("Request successful!")
except requests.exceptions.RequestException as e:
    print("An error occurred:", e)
```
