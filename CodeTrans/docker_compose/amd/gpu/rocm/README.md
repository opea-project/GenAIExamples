# Build and Deploy CodeTrans Application on AMD GPU (ROCm)

## Build Docker Images

### 1. Build Docker Image

```bash
# Create application install directory and go to it
mkdir ~/codetrans-install && cd codetrans-install
# Clone the repository GenAIExamples
git clone https://github.com/opea-project/GenAIExamples.git
# If you need to use a specific branch/tag of the GenAIExamples repository, then (v1.2 replace with its own value):
git clone https://github.com/opea-project/GenAIExamples.git && cd GenAIExamples && git checkout v1.2
# Go to build directory
cd ~/codetrans-install/GenAIExamples/CodeTrans/docker_image_build
# We are cleaning up the GenAIComps repository if it was previously cloned in this directory.
echo Y | rm -R GenAIComps
# Clone the repository GenAIComps
git clone https://github.com/opea-project/GenAIComps.git
# Setting the list of images for the build (from the build file.yaml)
# If you want to deploy a vLLM-based or TGI-based application, then the set of services is installed as follows:
# vLLM-based application
service_list="vllm-rocm llm-textgen codetrans codetrans-ui nginx"
# TGI-based application
service_list="llm-textgen codetrans codetrans-ui nginx"
# Optional. Pull TGI Docker Image (Do this if you want to use TGI)
docker pull ghcr.io/huggingface/text-generation-inference:2.3.1-rocm
# Build Docker Images
docker compose -f build.yaml build ${service_list} --no-cache
```

After the build, we check the list of images with the command:

```bash
docker image ls
```

The list of images should include:

#### vLLM-based application:

- opea/vllm-rocm:latest
- opea/llm-textgen:latest
- opea/codetrans:latest
- opea/codetrans-ui:latest
- opea/nginx:latest

#### TGI-based application:

- ghcr.io/huggingface/text-generation-inference:2.3.1-rocm
- opea/llm-textgen:latest
- opea/codetrans:latest
- opea/codetrans-ui:latest
- opea/nginx:latest

## Deploy the CodeTrans Application

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
   cd ~/codetrans-install/GenAIExamples/CodeTrans/docker_compose/amd/gpu/rocm
   ```

2. Configure environment variables:

## Set deploy environment variables

### Setting variables in the operating system environment

#### Set variable HUGGINGFACEHUB_API_TOKEN:

```bash
### Replace the string 'your_huggingfacehub_token' with your HuggingFacehub repository access token.
export HUGGINGFACEHUB_API_TOKEN='your_huggingfacehub_token'
```

#### Set variables value in set_env\*\*\*\*.sh file:

```bash
cd ~/codetrans-install/GenAIExamples/CodeGen/docker_compose/amd/gpu/rocm
### The example uses the Nano text editor. You can use any convenient text editor
# If you use vLLM
nano set_env_vllm.sh
# If you use TGI
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

  We set these values in the file set_env****.sh

- **Variables with names like "%%%%\_PORT"** - These variables set the IP port numbers for establishing network connections to the application services.
  The values shown in the file set_env.sh or set_env_vllm they are the values used for the development and testing of the application, as well as configured for the environment in which the development is performed. These values must be configured in accordance with the rules of network access to your environment's server, and must not overlap with the IP ports of other applications that are already in use.

# Set variables with script set_env\*\*\*\*.sh

```bash
# If you use vLLM
. set_env_vllm.sh
# If you use TGI
. set_env.sh
```

3. Start the services:

```bash
# If you use vLLM
docker compose -f compose_vllm.yaml up -d --force-recreate
# If you use TGI
docker compose -f compose.yaml up -d --force-recreate
```

## Validate the Services

### 1. Validate the vLLM/TGI Service

If you use vLLM:

```bash
curl http://${HOST_IP}:${CODEGEN_VLLM_SERVICE_PORT}/v1/chat/completions \
  -X POST \
  -d '{"model": "Qwen/Qwen2.5-Coder-7B-Instruct", "messages": [{"role": "user", "content": "What is Deep Learning?"}], "max_tokens": 17}' \
  -H 'Content-Type: application/json'
```

If you use TGI:

```bash
curl http://${HOST_IP}:${CODETRANS_TGI_SERVICE_PORT}/generate \
  -X POST \
  -d '{"inputs":"    ### System: Please translate the following Golang codes into  Python codes.    ### Original codes:    '\'''\'''\''Golang    \npackage main\n\nimport \"fmt\"\nfunc main() {\n    fmt.Println(\"Hello, World!\");\n    '\'''\'''\''    ### Translated codes:","parameters":{"max_new_tokens":17, "do_sample": true}}' \
  -H 'Content-Type: application/json'
```

### 2. Validate the LLM Service

```bash
curl http://${HOST_IP}:${CODETRANS_LLM_SERVICE_PORT}/v1/chat/completions \
  -X POST \
  -d '{"query":"    ### System: Please translate the following Golang codes into  Python codes.    ### Original codes:    '\'''\'''\''Golang    \npackage main\n\nimport \"fmt\"\nfunc main() {\n    fmt.Println(\"Hello, World!\");\n    '\'''\'''\''    ### Translated codes:"}' \
  -H 'Content-Type: application/json'
```

### 3. Validate the MegaService

```bash
curl http://${HOST_IP}:${CODEGEN_BACKEND_SERVICE_PORT}/v1/codetrans \
  -H "Content-Type: application/json" \
  -d '{"language_from": "Golang","language_to": "Python","source_code": "package main\n\nimport \"fmt\"\nfunc main() {\n    fmt.Println(\"Hello, World!\");\n}"}'
```
