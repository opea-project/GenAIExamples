# Build and deploy Translation Application on AMD GPU (ROCm)

## Build Docker Images

### 1. Build Docker Image

- #### Create application install directory and go to it:

  ```bash
  mkdir ~/translation-install && cd translation-install
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
  cd ~/translation-install/GenAIExamples/Translation/docker_image_build
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
  service_list="vllm-rocm translation translation-ui llm-textgen nginx"
  ```

  #### TGI-based application

  ```bash
  service_list="translation translation-ui llm-textgen nginx"
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
    - opea/nginx:latest
    - opea/translation:latest
    - opea/translation-ui:latest

  ##### TGI-based application:

  - ghcr.io/huggingface/text-generation-inference:2.3.1-rocm
    - opea/llm-textgen:latest
    - opea/nginx:latest
    - opea/translation:latest
    - opea/translation-ui:latest

---

### Docker Compose Configuration for AMD GPUs

To enable GPU support for AMD GPUs, the following configuration is added to the Docker Compose file:

- compose_vllm.yaml - for vLLM-based application
- compose.yaml - for TGI-based

```yaml
shm_size: 1g
devices:
  - /dev/kfd:/dev/kfd
  - /dev/dri/:/dev/dri/
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
```

#### Set variables value in set_env\*\*\*\*.sh file:

Go to Docker Compose directory:

```bash
cd ~/translation-install/GenAIExamples/Translation/docker_compose/amd/gpu/rocm
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

- translationn-vllm-service
- translation-tgi-service
- translation-llm
- translation-backend-server
- translation-ui-server
- translation-nginx-server

##### If you use TGI:

- translation-tgi-service
- translation-llm
- translation-backend-server
- translation-ui-server
- translation-nginx-server

---

## Validate the Services

### 1. Validate the vLLM/TGI Service

#### If you use vLLM:

```bash
DATA='{"model": "haoranxu/ALMA-13B", "prompt": "What is Deep Learning?", "max_tokens": 100, "temperature": 0}'

curl http://${HOST_IP}:${TRANSLATION_VLLM_SERVICE_PORT}/v1/chat/completions \
  -X POST \
  -d "$DATA" \
  -H 'Content-Type: application/json'
```

Checking the response from the service. The response should be similar to JSON:

```json
{
  "id": "cmpl-059dd7fb311a46c2b807e0b3315e730c",
  "object": "text_completion",
  "created": 1743063706,
  "model": "haoranxu/ALMA-13B",
  "choices": [
    {
      "index": 0,
      "text": " Deep Learning is a subset of machine learning. It attempts to mimic the way the human brain learns. Deep Learning is a subset of machine learning. It attempts to mimic the way the human brain learns. Deep Learning is a subset of machine learning. It attempts to mimic the way the human brain learns. Deep Learning is a subset of machine learning. It attempts to mimic the way the human brain learns. Deep Learning is a subset of machine learning",
      "logprobs": null,
      "finish_reason": "length",
      "stop_reason": null,
      "prompt_logprobs": null
    }
  ],

  "usage": {
    "prompt_tokens": 6,
    "total_tokens": 106,
    "completion_tokens": 100,
    "prompt_tokens_details": null
  }
}
```

If the service response has a meaningful response in the value of the "choices.message.content" key,
then we consider the vLLM service to be successfully launched

#### If you use TGI:

```bash
DATA='{"inputs":"What is Deep Learning?",'\
'"parameters":{"max_new_tokens":256,"do_sample": true}}'

curl http://${HOST_IP}:${TRANSLATION_TGI_SERVICE_PORT}/generate \
  -X POST \
  -d "$DATA" \
  -H 'Content-Type: application/json'
```

Checking the response from the service. The response should be similar to JSON:

```json
{
  "generated_text": "\n\n What can it Do? What's the Hype? What Should You Do If"
}
```

If the service response has a meaningful response in the value of the "generated_text" key,
then we consider the TGI service to be successfully launched

### 2. Validate the LLM Service

```bash
DATA='{"query":"What is Deep Learning?",'\
'"max_tokens":32,"top_k":10,"top_p":0.95,"typical_p":0.95,"temperature":0.01,'\
'"repetition_penalty":1.03,"stream":false}'

curl http://${HOST_IP}:${TRANSLATION_LLM_SERVICE_PORT}/v1/chat/completions \
  -X POST \
  -d "$DATA" \
  -H 'Content-Type: application/json'
```

Checking the response from the service. The response should be similar to JSON:

```json
{
  "id": "",
  "choices": [
    {
      "finish_reason": "length",
      "index": 0,
      "logprobs": null,
      "text": " Deep Learning is a subset of machine learning. It attempts to mimic the way the human brain learns. Deep Learning is a subset of machine learning."
    }
  ],
  "created": 1742978568,
  "model": "haoranxu/ALMA-13B",
  "object": "text_completion",
  "system_fingerprint": "2.3.1-sha-a094729-rocm",
  "usage": {
    "completion_tokens": 32,
    "prompt_tokens": 6,
    "total_tokens": 38,
    "completion_tokens_details": null,
    "prompt_tokens_details": null
  }
}
```

### 3. Validate Nginx Service

```bash
DATA='{"language_from": "Chinese","language_to": "English","source_language": "我爱机器翻译。"}'

curl http://${HOST_IP}:${TRANSLATION_LLM_SERVICE_PORT}/v1/translation  \
  -d "$DATA" \
  -H 'Content-Type: application/json'
```

