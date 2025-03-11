Copyright (C) 2024 Advanced Micro Devices, Inc.

# Deploy Translation application

## 1. Clone repo and build Docker images

### 1.1. Cloning GenAIComps repo

Create an empty directory in home directory and navigate to it:

```bash
mkdir ~/translation-apps && cd ~/translation-apps
```

Cloning GenAIExamples repo for build Docker images:

```bash
git clone https://github.com/opea-project/GenAIExamples.git
```

### 1.2. Navigate to repo directory and switching to the desired version of the code:

If you are using the main branch, then you do not need to make the transition, the main branch is used by default

```bash
cd GenAIExamples
```

If you are using a specific branch or tag, then we perform git checkout to the desired version.

```bash
### Replace "v1.2" with the code version you need (branch or tag)
cd GenAIExamples && git checkout v1.2
```

### 1.3. Build Docker images

```bash
cd docker_image_build
git clone git clone https://github.com/opea-project/GenAIComps.git
service_list="translation translation-ui llm-textgen nginx vllm-rocm"
docker compose -f build.yaml build ${service_list} --no-cache
```

### 1.8. Checking for the necessary Docker images

After assembling the images, you can check their presence in the list of available images using the command:

```bash
docker image ls
```

The output of the command should contain images:

- opea/llm-vllm-rocm:latest
- opea/llm-textgen:latest
- opea/translation:latest
- opea/translation-ui:latest
- opea/nginx:latest

## 2. Set deploy environment variables

### Setting variables in the operating system environment

#### Set variable HUGGINGFACEHUB_API_TOKEN:

```bash
### Replace the string 'your_huggingfacehub_token' with your HuggingFacehub repository access token.
export HUGGINGFACEHUB_API_TOKEN='your_huggingfacehub_token'
```

#### Set variables value in set_env_vllm.sh file:

```bash
cd ~/translation-apps/GenAIExamples/Translation/docker_compose/amd/gpu/rocm
### The example uses the Nano text editor. You can use any convenient text editor
nano set_env_vllm.sh
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

  We set these values in the file set_env_vllm.sh

- **Variables with names like "%%%%\_PORT"** - These variables set the IP port numbers for establishing network connections to the application services.
  The values shown in the file set_env_vllm.sh they are the values used for the development and testing of the application, as well as configured for the environment in which the development is performed. These values must be configured in accordance with the rules of network access to your environment's server, and must not overlap with the IP ports of other applications that are already in use.

#### Run set environment script:

```bash
. set_env_vllm.sh
```

## 3. Deploy application

### 3.1. Deploying applications using Docker Compose

```bash
docker compose -f compose_vllm.yaml up -d --force-recreate
```

After starting the containers, you need to view their status with the command:

```bash
docker compose -f compose_vllm.yaml ps
```

The following containers should be running:

- translation-nginx-server
- translation-ui-server
- translation-backend-server
- translation-llm-textgen-server
- translation-vllm-service

Containers should not restart.

#### 3.1.1. Configuring GPU forwarding

By default, in the Docker Compose file, compose_vllm.yaml is configured to forward all GPUs to the translation-vllm-service container. To use certain GPUs, you need to configure the forwarding of certain devices from the host system to the container.
The configuration must be done in:

```yaml
services:
  #######
  translation-vllm-service:
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

#### 3.2.1. Checking translation-vllm-service

Verification is performed in two ways:

- Checking the container logs

  ```bash
  docker logs translation-vllm-service
  ```

  A message like this should appear in the logs:

  ```textmate
  INFO:     Started server process [1]
  INFO:     Waiting for application startup.
  INFO:     Application startup complete.
  INFO:     Uvicorn running on http://0.0.0.0:8011 (Press CTRL+C to quit)
  ```

- Сhecking the response from the service
  ```bash
  ### curl request
  curl http://${HOST_IP}:${TRANSLATION_VLLM_SERVICE_PORT}/v1/completions \
  -H "Content-Type: application/json" \
  -d '{
      "model": "haoranxu/ALMA-13B",
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
    "model": "haoranxu/ALMA-13B",
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
  The value of "choice.text" must contain a response from the service that makes sense.
  If such a response is present, then the translation-vllm-service is considered verified.

#### 3.2.2. Checking translation-llm

It is performed using requests to the service

```bash
curl http://${HOST_IP}:${TRANSLATION_LLM_PORT}/v1/chat/completions \
  -X POST \
  -d '{"query":"Translate this from Chinese to English:\nChinese: 我爱机器翻译。\nEnglish:"}' \
  -H 'Content-Type: application/json'
