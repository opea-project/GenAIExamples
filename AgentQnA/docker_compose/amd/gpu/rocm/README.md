# Build Mega Service of AgentQnA on AMD ROCm GPU

## Build Docker Images

### 1. Build Docker Image

- #### Create application install directory and go to it:

  ```bash
  mkdir ~/agentqna-install && cd agentqna-install
  ```

- #### Clone the repository GenAIExamples (the default repository branch "main" is used here):

  ```bash
  git clone https://github.com/opea-project/GenAIExamples.git
  ```

  If you need to use a specific branch/tag of the GenAIExamples repository, then (v1.3 replace with its own value):

  ```bash
  git clone https://github.com/opea-project/GenAIExamples.git && cd GenAIExamples && git checkout v1.3
  ```

  We remind you that when using a specific version of the code, you need to use the README from this version:

- #### Go to build directory:

  ```bash
  cd ~/agentqna-install/GenAIExamples/AgentQnA/docker_image_build
  ```

- Cleaning up the GenAIComps repository if it was previously cloned in this directory.
  This is necessary if the build was performed earlier and the GenAIComps folder exists and is not empty:

  ```bash
  echo Y | rm -R GenAIComps
  ```

- #### Clone the repository GenAIComps (the default repository branch "main" is used here):

```bash
git clone https://github.com/opea-project/GenAIComps.git
```

We remind you that when using a specific version of the code, you need to use the README from this version.

- #### Setting the list of images for the build (from the build file.yaml)

  If you want to deploy a vLLM-based or TGI-based application, then the set of services is installed as follows:

  #### vLLM-based application

  ```bash
  service_list="vllm-rocm agent agent-ui"
  ```

  #### TGI-based application

  ```bash
  service_list="agent agent-ui"
  ```

- #### Optional. Pull TGI Docker Image (Do this if you want to use TGI)

  ```bash
  docker pull ghcr.io/huggingface/text-generation-inference:2.3.1-rocm
  ```

- #### Build Docker Images

  ```bash
  docker compose -f build.yaml build ${service_list} --no-cache
  ```

- #### Build DocIndexRetriever Docker Images

  ```bash
  cd ~/agentqna-install/GenAIExamples/DocIndexRetriever/docker_image_build/
  git clone https://github.com/opea-project/GenAIComps.git
  service_list="doc-index-retriever dataprep embedding retriever reranking"
  docker compose -f build.yaml build ${service_list} --no-cache
  ```

- #### Pull DocIndexRetriever Docker Images

  ```bash
  docker pull redis/redis-stack:7.2.0-v9
  docker pull ghcr.io/huggingface/text-embeddings-inference:cpu-1.5
  ```

  After the build, we check the list of images with the command:

  ```bash
  docker image ls
  ```

  The list of images should include:

  ##### vLLM-based application:

  - opea/vllm-rocm:latest
  - opea/agent:latest
  - redis/redis-stack:7.2.0-v9
  - ghcr.io/huggingface/text-embeddings-inference:cpu-1.5
  - opea/embedding:latest
  - opea/retriever:latest
  - opea/reranking:latest
  - opea/doc-index-retriever:latest

  ##### TGI-based application:

  - ghcr.io/huggingface/text-generation-inference:2.3.1-rocm
  - opea/agent:latest
  - redis/redis-stack:7.2.0-v9
  - ghcr.io/huggingface/text-embeddings-inference:cpu-1.5
  - opea/embedding:latest
  - opea/retriever:latest
  - opea/reranking:latest
  - opea/doc-index-retriever:latest

---

## Deploy the AgentQnA Application

### Docker Compose Configuration for AMD GPUs

To enable GPU support for AMD GPUs, the following configuration is added to the Docker Compose file:

- compose_vllm.yaml - for vLLM-based application
- compose.yaml - for TGI-based

```yaml
shm_size: 1g
devices:
  - /dev/kfd:/dev/kfd
  - /dev/dri:/dev/dri
cap_add:
  - SYS_PTRACE
group_add:
  - video
security_opt:
  - seccomp:unconfined
```

This configuration forwards all available GPUs to the container. To use a specific GPU, specify its `cardN` and `renderN` device IDs. For example:

```yaml
shm_size: 1g
devices:
  - /dev/kfd:/dev/kfd
  - /dev/dri/card0:/dev/dri/card0
  - /dev/dri/render128:/dev/dri/render128
cap_add:
  - SYS_PTRACE
group_add:
  - video
security_opt:
  - seccomp:unconfined
```

**How to Identify GPU Device IDs:**
Use AMD GPU driver utilities to determine the correct `cardN` and `renderN` IDs for your GPU.

### Set deploy environment variables

#### Setting variables in the operating system environment:

