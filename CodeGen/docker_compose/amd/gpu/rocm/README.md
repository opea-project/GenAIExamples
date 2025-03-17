Copyright (c) 2025 Advanced Micro Devices, Inc.

# Build and Deploy CodeGen Application on AMD GPU (ROCm)

## Build Docker Images

### 1. Build Docker Image

```bash
# Clone the repository GenAIExamples
git clone https://github.com/opea-project/GenAIExamples.git
# Go to build directory
cd GenAIExamples/CodeGen/docker_image_build
# We are cleaning up the GenAIComps repository if it was previously cloned in this directory.
echo Y | rm -R GenAIComps
# Clone the repository GenAIComps
git clone https://github.com/opea-project/GenAIComps.git
# Setting the list of images for the build (from the build file.yaml)
service_list="llm-textgen codegen codegen-ui"
# Build Docker Images
docker compose -f build.yaml build ${service_list} --no-cache
# Pull TGI Docker Image
docker pull ghcr.io/huggingface/text-generation-inference:2.3.1-rocm
```

After the build, we check the list of images with the command:
```bash
docker image ls
```

The list of images should include:

- ghcr.io/huggingface/text-generation-inference:2.3.1-rocm
- opea/llm-textgen:latest
- opea/codegen:latest
- opea/codegen-ui:latest

## Deploy the CodeGen Application

### Docker Compose Configuration for AMD GPUs

To enable GPU support for AMD GPUs, the following configuration is added to the Docker Compose file compose.yaml:

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

---

### Launch the Application

1. Navigate to the Docker Compose directory:

   ```bash
   cd GenAIExamples/CodeGen/docker_compose/amd/gpu/rocm
   ```

2. Configure environment variables:

## 2. Set deploy environment variables

### Setting variables in the operating system environment

#### Set variable HUGGINGFACEHUB_API_TOKEN:

```bash
### Replace the string 'your_huggingfacehub_token' with your HuggingFacehub repository access token.
export HUGGINGFACEHUB_API_TOKEN='your_huggingfacehub_token'
```

#### Set variables value in set_env_vllm.sh file:

```bash
cd GenAIExamples/CodeGen/docker_compose/amd/gpu/rocm
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

# Set variables with script set_env_vllm.sh
```bash
. set_env_vllm.sh
```

3. Start the services:

```bash
docker compose -f compose.yaml up -d --force-recreate
```

## Validate the Services

### 1. Validate the TGI Service

```bash
curl http://${HOST_IP}:${CODEGEN_TGI_SERVICE_PORT}/generate \
  -X POST \
  -d '{"inputs":"Implement a high-level API for a TODO list application. The API takes as input an operation request and updates the TODO list in place. If the request is invalid, raise an exception.","parameters":{"max_new_tokens":256, "do_sample": true}}' \
  -H 'Content-Type: application/json'
```

### 2. Validate the LLM Service

```bash
curl http://${HOST_IP}:${CODEGEN_LLM_SERVICE_PORT}/v1/chat/completions \
  -X POST \
  -d '{"query":"Implement a high-level API for a TODO list application. The API takes as input an operation request and updates the TODO list in place. If the request is invalid, raise an exception.","max_tokens":256,"top_k":10,"top_p":0.95,"typical_p":0.95,"temperature":0.01,"repetition_penalty":1.03,"stream":true}' \
  -H 'Content-Type: application/json'
```

### 3. Validate the MegaService

```bash
curl http://${HOST_IP}:${CODEGEN_BACKEND_SERVICE_PORT}/v1/codegen \
  -H "Content-Type: application/json" \
  -d '{
    "messages": "Implement a high-level API for a TODO list application. The API takes as input an operation request and updates the TODO list in place. If the request is invalid, raise an exception."
  }'
```



















Copyright (c) 2024 Advanced Micro Devices, Inc.

# Build and deploy CodeGen Application on AMD GPU (ROCm)

## Build images

### Build the LLM Docker Image

```bash
### Cloning repo
git clone https://github.com/opea-project/GenAIComps.git
cd GenAIComps

### Build Docker image
docker build -t opea/llm-textgen:latest --build-arg https_proxy=$https_proxy --build-arg http_proxy=$http_proxy -f comps/llms/src/text-generation/Dockerfile .
```

### Build the MegaService Docker Image

```bash
### Cloning repo
git clone https://github.com/opea-project/GenAIExamples
cd GenAIExamples/CodeGen

### Build Docker image
docker build -t opea/codegen:latest --build-arg https_proxy=$https_proxy --build-arg http_proxy=$http_proxy -f Dockerfile .
```

### Build the UI Docker Image

```bash
cd GenAIExamples/CodeGen/ui
### Build UI Docker image
docker build -t opea/codegen-ui:latest --build-arg https_proxy=$https_proxy --build-arg http_proxy=$http_proxy -f ./docker/Dockerfile .

### Build React UI Docker image (React UI allows you to use file uploads)
docker build --no-cache -t opea/codegen-react-ui:latest --build-arg https_proxy=$https_proxy --build-arg http_proxy=$http_proxy -f ./docker/Dockerfile.react .
```

It is recommended to use the React UI as it works for downloading files. The use of React UI is set in the Docker Compose file

## Deploy CodeGen Application

### Features of Docker compose for AMD GPUs

1. Added forwarding of GPU devices to the container TGI service with instructions:

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

In this case, all GPUs are thrown. To reset a specific GPU, you need to use specific device names cardN and renderN.

For example:

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

To find out which GPU device IDs cardN and renderN correspond to the same GPU, use the GPU driver utility

### Go to the directory with the Docker compose file

```bash
cd GenAIExamples/CodeGen/docker_compose/amd/gpu/rocm
```

### Set environments

In the file "GenAIExamples/CodeGen/docker_compose/amd/gpu/rocm/set_env.sh " it is necessary to set the required values. Parameter assignments are specified in the comments for each variable setting command

```bash
chmod +x set_env.sh
. set_env.sh
```

### Run services

```
docker compose up -d
```

# Validate the MicroServices and MegaService

## Validate TGI service

```bash
curl http://${HOST_IP}:${CODEGEN_TGI_SERVICE_PORT}/generate \
  -X POST \
  -d '{"inputs":"Implement a high-level API for a TODO list application. The API takes as input an operation request and updates the TODO list in place. If the request is invalid, raise an exception.","parameters":{"max_new_tokens":256, "do_sample": true}}' \
  -H 'Content-Type: application/json'
```

## Validate LLM service

```bash
curl http://${HOST_IP}:${CODEGEN_LLM_SERVICE_PORT}/v1/chat/completions\
  -X POST \
  -d '{"query":"Implement a high-level API for a TODO list application. The API takes as input an operation request and updates the TODO list in place. If the request is invalid, raise an exception.","max_tokens":256,"top_k":10,"top_p":0.95,"typical_p":0.95,"temperature":0.01,"repetition_penalty":1.03,"stream":true}' \
  -H 'Content-Type: application/json'
```

## Validate MegaService

```bash
curl http://${HOST_IP}:${CODEGEN_BACKEND_SERVICE_PORT}/v1/codegen -H "Content-Type: application/json" -d '{
  "messages": "Implement a high-level API for a TODO list application. The API takes as input an operation request and updates the TODO list in place. If the request is invalid, raise an exception."
  }'
```
