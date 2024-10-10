# Workflow Executor Agent

## Setup Guide

Workflow Executor will have a single docker image.

Instructions to setup.

```sh
git clone https://github.com/opea-project/GenAIExamples.git
cd GenAIExamples/WorkflowExecutor/
docker build -t opea/workflow-executor:latest -f Dockerfile .
```

Configure .env file with the following. Replace the variables according to your usecase.

```sh
export ip_address=$(hostname -I | awk '{print $1}')
export SERVING_PORT=8000
export model="mistralai/Mistral-7B-Instruct-v0.3"
export HUGGINGFACEHUB_API_TOKEN=${HF_TOKEN}
export SDK_BASE_URL=${SDK_BASE_URL}
export SERVING_TOKEN=${SERVING_TOKEN}
export http_proxy=${http_proxy}
export https_proxy=${https_proxy}
export recursion_limit=${recursion_limit}
export OPENAI_API_KEY=${OPENAI_API_KEY}
```

Launch service:

```sh
docker compose -f compose.yaml up -d
```