Checking the response from the service. The response should be similar to JSON:

```textmate
data: {"id":"","choices":[{"finish_reason":"","index":0,"logprobs":null,"text":" I"}],"created":1743062099,"model":"haoranxu/ALMA-13B","object":"text_completion","system_fingerprint":"2.3.1-sha-a094729-rocm","usage":null}

data: {"id":"","choices":[{"finish_reason":"","index":0,"logprobs":null,"text":" love"}],"created":1743062099,"model":"haoranxu/ALMA-13B","object":"text_completion","system_fingerprint":"2.3.1-sha-a094729-rocm","usage":null}

data: {"id":"","choices":[{"finish_reason":"","index":0,"logprobs":null,"text":" machine"}],"created":1743062099,"model":"haoranxu/ALMA-13B","object":"text_completion","system_fingerprint":"2.3.1-sha-a094729-rocm","usage":null}

data: {"id":"","choices":[{"finish_reason":"","index":0,"logprobs":null,"text":" translation"}],"created":1743062099,"model":"haoranxu/ALMA-13B","object":"text_completion","system_fingerprint":"2.3.1-sha-a094729-rocm","usage":null}

data: {"id":"","choices":[{"finish_reason":"","index":0,"logprobs":null,"text":"."}],"created":1743062099,"model":"haoranxu/ALMA-13B","object":"text_completion","system_fingerprint":"2.3.1-sha-a094729-rocm","usage":null}

data: {"id":"","choices":[{"finish_reason":"eos_token","index":0,"logprobs":null,"text":"</s>"}],"created":1743062099,"model":"haoranxu/ALMA-13B","object":"text_completion","system_fingerprint":"2.3.1-sha-a094729-rocm","usage":{"completion_tokens":6,"prompt_tokens":3071,"total_tokens":3077,"completion_tokens_details":null,"prompt_tokens_details":null}}

data: [DONE]
```

### 4. Validate MegaService

```bash
DATA='{"language_from": "Chinese","language_to": "English","source_language": "我爱机器翻译。"}'

curl http://${HOST_IP}:${TRANSLATION_BACKEND_SERVICE_PORT}/v1/translation \
  -H "Content-Type: application/json" \
  -d "$DATA"
```

Checking the response from the service. The response should be similar to JSON:

```textmate
data: {"id":"","choices":[{"finish_reason":"","index":0,"logprobs":null,"text":" I"}],"created":1742978968,"model":"haoranxu/ALMA-13B","object":"text_completion","system_fingerprint":"2.3.1-sha-a094729-rocm","usage":null}

data: {"id":"","choices":[{"finish_reason":"","index":0,"logprobs":null,"text":" love"}],"created":1742978968,"model":"haoranxu/ALMA-13B","object":"text_completion","system_fingerprint":"2.3.1-sha-a094729-rocm","usage":null}

data: {"id":"","choices":[{"finish_reason":"","index":0,"logprobs":null,"text":" machine"}],"created":1742978968,"model":"haoranxu/ALMA-13B","object":"text_completion","system_fingerprint":"2.3.1-sha-a094729-rocm","usage":null}

data: {"id":"","choices":[{"finish_reason":"","index":0,"logprobs":null,"text":" translation"}],"created":1742978968,"model":"haoranxu/ALMA-13B","object":"text_completion","system_fingerprint":"2.3.1-sha-a094729-rocm","usage":null}

data: {"id":"","choices":[{"finish_reason":"","index":0,"logprobs":null,"text":"."}],"created":1742978968,"model":"haoranxu/ALMA-13B","object":"text_completion","system_fingerprint":"2.3.1-sha-a094729-rocm","usage":null}

data: {"id":"","choices":[{"finish_reason":"eos_token","index":0,"logprobs":null,"text":"</s>"}],"created":1742978968,"model":"haoranxu/ALMA-13B","object":"text_completion","system_fingerprint":"2.3.1-sha-a094729-rocm","usage":{"completion_tokens":6,"prompt_tokens":3071,"total_tokens":3077,"completion_tokens_details":null,"prompt_tokens_details":null}}

data: [DONE]

```

If the response text is similar to the one above, then we consider the service verification successful.

### 5. Validate Frontend

To access the UI, use the URL - http://${EXTERNAL_HOST_IP}:${TRANSLATION_FRONTEND_SERVICE_PORT} A page should open when you click through to this address:
![UI start page](../../../../assets/img/translation-ui-starting-page.png)

If a page of this type has opened, then we believe that the service is running and responding, and we can proceed to functional UI testing.

Let's enter the task for the service in the "Input" field. For example, "我爱机器翻译" with selected "German" as language source and press Enter. After that, a page with the result of the task should open:

![UI start page](../../../../assets/img/translation-ui-response-example.png)
If the result shown on the page is correct, then we consider the verification of the UI service to be successful.

### 6. Stop application

#### If you use vLLM

```bash
cd ~/translation-install/GenAIExamples/Translation/docker_compose/amd/gpu/rocm
docker compose -f compose_vllm.yaml down
```

#### If you use TGI

```bash
cd ~/translation-install/GenAIExamples/Translation/docker_compose/amd/gpu/rocm
docker compose -f compose.yaml down
```
