Copyright (C) 2024 Advanced Micro Devices, Inc.

# Deploy AgentQnA application

## 1. Clone repo and build Docker images

### 1.1. Cloning GenAIComps repo

Create an empty directory in home directory and navigate to it:

```bash
mkdir -p ~/agentqna-test && cd ~/agentqna-test
```

Cloning GenAIExamples repo for build Docker images:

```bash
git clone https://github.com/opea-project/GenAIExamples.git
```

### 1.2. Navigate to repo directory and switching to the desired version of the code:

If you are using the main branch, then you do not need to make the transition, the main branch is used by default

```bash
cd ~/agentqna-test/GenAIExamples/AgentQnA/docker_image_build
```

If you are using a specific branch or tag, then we perform git checkout to the desired version.

```bash
### Replace "v1.2" with the code version you need (branch or tag)
cd cd ~/agentqna-test/GenAIExamples/AgentQnA/docker_image_build && git checkout v1.2
git clone https://github.com/opea-project/GenAIComps.git
```

### 1.3. Build Docker images repo

#### Build Agent Docker image:

```bash
docker compose -f build.yaml build --no-cache
```

#### Build Retrieval Tools Docker image:

```bash
cd ~/agentqna-test/GenAIExamples/DocIndexRetriever/docker_image_build/
git clone https://github.com/opea-project/GenAIComps.git
service_list="doc-index-retriever dataprep embedding retriever reranking"
docker compose -f build.yaml build ${service_list} --no-cache
```

#### Build ROCm vLLM Docker image:

```bash
cd ~/agentqna-test/GenAIExamples/AgentQnA
docker build --no-cache -t opea/llm-vllm-rocm:ci -f Dockerfile-vllm-rocm .
```

### 1.4. Pull Docker images from Docker Hub

```bash
docker pull ghcr.io/huggingface/text-embeddings-inference:cpu-1.5
```

### 1.5. Checking for the necessary Docker images

After assembling the images, you can check their presence in the list of available images using the command:

```bash
docker image ls
```

The output of the command should contain images:

- opea/doc-index-retriever:latest
- opea/embedding:latest
- opea/retriever:latest
- opea/reranking:latest
- opea/dataprep:lates
- opea/llm-vllm-rocm
- opea/agent:latest
- opea/agent-ui:latest
- ghcr.io/huggingface/text-embeddings-inference:cpu-1.5

## 2. Set deploy environment variables

### Setting variables in the operating system environment

#### Set variables:

```bash
### Replace the string "your_host_ip_or_host_name" with your server hostname or IP address.
export host_ip="your_host_ip_or_host_name"
### Replace the string 'your_huggingfacehub_token' with your HuggingFacehub repository access token.
export HUGGINGFACEHUB_API_TOKEN='your_huggingfacehub_token'
### Replace the string 'your_langchain_api_key' with your LangChain API key.
export LANGCHAIN_API_KEY='your_langchain_api_key'
export LANGCHAIN_TRACING_V2=""
```

If you are in a proxy environment, also set the proxy-related environment variables:

```bash
export http_proxy="Your_HTTP_Proxy"
export https_proxy="Your_HTTPs_Proxy"
```

- **Variables with names like "%%%%\_PORT"** - These variables set the IP port numbers for establishing network connections to the application services.
  The values shown in the file **launch_agent_service_vllm_rocm.sh** they are the values used for the development and testing of the application, as well as configured for the environment in which the development is performed. These values must be configured in accordance with the rules of network access to your environment's server, and must not overlap with the IP ports of other applications that are already in use.

## 3. Deploy application

### 3.1. Deploying applications using Docker Compose

```bash
cd cd ~/agentqna-test/GenAIExamples/AgentQnA/docker_compose/amd/gpu/rocm/
bash launch_agent_service_vllm_rocm.sh
```

After starting the containers, you need to view their status with the command:

```bash
docker ps
```

The following containers should be running:

- react-agent-endpoint
- vllm-service
- sql-agent-endpoint
- rag-agent-endpoint
- doc-index-retriever-server
- dataprep-redis-server
- retriever-redis-server
- reranking-tei-xeon-server
- embedding-server
- redis-vector-db
- tei-embedding-server
- tei-reranking-server

