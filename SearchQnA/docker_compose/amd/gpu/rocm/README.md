# Build and deploy SearchQnA Application on AMD GPU (ROCm)

## Build Docker Images

### 1. Build Docker Image

- #### Create application install directory and go to it:

  ```bash
  mkdir ~/searchqna-install && cd searchqna-install
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
  cd ~/searchqna-install/GenAIExamples/SearchQnA/docker_image_build
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

  If you use a specific tag of the GenAIExamples repository,
  then you should also use the corresponding tag for GenAIComps. (v1.3 replace with its own value):

  ```bash
  git clone https://github.com/opea-project/GenAIComps.git && cd GenAIComps && git checkout v1.3
  ```

  We remind you that when using a specific version of the code, you need to use the README from this version.

- #### Setting the list of images for the build (from the build file.yaml)

  If you want to deploy a vLLM-based or TGI-based application, then the set of services is installed as follows:

  #### vLLM-based application

  ```bash
  service_list="vllm-rocm llm-textgen reranking web-retriever embedding searchqna-ui searchqna"
  ```

  #### TGI-based application

  ```bash
  service_list="llm-textgen reranking web-retriever embedding searchqna-ui searchqna"
  ```

- #### Optional. Pull TGI Docker Image (Do this if you want to use TGI)

  ```bash
  docker pull ghcr.io/huggingface/text-generation-inference:2.3.1-rocm
  ```

- #### Build Docker Images

  ```bash
  docker compose -f build.yaml build ${service_list} --no-cache
  ```

  After the build, we check the list of images with the command:

  ```bash
  docker image ls
  ```

  The list of images should include:

  ##### vLLM-based application:

  - opea/vllm-rocm:latest
  - opea/llm-textgen:latest
  - opea/reranking:latest
  - opea/searchqna:latest
  - opea/searchqna-ui:latest
  - opea/web-retriever:latest

  ##### TGI-based application:

  - ghcr.io/huggingface/text-generation-inference:2.3.1-rocm
  - opea/llm-textgen:latest
  - opea/reranking:latest
  - opea/searchqna:latest
  - opea/searchqna-ui:latest
  - opea/web-retriever:latest

---

## Deploy the SearchQnA Application

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
  - /dev/dri/renderD128:/dev/dri/renderD128
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

##### Set variable HUGGINGFACEHUB_API_TOKEN:

```bash
### Replace the string 'your_huggingfacehub_token' with your HuggingFacehub repository access token.
export HUGGINGFACEHUB_API_TOKEN='your_huggingfacehub_token'
### Replace the string 'your_google_api_token' with your Google API access token
export GOOGLE_API_KEY='your_google_api_token'
### Replace the string 'your_google_cse_id' with your Google CSE ID
export GOOGLE_CSE_ID='your_google_cse_id'
```

#### Set variables value in set_env\*\*\*\*.sh file:

Go to Docker Compose directory:

```bash
cd ~/searchqna-install/GenAIExamples/SearchQnA/docker_compose/amd/gpu/rocm
```

The example uses the Nano text editor. You can use any convenient text editor:

#### If you use vLLM

```bash
nano set_env_vllm.sh
```

#### If you use TGI

```bash
nano set_env.sh
```

If you are in a proxy environment, also set the proxy-related environment variables:

```bash
export http_proxy="Your_HTTP_Proxy"
export https_proxy="Your_HTTPs_Proxy"
```

Set the values of the variables:

- **HOST_IP, HOST_IP_EXTERNAL** - These variables are used to configure the name/address of the service in the operating system environment for the application services to interact with each other and with the outside world.

  If your server uses only an internal address and is not accessible from the Internet, then the values for these two variables will be the same and the value will be equal to the server's internal name/address.

  If your server uses only an external, Internet-accessible address, then the values for these two variables will be the same and the value will be equal to the server's external name/address.

  If your server is located on an internal network, has an internal address, but is accessible from the Internet via a proxy/firewall/load balancer, then the HOST_IP variable will have a value equal to the internal name/address of the server, and the EXTERNAL_HOST_IP variable will have a value equal to the external name/address of the proxy/firewall/load balancer behind which the server is located.

  We set these values in the file set_env\*\*\*\*.sh

- **Variables with names like "**\*\*\*\*\*\*\_PORT"\*\* - These variables set the IP port numbers for establishing network connections to the application services.
  The values shown in the file set_env.sh or set_env_vllm they are the values used for the development and testing of the application, as well as configured for the environment in which the development is performed. These values must be configured in accordance with the rules of network access to your environment's server, and must not overlap with the IP ports of other applications that are already in use.

#### Set variables with script set_env\*\*\*\*.sh

#### If you use vLLM

```bash
. set_env_vllm.sh
```

#### If you use TGI

```bash
. set_env.sh
```

### Start the services:

#### If you use vLLM

```bash
docker compose -f compose_vllm.yaml up -d
```

#### If you use TGI

```bash
docker compose -f compose.yaml up -d
```

All containers should be running and should not restart:

##### If you use vLLM:

- search-vllm-service
- search-llm-server
- search-web-retriever-server
- search-tei-embedding-server
- search-tei-reranking-server
- search-reranking-server
- search-embedding-server
- search-backend-server
- search-ui-server

##### If you use TGI:

- search-tgi-service
- search-llm-server
- search-web-retriever-server
- search-tei-embedding-server
- search-tei-reranking-server
- search-reranking-server
- search-embedding-server
- search-backend-server
- search-ui-server

---

## Validate the Services

### 1. Validate the vLLM/TGI Service

#### If you use vLLM:

```bash
DATA='{"model": "Intel/neural-chat-7b-v3-3", '\
'"messages": [{"role": "user", "content": "What is Deep Learning?"}], "max_tokens": 32}'

