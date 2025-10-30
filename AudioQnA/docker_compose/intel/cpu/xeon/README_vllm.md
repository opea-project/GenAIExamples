Copyright (C) 2025 Advanced Micro Devices, Inc.

# Deploy AudioQnA application

## 1. Clone repo and build Docker images

### 1.1. Cloning repo

Create an empty directory in home directory and navigate to it:

```bash
mkdir -p ~/audioqna-test && cd ~/audioqna-test
```

Cloning GenAIExamples repo for build Docker images:

```bash
git clone https://github.com/opea-project/GenAIExamples.git
```

### 1.2. Navigate to repo directory and switching to the desired version of the code:

If you are using the main branch, then you do not need to make the transition, the main branch is used by default

```bash
cd GenAIExamples/AudioQnA/docker_image_build
git clone https://github.com/opea-project/GenAIComps.git
```

If you are using a specific branch or tag, then we perform git checkout to the desired version.

```bash
### Replace "v1.3" with the code version you need (branch or tag)
cd GenAIExamples/AudioQnA/docker_image_build && git checkout v1.3
git clone https://github.com/opea-project/GenAIComps.git
```

### 1.3. Build Docker images repo

#### Build Docker image:

```bash
service_list="audioqna audioqna-ui whisper speecht5 vllm-rocm"
docker compose -f build.yaml build --no-cache
```

### 1.4. Checking for the necessary Docker images

After assembling the images, you can check their presence in the list of available images using the command:

```bash
docker image ls
```

The output of the command should contain images:

- opea/whisper:latest
- opea/speecht5:latest
- opea/vllm-rocm:latest
- opea/audioqna:latest
- opea/audioqna-ui:latest

## 2. Set deploy environment variables

### Setting variables in the operating system environment

#### Set variables:

```bash
### Replace the string 'your_huggingfacehub_token' with your HuggingFacehub repository access token.
export HF_TOKEN='your_huggingfacehub_token'
```

### Setting variables in the file set_env_vllm.sh

```bash
cd ~/searchqna-test/GenAIExamples/SearchQnA/docker_compose/amd/gpu/rocm
### The example uses the Nano text editor. You can use any convenient text editor
nano set_env_vllm.sh
```

Set the values of the variables:

- **host_ip, external_host_ip** - These variables are used to configure the name/address of the service in the operating system environment for the application services to interact with each other and with the outside world.

  If your server uses only an internal address and is not accessible from the Internet, then the values for these two variables will be the same and the value will be equal to the server's internal name/address.

  If your server uses only an external, Internet-accessible address, then the values for these two variables will be the same and the value will be equal to the server's external name/address.

  If your server is located on an internal network, has an internal address, but is accessible from the Internet via a proxy/firewall/load balancer, then the host_ip variable will have a value equal to the internal name/address of the server, and the external_host_ip variable will have a value equal to the external name/address of the proxy/firewall/load balancer behind which the server is located.

  We set these values in the file set_env_vllm.sh

- **Variables with names like "%%%%\_PORT"** - These variables set the IP port numbers for establishing network connections to the application services.
  The values shown in the file set_env_vllm.sh they are the values used for the development and testing of the application, as well as configured for the environment in which the development is performed. These values must be configured in accordance with the rules of network access to your environment's server, and must not overlap with the IP ports of other applications that are already in use.

If you are in a proxy environment, also set the proxy-related environment variables:

```bash
export http_proxy="Your_HTTP_Proxy"
export https_proxy="Your_HTTPs_Proxy"
```

## 3. Deploy application

### 3.1. Deploying applications using Docker Compose

```bash
cd GenAIExamples/AudioQnA/docker_compose/intel/cpu/xeon/
docker compose up -d
```

After starting the containers, you need to view their status with the command:

```bash
docker ps
```

The following containers should be running:

- whisper-service
- speecht5-service
- audioqna-vllm-service
- audioqna-backend-server
- audioqna-ui-server

Containers should not restart.

(Optional) Enabling monitoring using the command:

```bash
docker compose -f compose.yaml -f compose.monitoring.yaml up -d
```

#### 3.1.1. Configuring GPU forwarding

By default, in the Docker Compose file, compose_vllm.yaml is configured to forward all GPUs to the audioqna-vllm-service container.
To use certain GPUs, you need to configure the forwarding of certain devices from the host system to the container.
The configuration must be done in:

```yaml
services:
  #######
  audioqna-vllm-service:
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

#### 3.2.1. Checking audioqna-vllm-service

Verification is performed in two ways:

- Checking the container logs

  ```bash
  docker logs audioqna-vllm-service
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
  ### Replace 18110 with the value set in the startup script in the variable VLLM_SERVICE_PORT
  curl http://${host_ip}:${VLLM_SERVICE_PORT}/v1/completions \
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
  The value of "choice.text" must contain a response from the service that makes sense.
  If such a response is present, then the search-vllm-service is considered verified.

#### 3.2.2. Checking whisper-service

Сhecking the response from the service

```bash
wget https://github.com/intel/intel-extension-for-transformers/raw/main/intel_extension_for_transformers/neural_chat/assets/audio/sample.wav
curl http://${host_ip}:${WHISPER_SERVER_PORT}/v1/audio/transcriptions \
  -H "Content-Type: multipart/form-data" \
  -F file="@./sample.wav" \
  -F model="openai/whisper-small"
```

The response from the service must be in the form of JSON:

```json
{ "text": "who is pat gelsinger" }
```

If the value of the text key is "who is pat gelsinger", then we consider the service to be successfully launched.

#### 3.2.3. Checking speecht5-service

Сhecking the response from the service

```bash
curl http://${host_ip}:${SPEECHT5_SERVER_PORT}/v1/audio/speech -XPOST -d '{"input": "Who are you?"}' -H 'Content-Type: application/json' --output speech.mp3
```

The result of the request is a speech.mp3 file. If you hear the phrase "Who are you?" while listening to the file, the service is considered successfully launched

#### 3.2.4. Checking audioqna-backend-server

Сhecking the response from the service

```bash
curl http://${host_ip}:${BACKEND_SERVICE_PORT}/v1/audioqna \
  -X POST \
  -d '{"audio": "UklGRigAAABXQVZFZm10IBIAAAABAAEARKwAAIhYAQACABAAAABkYXRhAgAAAAEA", "max_tokens":64, "voice":"default"}' \
  -H 'Content-Type: application/json' | sed 's/^"//;s/"$//' | base64 -d > output.wav
```

The result of the request is the output.wav file. If, when listening to it, you hear the answer that it is an assistant and a request for a new question, then the service is considered started.