Containers should not restart.

#### 3.1.1. Configuring GPU forwarding

By default, in the Docker Compose file, compose_vllm.yaml is configured to forward all GPUs to the chatqna-vllm-service container.
To use certain GPUs, you need to configure the forwarding of certain devices from the host system to the container.
The configuration must be done in:

```yaml
services:
  #######
  vllm-service:
    devices:
```

Example for set isolation for 1 GPU

```
      - /dev/dri/card0:/dev/dri/card0
      - /dev/dri/renderD128:/dev/dri/renderD128
```

Example for set isolation for 2 GPUs

```
      - /dev/dri/card0:/dev/dri/card0
      - /dev/dri/renderD128:/dev/dri/renderD128
      - /dev/dri/card1:/dev/dri/card1
      - /dev/dri/renderD129:/dev/dri/renderD129
```

### 3.2. Checking the application services

#### 3.2.1. Checking vllm-service

Verification is performed in two ways:

- Checking the container logs

  ```bash
  docker logs vllm-service
  ```

  A message like this should appear in the logs:

  ```commandline
  INFO:     Started server process [1]
  INFO:     Waiting for application startup.
  INFO:     Application startup complete.
  INFO:     Uvicorn running on http://0.0.0.0:8011 (Press CTRL+C to quit)
  ```

- Сhecking the response from the service
  ```bash
  ### curl request
  ### Replace 18110 with the value set in the startup script in the variable VLLM_SERVICE_PORT
  curl http://${host_ip}:18110/v1/completions \
  -H "Content-Type: application/json" \
  -d '{
      "model": "Intel/neural-chat-7b-v3-3",
      "prompt": "What is a Deep Learning?",
      "max_tokens": 30,
      "temperature": 0
  }'
  ```
  The response from the service must be in the form of JSON:
  ```json
  {
    "id": "cmpl-1d7d175d36d0491cba3abaa8b5bd6991",
    "object": "text_completion",
    "created": 1740411135,
    "model": "Intel/neural-chat-7b-v3-3",
    "choices": [
      {
        "index": 0,
        "text": " Deep learning is a subset of machine learning that involves the use of artificial neural networks to analyze and interpret data. It is called \"deep\" because it",
        "logprobs": null,
        "finish_reason": "length",
        "stop_reason": null,
        "prompt_logprobs": null
      }
    ],
    "usage": { "prompt_tokens": 7, "total_tokens": 37, "completion_tokens": 30, "prompt_tokens_details": null }
  }
  ```
  The value of choice.text must contain a response from the service that makes sense.
  If such a response is present, then the vllm-service is considered verified.

#### 3.2.2. Checking worker rag agent

It is performed using requests to the service

**Checking Upload file**

```bash
### Replace 18111 with the value set in the startup script in the variable WORKER_RAG_AGENT_PORT
export agent_port="18111"
prompt="Tell me about Michael Jackson song Thriller"
python3 ~/agentqna-test/GenAIExamples/AgentQnA/tests/test.py --prompt "$prompt" --agent_role "worker" --ext_port $agent_port
```

The response must contain the correct text.

#### 3.2.3. Checking worker sql agent

It is performed using requests to the service

```bash
### Replace 18112 with the value set in the startup script in the variable WORKER_SQL_AGENT_PORT
export agent_port="18112"
prompt="How many employees are there in the company?"
python3 ~/agentqna-test/GenAIExamples/AgentQnA/tests/test.py --prompt "$prompt" --agent_role "worker" --ext_port $agent_port
```

The response should contain the string "8 employees in the company"

#### 3.2.4. Checking supervisor react agent

It is performed using requests to the service

```bash
### Replace 18113 with the value set in the startup script in the variable SUPERVISOR_REACT_AGENT_PORT
export agent_port="18113"
python3 ~/agentqna-test/GenAIExamples/AgentQnA/tests/test.py --agent_role "supervisor" --ext_port $agent_port --stream
```

The response must contain the string "Iron Maiden"