curl http://${HOST_IP}:${SEARCH_VLLM_SERVICE_PORT}/v1/chat/completions \
  -X POST \
  -d "$DATA" \
  -H 'Content-Type: application/json'
```

Checking the response from the service. The response should be similar to JSON:

```json
{
  "id": "chatcmpl-a3761920c4034131b3cab073b8e8b841",
  "object": "chat.completion",
  "created": 1742959065,
  "model": "Intel/neural-chat-7b-v3-3",
  "choices": [
    {
      "index": 0,
      "message": {
        "role": "assistant",
        "content": " Deep Learning refers to a modern approach of Artificial Intelligence that aims to replicate the way human brains process information by teaching computers to learn from data without extensive programming",
        "tool_calls": []
      },
      "logprobs": null,
      "finish_reason": "length",
      "stop_reason": null
    }
  ],
  "usage": { "prompt_tokens": 15, "total_tokens": 47, "completion_tokens": 32, "prompt_tokens_details": null },
  "prompt_logprobs": null
}
```

If the service response has a meaningful response in the value of the "choices.message.content" key,
then we consider the vLLM service to be successfully launched

#### If you use TGI:

```bash
DATA='{"inputs":"What is Deep Learning?",'\
'"parameters":{"max_new_tokens":256,"do_sample": true}}'

curl http://${HOST_IP}:${SEARCH_TGI_SERVICE_PORT}/generate \
  -X POST \
  -d "$DATA" \
  -H 'Content-Type: application/json'
