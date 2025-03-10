Copyright (C) 2024 Advanced Micro Devices, Inc.

# Deploy FaqGen application

## 1. Clone repo and build Docker images

### 1.1. Cloning GenAIComps repo

Create an empty directory in home directory and navigate to it:

```bash
mkdir -p ~/faqgen-test && cd ~/faqgen-test
```

Cloning GenAIExamples repo for build Docker images:

```bash
git clone https://github.com/opea-project/GenAIExamples.git
```

### 1.2. Navigate to repo directory and switching to the desired version of the code:

If you are using the main branch, then you do not need to make the transition, the main branch is used by default

```bash
cd ~/faqgen-test/GenAIExamples/FaqGen/docker_image_build
git clone https://github.com/opea-project/GenAIComps.git
```

If you are using a specific branch or tag, then we perform git checkout to the desired version.

```bash
### Replace "v1.2" with the code version you need (branch or tag)
cd cd ~/faqgen-test/GenAIExamples/FaqGen/docker_image_build && git checkout v1.2
git clone https://github.com/opea-project/GenAIComps.git
```

### 1.3. Build Docker images repo

#### Build Docker image:

```bash
docker compose -f build.yaml build --no-cache
```

### 1.5. Checking for the necessary Docker images

After assembling the images, you can check their presence in the list of available images using the command:

```bash
docker image ls
```

The output of the command should contain images:

- opea/llm-vllm-rocm:latest
- opea/llm-faqgen:latest
- opea/faqgen:latest
- opea/faqgen-ui:latest

## 2. Set deploy environment variables

### Setting variables in the operating system environment

#### Set variables:

```bash
### Replace the string 'your_huggingfacehub_token' with your HuggingFacehub repository access token.
export HUGGINGFACEHUB_API_TOKEN='your_huggingfacehub_token'
```

### Setting variables in the file set_env_vllm.sh

```bash
cd cd cd ~/faqgen-test/GenAIExamples/FaqGen/docker_compose-/amd/gpu/rocm
### The example uses the Nano text editor. You can use any convenient text editor
nano set_env_vllm.sh
```

Set the values of the variables:

- **HOST_IP, HOST_IP_EXTERNAL** - These variables are used to configure the name/address of the service in the operating system environment for the application services to interact with each other and with the outside world.

  If your server uses only an internal address and is not accessible from the Internet, then the values for these two variables will be the same and the value will be equal to the server's internal name/address.

  If your server uses only an external, Internet-accessible address, then the values for these two variables will be the same and the value will be equal to the server's external name/address.

  If your server is located on an internal network, has an internal address, but is accessible from the Internet via a proxy/firewall/load balancer, then the HOST_IP variable will have a value equal to the internal name/address of the server, and the EXTERNAL_HOST_IP variable will have a value equal to the external name/address of the proxy/firewall/load balancer behind which the server is located.

  We set these values in the file set_env_vllm.sh

- **Variables with names like "%%%%\_PORT"** - These variables set the IP port numbers for establishing network connections to the application services.
  The values shown in the file set_env_vllm.sh they are the values used for the development and testing of the application, as well as configured for the environment in which the development is performed. These values must be configured in accordance with the rules of network access to your environment's server, and must not overlap with the IP ports of other applications that are already in use.

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
cd cd ~/faqgen-test/GenAIExamples/FaqGen/docker_compose/amd/gpu/rocm/
docker compose -f compose_vllm up -d
```

After starting the containers, you need to view their status with the command:

```bash
docker ps
```

The following containers should be running:

- faqgen-vllm-service
- faqgen-llm-server
- faqgen-backend-server
- faqgen-ui-server

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
  curl http://${HOST_IP}:${FAQGEN_VLLM_SERVICE_PORT}/v1/completions \
  -H "Content-Type: application/json" \
  -d '{
      "model": "meta-llama/Meta-Llama-3-8B-Instruct",
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
    "model": "meta-llama/Meta-Llama-3-8B-Instruct",
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