```

The response from the service must be in the form of JSON:
```textmate
data: {"id":"cmpl-8b5634bc3b97466f8f166dd71d35a7f0","choices":[{"finish_reason":null,"index":0,"logprobs":null,"text":"I","stop_reason":null}],"created":1741677287,"model":"haoranxu/ALMA-13B","object":"text_completion","system_fingerprint":null,"usage":null}
data: {"id":"cmpl-8b5634bc3b97466f8f166dd71d35a7f0","choices":[{"finish_reason":null,"index":0,"logprobs":null,"text":" love","stop_reason":null}],"created":1741677287,"model":"haoranxu/ALMA-13B","object":"text_completion","system_fingerprint":null,"usage":null}
data: {"id":"cmpl-8b5634bc3b97466f8f166dd71d35a7f0","choices":[{"finish_reason":null,"index":0,"logprobs":null,"text":" machine","stop_reason":null}],"created":1741677287,"model":"haoranxu/ALMA-13B","object":"text_completion","system_fingerprint":null,"usage":null}
data: {"id":"cmpl-8b5634bc3b97466f8f166dd71d35a7f0","choices":[{"finish_reason":null,"index":0,"logprobs":null,"text":" translation","stop_reason":null}],"created":1741677287,"model":"haoranxu/ALMA-13B","object":"text_completion","system_fingerprint":null,"usage":null}
data: {"id":"cmpl-8b5634bc3b97466f8f166dd71d35a7f0","choices":[{"finish_reason":null,"index":0,"logprobs":null,"text":".","stop_reason":null}],"created":1741677287,"model":"haoranxu/ALMA-13B","object":"text_completion","system_fingerprint":null,"usage":null}
data: {"id":"cmpl-8b5634bc3b97466f8f166dd71d35a7f0","choices":[{"finish_reason":"stop","index":0,"logprobs":null,"text":"","stop_reason":null}],"created":1741677287,"model":"haoranxu/ALMA-13B","object":"text_completion","system_fingerprint":null,"usage":null}
data: [DONE]
```

The value of "choices.text" must contain a response from the service that makes sense.
If such a response is present, then the translation-llm is considered verified.

#### 3.2.3. Checking translation-backend-server (Megaservice)

It is performed using requests to the service

```bash
curl http://${HOST_IP}:${TRANSLATION_BACKEND_SERVICE_PORT}/v1/translation \
    -H "Content-Type: application/json" -d '{
    "language_from": "Chinese","language_to": "English","source_language": "我爱机器翻译。"}'
```

The response from the service must be in the form of JSON:

```textmate
data: {"id":"cmpl-009a6002085e4893b6e1e7f2f3eadcb8","choices":[{"finish_reason":null,"index":0,"logprobs":null,"text":" I","stop_reason":null}],"created":1741677514,"model":"haoranxu/ALMA-13B","object":"text_completion","system_fingerprint":null,"usage":null}
data: {"id":"cmpl-009a6002085e4893b6e1e7f2f3eadcb8","choices":[{"finish_reason":null,"index":0,"logprobs":null,"text":" love","stop_reason":null}],"created":1741677514,"model":"haoranxu/ALMA-13B","object":"text_completion","system_fingerprint":null,"usage":null}
data: {"id":"cmpl-009a6002085e4893b6e1e7f2f3eadcb8","choices":[{"finish_reason":null,"index":0,"logprobs":null,"text":" machine","stop_reason":null}],"created":1741677514,"model":"haoranxu/ALMA-13B","object":"text_completion","system_fingerprint":null,"usage":null}
data: {"id":"cmpl-009a6002085e4893b6e1e7f2f3eadcb8","choices":[{"finish_reason":null,"index":0,"logprobs":null,"text":" translation","stop_reason":null}],"created":1741677514,"model":"haoranxu/ALMA-13B","object":"text_completion","system_fingerprint":null,"usage":null}
data: {"id":"cmpl-009a6002085e4893b6e1e7f2f3eadcb8","choices":[{"finish_reason":null,"index":0,"logprobs":null,"text":".","stop_reason":null}],"created":1741677514,"model":"haoranxu/ALMA-13B","object":"text_completion","system_fingerprint":null,"usage":null}
data: {"id":"cmpl-009a6002085e4893b6e1e7f2f3eadcb8","choices":[{"finish_reason":"stop","index":0,"logprobs":null,"text":"","stop_reason":null}],"created":1741677514,"model":"haoranxu/ALMA-13B","object":"text_completion","system_fingerprint":null,"usage":null}
data: [DONE]
```

The value of "choices.text" must contain a response from the service that makes sense.
If such a response is present, then the translation-backend-server is considered verified.