```

Checking the response from the service. The response should be similar to JSON:

```json
{
  "generated_text": "\n\nDeep Learning is a subset of machine learning, which focuses on developing methods inspired by the functioning of the human brain; more specifically, the way it processes and acquires various types of knowledge and information. To enable deep learning, the networks are composed of multiple processing layers that form a hierarchy, with each layer learning more complex and abstraction levels of data representation.\n\nThe principle of Deep Learning is to emulate the structure of neurons in the human brain to construct artificial neural networks capable to accomplish complicated pattern recognition tasks more effectively and accurately. Therefore, these neural networks contain a series of hierarchical components, where units in earlier layers receive simple inputs and are activated by these inputs. The activation of the units in later layers are the results of multiple nonlinear transformations generated from reconstructing and integrating the information in previous layers. In other words, by combining various pieces of information at each layer, a Deep Learning network can extract the input features that best represent the structure of data, providing their outputs at the last layer or final level of abstraction.\n\nThe main idea of using these 'deep' networks in contrast to regular algorithms is that they are capable of representing hierarchical relationships that exist within the data and learn these representations by"
}
```

If the service response has a meaningful response in the value of the "generated_text" key,
then we consider the TGI service to be successfully launched

### 2. Validate the LLM Service

```bash
DATA='{"query":"What is Deep Learning?",'\
'"max_tokens":32,"top_k":10,"top_p":0.95,"typical_p":0.95,"temperature":0.01,'\
'"repetition_penalty":1.03,"stream":false}'

curl http://${HOST_IP}:${SEARCH_LLM_SERVICE_PORT}/v1/chat/completions \
  -X POST \
  -d "$DATA" \
  -H 'Content-Type: application/json'
```

Checking the response from the service. The response should be similar to JSON:

```json
{
  "id": "cmpl-0b974d00a7604c2ab8b721ebf6b88ae3",
  "choices": [
    {
      "finish_reason": "length",
      "index": 0,
      "logprobs": null,
      "text": "\n\nDeep Learning is a subset of Machine Learning that is concerned with algorithms inspired by the structure and function of the brain. It is a part of Artificial",
      "stop_reason": null,
      "prompt_logprobs": null
    }
  ],
  "created": 1742959134,
  "model": "Intel/neural-chat-7b-v3-3",
  "object": "text_completion",
  "system_fingerprint": null,
  "usage": {
    "completion_tokens": 32,
    "prompt_tokens": 6,
    "total_tokens": 38,
    "completion_tokens_details": null,
    "prompt_tokens_details": null
  }
}
```

### 3. Validate TEI Embedding service

```bash
curl http://${HOST_IP}:${SEARCH_TEI_EMBEDDING_PORT}/embed \
    -X POST \
    -d '{"inputs":"What is Deep Learning?"}' \
    -H 'Content-Type: application/json'
```

Checking the response from the service. The response should be similar to text:

```textmate
[[0.00037115702,-0.06356819,..................,-0.02125421,-0.02984927,-0.0049473033]]
```

If the response text is similar to the one above, then we consider the service verification successful.

### 4. Validate Embedding service

```bash
curl http://${HOST_IP}:${SEARCH_EMBEDDING_SERVICE_PORT}/v1/embeddings \
  -X POST \
  -d '{"input":"Hello!"}' \
  -H 'Content-Type: application/json'
```

Checking the response from the service. The response should be similar to JSON:

```json
{
  "object": "list",
  "model": "BAAI/bge-base-en-v1.5",
  "data": [
    { "index": 0, "object": "embedding", "embedding": [0.010614655, 0.019818036, "******", 0.06571652, -0.019738553] }
  ],
  "usage": { "prompt_tokens": 4, "total_tokens": 4, "completion_tokens": 0 }
}
```

If the response JSON is similar to the one above, then we consider the service verification successful.

### 5. Validate Web Retriever service

```bash
export your_embedding=$(python3 -c "import random; embedding = [random.uniform(-1, 1) for _ in range(768)]; print(embedding)")
curl http://${HOST_IP}:${SEARCH_WEB_RETRIEVER_SERVICE_PORT}/v1/web_retrieval \
  -X POST \
  -d "{\"text\":\"What is the 2024 holiday schedule?\",\"embedding\":${your_embedding}}" \
  -H 'Content-Type: application/json'