```bash
### Replace the string 'server_address' with your local server IP address
export host_ip='server_address'
### Replace the string 'your_huggingfacehub_token' with your HuggingFacehub repository access token.
export HF_TOKEN='your_huggingfacehub_token'
### Replace the string 'your_langchain_api_key' with your LANGCHAIN API KEY.
export LANGCHAIN_API_KEY='your_langchain_api_key'
export LANGCHAIN_TRACING_V2=""
```

### Start the services:

#### If you use vLLM

```bash
cd ~/agentqna-install/GenAIExamples/AgentQnA/docker_compose/amd/gpu/rocm
bash launch_agent_service_vllm_rocm.sh
```

#### If you use TGI

```bash
cd ~/agentqna-install/GenAIExamples/AgentQnA/docker_compose/amd/gpu/rocm
bash launch_agent_service_tgi_rocm.sh
```

All containers should be running and should not restart:

##### If you use vLLM:

- dataprep-redis-server
- doc-index-retriever-server
- embedding-server
- rag-agent-endpoint
- react-agent-endpoint
- redis-vector-db
- reranking-tei-xeon-server
- retriever-redis-server
- sql-agent-endpoint
- tei-embedding-server
- tei-reranking-server
- vllm-service

##### If you use TGI:

- dataprep-redis-server
- doc-index-retriever-server
- embedding-server
- rag-agent-endpoint
- react-agent-endpoint
- redis-vector-db
- reranking-tei-xeon-server
- retriever-redis-server
- sql-agent-endpoint
- tei-embedding-server
- tei-reranking-server
- tgi-service

---

## Validate the Services

### 1. Validate the vLLM/TGI Service

#### If you use vLLM:

```bash
DATA='{"model": "Intel/neural-chat-7b-v3-3t", '\
'"messages": [{"role": "user", "content": "What is Deep Learning?"}], "max_tokens": 256}'

curl http://${HOST_IP}:${VLLM_SERVICE_PORT}/v1/chat/completions \
  -X POST \
  -d "$DATA" \
  -H 'Content-Type: application/json'
```

Checking the response from the service. The response should be similar to JSON:

```json
{
  "id": "chatcmpl-142f34ef35b64a8db3deedd170fed951",
  "object": "chat.completion",
  "created": 1742270316,
  "model": "Intel/neural-chat-7b-v3-3",
  "choices": [
    {
      "index": 0,
      "message": {
        "role": "assistant",
        "content": "",
        "tool_calls": []
      },
      "logprobs": null,
      "finish_reason": "length",
      "stop_reason": null
    }
  ],
  "usage": { "prompt_tokens": 66, "total_tokens": 322, "completion_tokens": 256, "prompt_tokens_details": null },
  "prompt_logprobs": null
}
```

If the service response has a meaningful response in the value of the "choices.message.content" key,
then we consider the vLLM service to be successfully launched

#### If you use TGI:

```bash
DATA='{"inputs":"What is Deep Learning?",'\
'"parameters":{"max_new_tokens":256,"do_sample": true}}'

curl http://${HOST_IP}:${TGI_SERVICE_PORT}/generate \
  -X POST \
  -d "$DATA" \
  -H 'Content-Type: application/json'
```

Checking the response from the service. The response should be similar to JSON:

```json
{
  "generated_text": " "
}
```

If the service response has a meaningful response in the value of the "generated_text" key,
then we consider the TGI service to be successfully launched

### 2. Validate Agent Services

#### Validate Rag Agent Service

```bash
export agent_port=${WORKER_RAG_AGENT_PORT}
prompt="Tell me about Michael Jackson song Thriller"
python3 ~/agentqna-install/GenAIExamples/AgentQnA/tests/test.py --prompt "$prompt" --agent_role "worker" --ext_port $agent_port
```

The response must contain the meaningful text of the response to the request from the "prompt" variable

#### Validate Sql Agent Service

```bash
export agent_port=${WORKER_SQL_AGENT_PORT}
prompt="How many employees are there in the company?"
python3 ~/agentqna-install/GenAIExamples/AgentQnA/tests/test.py --prompt "$prompt" --agent_role "worker" --ext_port $agent_port
```

The answer should make sense - "8 employees in the company"

#### Validate React (Supervisor) Agent Service

```bash
export agent_port=${SUPERVISOR_REACT_AGENT_PORT}
python3 ~/agentqna-install/GenAIExamples/AgentQnA/tests/test.py --agent_role "supervisor" --ext_port $agent_port --stream
```

The response should contain "Iron Maiden"

### 3. Stop application

#### If you use vLLM

```bash
cd ~/agentqna-install/GenAIExamples/AgentQnA/docker_compose/amd/gpu/rocm
bash stop_agent_service_vllm_rocm.sh
```

#### If you use TGI

```bash
cd ~/agentqna-install/GenAIExamples/AgentQnA/docker_compose/amd/gpu/rocm
bash stop_agent_service_tgi_rocm.sh
```
