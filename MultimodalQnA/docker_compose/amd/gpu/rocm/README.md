# Build and Deploy MultimodalQnA Application on AMD GPU (ROCm)

This document outlines the deployment process for a MultimodalQnA application utilizing the [GenAIComps](https://github.com/opea-project/GenAIComps.git) microservice pipeline on AMD server with ROCm GPUs. The steps include Docker image creation, container deployment via Docker Compose, and service execution to integrate microservices such as `multimodal_embedding` that employs [BridgeTower](https://huggingface.co/BridgeTower/bridgetower-large-itm-mlm-gaudi) model as embedding model, `multimodal_retriever`, `lvm`, and `multimodal-data-prep`. We will publish the Docker images to Docker Hub soon, it will simplify the deployment process for this service.

For detailed information about these instance types, you can refer to this [link](https://aws.amazon.com/ec2/instance-types/m7i/). Once you've chosen the appropriate instance type, proceed with configuring your instance settings, including network configurations, security groups, and storage options.

After launching your instance, you can connect to it using SSH (for Linux instances) or Remote Desktop Protocol (RDP) (for Windows instances). From there, you'll have full access to your Xeon server, allowing you to install, configure, and manage your applications as needed.

## Build Docker Images

### 1. Build Docker Image

- #### Create application install directory and go to it:

  ```bash
  mkdir ~/multimodalqna-install && cd multimodalqna-install
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
  cd ~/multimodalqna-install/GenAIExamples/MultimodalQnA/docker_image_build
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
  service_list="multimodalqna multimodalqna-ui embedding-multimodal-bridgetower embedding retriever lvm dataprep whisper vllm-rocm"
  ```

  #### TGI-based application

  ```bash
  service_list="multimodalqna multimodalqna-ui embedding-multimodal-bridgetower embedding retriever lvm dataprep whisper"
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
    - opea/lvm:latest
    - opea/multimodalqna:latest
    - opea/multimodalqna-ui:latest
    - opea/dataprep:latest
    - opea/embedding:latest
    - opea/embedding-multimodal-bridgetower:latest
    - opea/retriever:latest
    - opea/whisper:latest

  ##### TGI-based application:

  - ghcr.io/huggingface/text-generation-inference:2.4.1-rocm
    - opea/lvm:latest
    - opea/multimodalqna:latest
    - opea/multimodalqna-ui:latest
    - opea/dataprep:latest
    - opea/embedding:latest
    - opea/embedding-multimodal-bridgetower:latest
    - opea/retriever:latest
    - opea/whisper:latest

---

## Deploy the MultimodalQnA Application

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
cd ~/multimodalqna-install/GenAIExamples/MultimodalQnA/docker_compose/amd/gpu/rocm
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

#### Required Models

By default, the multimodal-embedding and LVM models are set to a default value as listed below:

| Service   | Model                                       |
| --------- | ------------------------------------------- |
| embedding | BridgeTower/bridgetower-large-itm-mlm-gaudi |
| LVM       | llava-hf/llava-1.5-7b-hf                    |
| LVM       | Xkev/Llama-3.2V-11B-cot                     |

Note:

For AMD ROCm System "Xkev/Llama-3.2V-11B-cot" is recommended to run on ghcr.io/huggingface/text-generation-inference:2.4.1-rocm

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

- multimodalqna-vllm-service
- multimodalqna-lvm
- multimodalqna-backend-server
- multimodalqna-gradio-ui-server
- whisper-service
- embedding-multimodal-bridgetower
- redis-vector-db
- embedding
- retriever-redis
- dataprep-multimodal-redis

##### If you use TGI:

- tgi-llava-rocm-server
- multimodalqna-lvm
- multimodalqna-backend-server
- multimodalqna-gradio-ui-server
- whisper-service
- embedding-multimodal-bridgetower
- redis-vector-db
- embedding
- retriever-redis
- dataprep-multimodal-redis

---

## Validate the Services

### 1. Validate the vLLM/TGI Service

#### If you use vLLM:

```bash
DATA='{"model": "Xkev/Llama-3.2V-11B-cot", '\
'"messages": [{"role": "user", "content": ""}], "max_tokens": 256}'

curl http://${HOST_IP}:${MULTIMODALQNA_VLLM_SERVICE_PORT}/v1/chat/completions \
  -X POST \
  -d "$DATA" \
  -H 'Content-Type: application/json'
```

Checking the response from the service. The response should be similar to JSON:

```json

```

If the service response has a meaningful response in the value of the "choices.message.content" key,
then we consider the vLLM service to be successfully launched

#### If you use TGI:

```bash
DATA='{"inputs":"",'\
'"parameters":{"max_new_tokens":256,"do_sample": true}}'

curl http://${HOST_IP}:${MULTIMODALQNA_TGI_SERVICE_PORT}/generate \
  -X POST \
  -d "$DATA" \
  -H 'Content-Type: application/json'
```

Checking the response from the service. The response should be similar to JSON:

```json

```

If the service response has a meaningful response in the value of the "generated_text" key,
then we consider the TGI service to be successfully launched

### 2. Validate the LLM Service

```bash
DATA='{"query":"",'\
'"max_tokens":256,"top_k":10,"top_p":0.95,"typical_p":0.95,"temperature":0.01,'\
'"repetition_penalty":1.03,"stream":false}'

curl http://${HOST_IP}:${MULTIMODALQNA_LLM_SERVICE_PORT}/v1/chat/completions \
  -X POST \
  -d "$DATA" \
  -H 'Content-Type: application/json'
```

Checking the response from the service. The response should be similar to JSON:

```json

```

If the service response has a meaningful response in the value of the "choices.text" key,
then we consider the vLLM service to be successfully launched

### 3. Validate the MegaService

```bash
DATA='{"messages": "Implement a high-level API for a TODO list application. '\
'The API takes as input an operation request and updates the TODO list in place. '\
'If the request is invalid, raise an exception."}'

curl http://${HOST_IP}:${MULTIMODALQNA_BACKEND_SERVICE_PORT}/v1/multimodalqna \
  -H "Content-Type: application/json" \
  -d "$DATA"
```

Checking the response from the service. The response should be similar to text:

```textmate

```

If the output lines in the "choices.text" keys contain words (tokens) containing meaning, then the service is considered launched successfully.

### 4. Validate MicroServices

```bash
# whisper service
curl http://${host_ip}:7066/v1/asr \
  -X POST \
  -d '{"audio": "UklGRigAAABXQVZFZm10IBIAAAABAAEARKwAAIhYAQACABAAAABkYXRhAgAAAAEA"}' \
  -H 'Content-Type: application/json'
```

Checking the response from the service. The response should be similar to text:

```textmate

```

### 4. Validate the Frontend (UI)

To access the UI, use the URL - http://${EXTERNAL_HOST_IP}:${MULTIMODALQNA_UI_SERVICE_PORT}
A page should open when you click through to this address:

![UI start page](../../../../assets/img/ui-starting-page.png)

If a page of this type has opened, then we believe that the service is running and responding,
and we can proceed to functional UI testing.

### 5. Stop application

##### If you use vLLM

```bash
cd ~/multimodalqna-install/GenAIExamples/MultimodalQnA/docker_compose/amd/gpu/rocm
docker compose -f compose_vllm.yaml down
```

##### If you use TGI

```bash
cd ~/multimodalqna-install/GenAIExamples/MultimodalQnA/docker_compose/amd/gpu/rocm
docker compose -f compose.yaml down
```