```

Checking the response from the service. The response should be similar to JSON:

```json
{
  "id": "ec32c767e0ae107c4943b634648c9752",
  "retrieved_docs": [
    {
      "downstream_black_list": [],
      "id": "ab002cd89cd20d9229adae1e091c7e2d",
      "text": "2025\n\n    * ###  New Year’s Day 2024/2025 \n\nWednesday, January 1, 2025  Early Close (2:00 p.m. Eastern Time): Tuesday,\nDecember 31, 2024\n\n    * ###  Martin Luther King Day \n\nMonday, January 20, 2025\n\n    * ###  Presidents Day \n\nMonday, February 17, 2025\n\n    * ###  Good Friday \n\nFriday, April 18, 2025  Early Close (2:00 p.m. Eastern Time): Thursday, April\n17, 2025\n\n    * ###  Memorial Day \n\nMonday, May 26, 2025  Early Close (2:00 p.m. Eastern Time): Friday, May 23,\n2025\n\n    * ###  Juneteenth \n\nThursday, June 19, 2025\n\n    * ###  U.S. Independence Day \n\nFriday, July 4, 2025  Early Close (2:00 p.m. Eastern Time): Thursday, July 3,\n2025\n\n    * ###  Labor Day \n\nMonday, September 1, 2025\n\n    * ###  Columbus Day \n\nMonday, October 13, 2025\n\n    * ###  Veterans Day \n\nTuesday, November 11, 2025\n\n    * ###  Thanksgiving Day \n\nThursday, November 27, 2025  Early Close (2:00 p.m. Eastern Time): Friday,\nNovember 28, 2025\n\n    * ###  Christmas Day \n\nThursday, December 25, 2025  Early Close (2:00 p.m. Eastern Time): Wednesday,\nDecember 24, 2025\n\n    * ###  New Year’s Day 2025/2026 \n\nThursday, January 1, 2026  Early Close (2:00 p.m. Eastern Time): Wednesday,\nDecember 31, 2025\n\n2026\n\n    * ###  New Year’s Day 2025/2026 \n\nThursday, January 1, 2026  Early Close (2:00 p.m. Eastern Time): Wednesday,\nDecember 31, 2025\n\n    * ###  Martin Luther King Day \n\nMonday, January 19, 2026\n\n    * ###  Presidents Day \n\nMonday, February 16, 2026\n\n    * ###  Good Friday \n description:  \n \n title: \n                  Holiday Schedule - SIFMA - Holiday Schedule - SIFMA\n               \n \n source: https://www.sifma.org/resources/general/holiday-schedule/ \n"
    },
    {
      "downstream_black_list": [],
      "id": "f498f4a1357bfbc631a5d67663c64680",
      "text": "Monday, May 26, 2025\n\n    * ###  Juneteenth \n\nThursday, June 19, 2025\n\n    * ###  U.S. Independence Day \n\nFriday, July 4, 2025\n\n    * ###  Summer Bank Holiday \n\nMonday, August 25, 2025\n\n    * ###  Labor Day \n\nMonday, September 1, 2025\n\n    * ###  Columbus Day \n\nMonday, October 13, 2025\n\n    * ###  Veterans Day \n\nTuesday, November 11, 2025\n\n    * ###  Thanksgiving Day \n\nThursday, November 27, 2025\n\n    * ###  Christmas Day \n\nThursday, December 25, 2025\n\n    * ###  Boxing Day \n\nFriday, December 26, 2025\n\n    * ###  New Year’s Day 2025/2026 \n\nThursday, January 1, 2026\n\n2026\n\n    * ###  New Year’s Day 2025/2026 \n\nThursday, January 1, 2026\n\n    * ###  Martin Luther King Day \n\nMonday, January 19, 2026\n\n    * ###  Presidents Day \n\nMonday, February 16, 2026\n\n    * ###  Good Friday \n\nFriday, April 3, 2026\n\n    * ###  Easter Monday \n\nMonday, April 6, 2026\n\n    * ###  May Day \n\nMonday, May 4, 2026\n\n    * ###  Memorial Day \n\nMonday, May 25, 2026\n\n    * ###  Spring Bank Holiday \n\nMonday, May 25, 2026\n\n    * ###  Juneteenth \n\nFriday, June 19, 2026\n\n    * ###  U.S. Independence Day \n\nFriday, July 3, 2026\n\n    * ###  Summer Bank Holiday \n\nMonday, August 31, 2026\n\n    * ###  Labor Day \n\nMonday, September 7, 2026\n\n    * ###  Columbus Day \n\nMonday, October 12, 2026\n\n    * ###  Veterans Day \n\nWednesday, November 11, 2026\n\n    * ###  Thanksgiving Day \n\nThursday, November 26, 2026\n\n    * ###  Christmas Day \n\nFriday, December 25, 2026\n\n    * ###  Boxing Day (Substitute) \n description:  \n \n title: \n                  Holiday Schedule - SIFMA - Holiday Schedule - SIFMA\n               \n \n source: https://www.sifma.org/resources/general/holiday-schedule/ \n"
    },
    {
      "downstream_black_list": [],
      "id": "3a845fba37a225ee3a67601cfa51f6d6",
      "text": "**Holiday** | **2024** | **Non-Management, Supervisory Units** | **Department of Corrections Employees** | **State Police Unit** | **Exempt, Managerial, and Confidential**  \n---|---|---|---|---|---  \n**New Year’s Day** | **Monday, January 1, 2024** | Observed | Observed | Observed | Observed  \n**Martin Luther King Jr. Day** | **Monday, January 15, 2024** | Observed | Observed | Observed | Observed  \n**Presidents' Day** | **Monday, February 19, 2024** | Observed | Observed | Observed | Observed  \n**Town Meeting Day** | **Tuesday,    \nMarch 5, 2024** | Observed | Observed | Observed | Observed  \n**Memorial Day** | **Monday,    \nMay 27, 2024** | Observed | Observed | Observed | Observed  \n**Independence Day** | **Thursday,    \nJuly 4, 2024** | Observed | Observed | Observed | Observed  \n**Bennington Battle Day** | **Friday,    \nAugust 16, 2024** | Observed | **Not Observed** | **Not Observed** | Observed  \n**Labor Day** | **Monday, September 2, 2024** | Observed | Observed | Observed | Observed  \n**Indigenous Peoples' Day** | **Monday, October 14, 2024** | **Not Observed** | Observed | Observed | **Not Observed**  \n**Veterans' Day** | **Monday, November 11, 2024** | Observed | Observed | Observed | Observed  \n**Thanksgiving Day** | **Thursday, November 28, 2024** | Observed | Observed | Observed | Observed  \n**Christmas Day** | **Wednesday, December 25, 2024** | Observed | Observed | Observed | Observed  \n title: State Holiday Schedule | Department of Human Resources \n \n source: https://humanresources.vermont.gov/benefits-wellness/holiday-schedule \n"
    },
    {
      "downstream_black_list": [],
      "id": "34926c9655c38d2af761833d57c8ab8a",
      "text": "* ###  Good Friday \n\nNone  Early Close (12:00 p.m. Eastern Time): Friday, April 3, 2026 - Tentative\n- pending confirmation of scheduled release of BLS employment report\n\n    * ###  Memorial Day \n\nMonday, May 25, 2026  Early Close (2:00 p.m. Eastern Time): Friday, May 22,\n2026\n\n    * ###  Juneteenth \n\nFriday, June 19, 2026\n\n    * ###  U.S. Independence Day (observed) \n\nFriday, July 3, 2026  Early Close (2:00 p.m. Eastern Time): Thursday, July 2,\n2026\n\n    * ###  Labor Day \n\nMonday, September 7, 2026\n\n    * ###  Columbus Day \n\nMonday, October 12, 2026\n\n    * ###  Veterans Day \n\nWednesday, November 11, 2026\n\n    * ###  Thanksgiving Day \n\nThursday, November 26, 2026  Early Close (2:00 p.m. Eastern Time): Friday,\nNovember 27, 2026\n\n    * ###  Christmas Day \n\nFriday, December 25, 2026  Early Close (2:00 p.m. Eastern Time): Thursday,\nDecember 24, 2026\n\n    * ###  New Year’s Day 2026/2027 \n\nFriday, January 1, 2027  Early Close (2:00 p.m. Eastern Time): Thursday,\nDecember 31, 2026\n\nArchive\n\n###  U.K. Holiday Recommendations\n\n2025\n\n    * ###  New Year’s Day 2024/2025 \n\nWednesday, January 1, 2025\n\n    * ###  Martin Luther King Day \n\nMonday, January 20, 2025\n\n    * ###  Presidents Day \n\nMonday, February 17, 2025\n\n    * ###  Good Friday \n\nFriday, April 18, 2025\n\n    * ###  Easter Monday \n\nMonday, April 21, 2025\n\n    * ###  May Day \n\nMonday, May 5, 2025\n\n    * ###  Memorial Day \n\nMonday, May 26, 2025\n\n    * ###  Spring Bank Holiday \n\nMonday, May 26, 2025\n\n    * ###  Juneteenth \n description:  \n \n title: \n                  Holiday Schedule - SIFMA - Holiday Schedule - SIFMA\n               \n \n source: https://www.sifma.org/resources/general/holiday-schedule/ \n"
    }
  ],
  "initial_query": "What is the 2024 holiday schedule?",
  "top_n": 1
}
```

If the response JSON is similar to the one above, then we consider the service verification successful.

### 6. Validate the TEI Reranking Service

```bash
DATA='{"query":"What is Deep Learning?", "texts": ["Deep Learning is not...", "Deep learning is..."]}'
curl http://${HOST_IP}:${SEARCH_TEI_RERANKING_PORT}/rerank \
  -X POST \
  -d "$DATA" \
  -H 'Content-Type: application/json'
