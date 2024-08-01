# PII Detection Microservice

This microservice provides a unified API to detect if there is Personal Identifiable Information or Business Sensitive Information in text.

We provide 2 detection strategies:

1. Regular expression matching + named entity recognition (NER) - pass "ner" as strategy in your request to the microservice.
2. Logistic regression classifier - pass "ml" as strategy in your request to the microservice. **Note**: Currently this strategy is for demo only, and only supports using `nomic-ai/nomic-embed-text-v1` as the embedding model and the `Intel/business_safety_logistic_regression_classifier` model as the classifier. Please read the [full disclaimers in the model card](https://huggingface.co/Intel/business_safety_logistic_regression_classifier) before using this strategy.

## NER strategy

We adopted the [pii detection code](https://github.com/bigcode-project/bigcode-dataset/tree/main/pii) of the [BigCode](https://www.bigcode-project.org/) project and use the bigcode/starpii model for NER. Currently this strategy can detect IP address, emails, phone numbers, alphanumeric keys, names and passwords. The IP address, emails, phone numbers, alphanumeric keys are detected with regular expression matching. The names and passwords are detected with NER. Please refer to the starpii [model card](https://huggingface.co/bigcode/starpii) for more information of the detection performance.

## ML strategy

We have trained a classifier model using the [Patronus EnterprisePII dataset](https://www.patronus.ai/announcements/patronus-ai-launches-enterprisepii-the-industrys-first-llm-dataset-for-detecting-business-sensitive-information) for the demo purpose only. Please note that the demo model has not been extensively tested so is not intended for use in production environment. Please read the [full disclaimers in the model card](https://huggingface.co/Intel/business_safety_logistic_regression_classifier).

The classifiler model is used together with an embedding model to make predictions. The embedding model used for demo is `nomic-ai/nomic-embed-text-v1` [model](https://blog.nomic.ai/posts/nomic-embed-text-v1) available on Huggingface hub. We picked this open-source embedding model for demo as it is one of the top-performing long-context (max sequence length = 8192 vs. 512 for other BERT-based encoders) encoder models that do well on [Huggingface MTEB Leaderboard](https://huggingface.co/spaces/mteb/leaderboard) as well as long-context [LoCo benchmark](https://hazyresearch.stanford.edu/blog/2024-01-11-m2-bert-retrieval). The long-context capability is useful when the text is long (>512 tokens).

Currently this strategy can detect both personal sensitive and business sensitive information such as financial figures and performance reviews. Please refer to the [model card](<(https://huggingface.co/Intel/business_safety_logistic_regression_classifier)>) to see the performance of our demo model on the Patronus EnterprisePII dataset.

# Input and output

Users can send a list of files, a list of text strings, or a list of urls to the microservice, and the microservice will return a list of True or False for each piece of text following the original sequence.

For a concrete example of what input should look like, please refer to [Consume Microservice](#4-consume-microservice) section below.

The output will be a list of booleans, which can be parsed and used as conditions in a bigger application.

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
url = "http://localhost:6357/v1/piidetect"

strategy = "ml"  # options: "ner", "ml"
content = [
    "Q1 revenue was $1.23 billion, up 12% year over year. ",
    "We are excited to announce the opening of our new office in Miami! ",
    "Mary Smith, 123-456-7890,",
    "John is a good team leader",
    "meeting minutes: sync up with sales team on the new product launch",
]

payload = {"text_list": json.dumps(content), "strategy": strategy}

try:
    resp = requests.post(url=url, data=payload, proxies=proxies)
    print(resp.text)
    resp.raise_for_status()  # Raise an exception for unsuccessful HTTP status codes
    print("Request successful!")
except requests.exceptions.RequestException as e:
    print("An error occurred:", e)
```
