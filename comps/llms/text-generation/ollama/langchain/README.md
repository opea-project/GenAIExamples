# Introduction

[Ollama](https://github.com/ollama/ollama) allows you to run open-source large language models, such as Llama 3, locally. Ollama bundles model weights, configuration, and data into a single package, defined by a Modelfile. Ollama is a lightweight, extensible framework for building and running language models on the local machine. It provides a simple API for creating, running, and managing models, as well as a library of pre-built models that can be easily used in a variety of applications. It's the best choice to deploy large language models on AIPC locally.

## Get Started

### Setup

Follow [these instructions](https://github.com/ollama/ollama) to set up and run a local Ollama instance.

- Download and install Ollama onto the available supported platforms (including Windows)
- Fetch available LLM model via `ollama pull <name-of-model>`. View a list of available models via the model library and pull to use locally with the command `ollama pull llama3`
- This will download the default tagged version of the model. Typically, the default points to the latest, smallest sized-parameter model.

Note:
Special settings are necessary to pull models behind the proxy.

- Step1: Modify the ollama service configure file.

  ```bash
  sudo vim /etc/systemd/system/ollama.service
  ```

  Add your proxy to the above configure file.

  ```markdown
  [Service]
  Environment="http_proxy=${your_proxy}"
  Environment="https_proxy=${your_proxy}"
  ```

- Step2: Restart the ollama service.
  ```bash
  sudo systemctl daemon-reload
  sudo systemctl restart ollama
  ```

### Usage

Here are a few ways to interact with pulled local models:

#### In the terminal

All of your local models are automatically served on localhost:11434. Run `ollama run <name-of-model>` to start interacting via the command line directly.

#### API access

Send an application/json request to the API endpoint of Ollama to interact.

```bash
curl --noproxy "*" http://localhost:11434/api/generate -d '{
  "model": "llama3",
  "prompt":"Why is the sky blue?"
}'
```

## Build Docker Image

```bash
cd GenAIComps/
docker build --no-cache -t opea/llm-ollama:latest --build-arg https_proxy=$https_proxy --build-arg http_proxy=$http_proxy -f comps/llms/text-generation/ollama/langchain/Dockerfile .
```

## Run the Ollama Microservice

```bash
docker run --network host -e http_proxy=$http_proxy -e https_proxy=$https_proxy opea/llm-ollama:latest
```

## Consume the Ollama Microservice

```bash
curl http://127.0.0.1:9000/v1/chat/completions  -X POST   -d '{"model": "llama3", "query":"What is Deep Learning?","max_new_tokens":32,"top_k":10,"top_p":0.95,"typical_p":0.95,"temperature":0.01,"repetition_penalty":1.03,"streaming":true}'   -H 'Content-Type: application/json'
```