```

Checking the response from the service. The response should be similar to JSON:

```json
[
  { "index": 1, "score": 0.94238955 },
  { "index": 0, "score": 0.120219156 }
]
```

If the response JSON is similar to the one above, then we consider the service verification successful.

### 7. Validate Reranking service

```bash
DATA='{"initial_query":"What is Deep Learning?", "retrieved_docs": '\
'[{"text":"Deep Learning is not..."}, {"text":"Deep learning is..."}]}'

curl http://${HOST_IP}:${SEARCH_RERANK_SERVICE_PORT}/v1/reranking \
  -X POST \
  -d "$DATA" \
  -H 'Content-Type: application/json'
```

Checking the response from the service. The response should be similar to JSON:

```json
{
  "id": "d44b5be4002e8e2cc3b6a4861e396093",
  "model": null,
  "query": "What is Deep Learning?",
  "max_tokens": 1024,
  "max_new_tokens": 1024,
  "top_k": 10,
  "top_p": 0.95,
  "typical_p": 0.95,
  "temperature": 0.01,
  "frequency_penalty": 0.0,
  "presence_penalty": 0.0,
  "repetition_penalty": 1.03,
  "stream": true,
  "language": "auto",
  "chat_template": null,
  "documents": ["Deep learning is..."]
}
```

If the response JSON is similar to the one above, then we consider the service verification successful.

### 8. Validate MegaService

```bash
DATA='{"messages": "What is the latest news from the AI world? '\
'Give me a summary.","stream": "True"}'

curl http://${HOST_IP}:${SEARCH_BACKEND_SERVICE_PORT}/v1/searchqna \
  -H "Content-Type: application/json" \
  -d "$DATA"
```

Checking the response from the service. The response should be similar to JSON:

```textmate
data: {"id":"cmpl-f095893d094a4e9989423c2364f00bc1","choices":[{"finish_reason":null,"index":0,"logprobs":null,"text":",","stop_reason":null}],"created":1742960360,"model":"Intel/neural-chat-7b-v3-3","object":"text_completion","system_fingerprint":null,"usage":null}
data: {"id":"cmpl-f095893d094a4e9989423c2364f00bc1","choices":[{"finish_reason":null,"index":0,"logprobs":null,"text":" with","stop_reason":null}],"created":1742960360,"model":"Intel/neural-chat-7b-v3-3","object":"text_completion","system_fingerprint":null,"usage":null}
data: {"id":"cmpl-f095893d094a4e9989423c2364f00bc1","choices":[{"finish_reason":null,"index":0,"logprobs":null,"text":" calls","stop_reason":null}],"created":1742960360,"model":"Intel/neural-chat-7b-v3-3","object":"text_completion","system_fingerprint":null,"usage":null}
data: {"id":"cmpl-f095893d094a4e9989423c2364f00bc1","choices":[{"finish_reason":null,"index":0,"logprobs":null,"text":" for","stop_reason":null}],"created":1742960360,"model":"Intel/neural-chat-7b-v3-3","object":"text_completion","system_fingerprint":null,"usage":null}
data: {"id":"cmpl-f095893d094a4e9989423c2364f00bc1","choices":[{"finish_reason":null,"index":0,"logprobs":null,"text":" more","stop_reason":null}],"created":1742960360,"model":"Intel/neural-chat-7b-v3-3","object":"text_completion","system_fingerprint":null,"usage":null}
data: {"id":"cmpl-f095893d094a4e9989423c2364f00bc1","choices":[{"finish_reason":null,"index":0,"logprobs":null,"text":" regulation","stop_reason":null}],"created":1742960360,"model":"Intel/neural-chat-7b-v3-3","object":"text_completion","system_fingerprint":null,"usage":null}
data: {"id":"cmpl-f095893d094a4e9989423c2364f00bc1","choices":[{"finish_reason":null,"index":0,"logprobs":null,"text":" and","stop_reason":null}],"created":1742960360,"model":"Intel/neural-chat-7b-v3-3","object":"text_completion","system_fingerprint":null,"usage":null}
data: {"id":"cmpl-f095893d094a4e9989423c2364f00bc1","choices":[{"finish_reason":null,"index":0,"logprobs":null,"text":" trans","stop_reason":null}],"created":1742960360,"model":"Intel/neural-chat-7b-v3-3","object":"text_completion","system_fingerprint":null,"usage":null}
data: {"id":"cmpl-f095893d094a4e9989423c2364f00bc1","choices":[{"finish_reason":null,"index":0,"logprobs":null,"text":"parency","stop_reason":null}],"created":1742960360,"model":"Intel/neural-chat-7b-v3-3","object":"text_completion","system_fingerprint":null,"usage":null}
data: {"id":"cmpl-f095893d094a4e9989423c2364f00bc1","choices":[{"finish_reason":null,"index":0,"logprobs":null,"text":".","stop_reason":null}],"created":1742960360,"model":"Intel/neural-chat-7b-v3-3","object":"text_completion","system_fingerprint":null,"usage":null}
data: {"id":"cmpl-f095893d094a4e9989423c2364f00bc1","choices":[{"finish_reason":"stop","index":0,"logprobs":null,"text":"","stop_reason":null}],"created":1742960360,"model":"Intel/neural-chat-7b-v3-3","object":"text_completion","system_fingerprint":null,"usage":null}
data: [DONE]
```

If the response text is similar to the one above, then we consider the service verification successful.

### 9. Validate Frontend

To access the UI, use the URL - http://${EXTERNAL_HOST_IP}:${SEARCH_FRONTEND_SERVICE_PORT} A page should open when you click through to this address:
![UI start page](../../../../assets/img/searchqna-ui-starting-page.png)

If a page of this type has opened, then we believe that the service is running and responding, and we can proceed to functional UI testing.

Let's enter the task for the service in the "Enter prompt here" field. For example, "What is DeepLearning?" and press Enter. After that, a page with the result of the task should open:

![UI start page](../../../../assets/img/searchqna-ui-response-example.png)
If the result shown on the page is correct, then we consider the verification of the UI service to be successful.

### 10. Stop application

#### If you use vLLM

```bash
cd ~/searchqna-install/GenAIExamples/SearchQnA/docker_compose/amd/gpu/rocm
docker compose -f compose_vllm.yaml down
```

#### If you use TGI

```bash
cd ~/searchqna-install/GenAIExamples/SearchQnA/docker_compose/amd/gpu/rocm
docker compose -f compose.yaml down
```
