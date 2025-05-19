# Deploying CodeTrans on AMD ROCm GPU

This document outlines the single node deployment process for a CodeTrans application utilizing the [GenAIComps](https://github.com/opea-project/GenAIComps.git) microservices on Intel Xeon server and AMD GPU. The steps include pulling Docker images, container deployment via Docker Compose, and service execution using microservices `llm`.

Note: The default LLM is `Qwen/Qwen2.5-Coder-7B-Instruct`. Before deploying the application, please make sure either you've requested and been granted the access to it on [Huggingface](https://huggingface.co/Qwen/Qwen2.5-Coder-7B-Instruct) or you've downloaded the model locally from [ModelScope](https://www.modelscope.cn/models).

## Table of Contents

1. [CodeTrans Quick Start Deployment](#codetrans-quick-start-deployment)
2. [CodeTrans Docker Compose Files](#codetrans-docker-compose-files)
3. [Validate Microservices](#validate-microservices)
4. [Conclusion](#conclusion)

## CodeTrans Quick Start Deployment

This section describes how to quickly deploy and test the CodeTrans service manually on an AMD ROCm GPU. The basic steps are:

1. [Access the Code](#access-the-code)
2. [Configure the Deployment Environment](#configure-the-deployment-environment)
3. [Deploy the Services Using Docker Compose](#deploy-the-services-using-docker-compose)
4. [Check the Deployment Status](#check-the-deployment-status)
5. [Validate the Pipeline](#validate-the-pipeline)
6. [Cleanup the Deployment](#cleanup-the-deployment)

### Access the Code

Clone the GenAIExample repository and access the CodeTrans AMD ROCm GPU platform Docker Compose files and supporting scripts:

```bash
git clone https://github.com/opea-project/GenAIExamples.git
cd GenAIExamples/CodeTrans
```

Then checkout a released version, such as v1.2:

```bash
git checkout v1.2
```

### Configure the Deployment Environment

To set up environment variables for deploying CodeTrans services, set up some parameters specific to the deployment environment and source the `set_env_*.sh` script in this directory:

- if used vLLM - set_env_vllm.sh
- if used TGI - set_env.sh

Set the values of the variables:

- **HOST_IP, HOST_IP_EXTERNAL** - These variables are used to configure the name/address of the service in the operating system environment for the application services to interact with each other and with the outside world.

  If your server uses only an internal address and is not accessible from the Internet, then the values for these two variables will be the same and the value will be equal to the server's internal name/address.

  If your server uses only an external, Internet-accessible address, then the values for these two variables will be the same and the value will be equal to the server's external name/address.

  If your server is located on an internal network, has an internal address, but is accessible from the Internet via a proxy/firewall/load balancer, then the HOST_IP variable will have a value equal to the internal name/address of the server, and the EXTERNAL_HOST_IP variable will have a value equal to the external name/address of the proxy/firewall/load balancer behind which the server is located.

  We set these values in the file set_env\*\*\*\*.sh

- **Variables with names like "**\*\*\*\*\*\*\_PORT"\*\* - These variables set the IP port numbers for establishing network connections to the application services.
  The values shown in the file set_env.sh or set_env_vllm they are the values used for the development and testing of the application, as well as configured for the environment in which the development is performed. These values must be configured in accordance with the rules of network access to your environment's server, and must not overlap with the IP ports of other applications that are already in use.

Setting variables in the operating system environment:

```bash
export HUGGINGFACEHUB_API_TOKEN="Your_HuggingFace_API_Token"
source ./set_env_*.sh # replace the script name with the appropriate one
```

Consult the section on [CodeTrans Service configuration](#codetrans-configuration) for information on how service specific configuration parameters affect deployments.

### Deploy the Services Using Docker Compose

To deploy the CodeTrans services, execute the `docker compose up` command with the appropriate arguments. For a default deployment with TGI, execute the command below. It uses the 'compose.yaml' file.

```bash
cd docker_compose/amd/gpu/rocm
# if used TGI
docker compose -f compose.yaml up -d
# if used vLLM
# docker compose -f compose_vllm.yaml up -d
```

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

> **Note**: developers should build docker image from source when:
>
> - Developing off the git main branch (as the container's ports in the repo may be different > from the published docker image).
> - Unable to download the docker image.
> - Use a specific version of Docker image.

Please refer to the table below to build different microservices from source:

| Microservice | Deployment Guide                                                                                               |
| ------------ | -------------------------------------------------------------------------------------------------------------- |
| vLLM         | [vLLM build guide](https://github.com/opea-project/GenAIComps/tree/main/comps/third_parties/vllm#build-docker) |
| TGI          | [TGI project](https://github.com/huggingface/text-generation-inference.git)                                    |
| LLM          | [LLM build guide](https://github.com/opea-project/GenAIComps/tree/main/comps/llms)                             |
| MegaService  | [MegaService guide](../../../../README.md)                                                                     |
| UI           | [UI guide](../../../../ui/svelte/README.md)                                                                    |
| Nginx        | [Nginx guide](https://github.com/opea-project/GenAIComps/tree/main/comps/third_parties/nginx)                  |

### Check the Deployment Status

After running docker compose, check if all the containers launched via docker compose have started:

```bash
docker ps -a
```

For the default deployment with TGI, the following 9 containers should have started:

```
CONTAINER ID   IMAGE                                                   COMMAND                  CREATED          STATUS                    PORTS                                                                                      NAMES
eaf24161aca8   opea/nginx:latest                                       "/docker-entrypoint.…"   37 seconds ago   Up 5 seconds              0.0.0.0:18104->80/tcp, [::]:18104->80/tcp                                                  chaqna-nginx-server
2fce48a4c0f4   opea/codetrans-ui:latest                                  "docker-entrypoint.s…"   37 seconds ago   Up 5 seconds              0.0.0.0:18101->5173/tcp, [::]:18101->5173/tcp                                              codetrans-ui-server
613c384979f4   opea/codetrans:latest                                     "bash entrypoint.sh"     37 seconds ago   Up 5 seconds              0.0.0.0:18102->8888/tcp, [::]:18102->8888/tcp                                              codetrans-backend-server
e0ef1ea67640   opea/llm-textgen:latest                                  "bash entrypoint.sh"     37 seconds ago   Up 36 seconds             0.0.0.0:18011->9000/tcp, [::]:18011->9000/tcp                                              codetrans-llm-server
342f01bfdbb2   ghcr.io/huggingface/text-generation-inference:2.3.1-rocm"python3 /workspace/…"   37 seconds ago   Up 36 seconds             0.0.0.0:18008->8011/tcp, [::]:18008->8011/tcp                                              codetrans-tgi-service
```

if used vLLM:

```
CONTAINER ID   IMAGE                                                   COMMAND                  CREATED          STATUS                    PORTS                                                                                      NAMES
eaf24161aca8   opea/nginx:latest                                       "/docker-entrypoint.…"   37 seconds ago   Up 5 seconds              0.0.0.0:18104->80/tcp, [::]:18104->80/tcp                                                  chaqna-nginx-server
2fce48a4c0f4   opea/codetrans-ui:latest                                  "docker-entrypoint.s…"   37 seconds ago   Up 5 seconds              0.0.0.0:18101->5173/tcp, [::]:18101->5173/tcp                                              codetrans-ui-server
613c384979f4   opea/codetrans:latest                                     "bash entrypoint.sh"     37 seconds ago   Up 5 seconds              0.0.0.0:18102->8888/tcp, [::]:18102->8888/tcp                                              codetrans-backend-server
e0ef1ea67640   opea/llm-textgen:latest                                  "bash entrypoint.sh"     37 seconds ago   Up 36 seconds             0.0.0.0:18011->9000/tcp, [::]:18011->9000/tcp                                              codetrans-llm-server
342f01bfdbb2   opea/vllm-rocm:latest                                   "python3 /workspace/…"   37 seconds ago   Up 36 seconds             0.0.0.0:18008->8011/tcp, [::]:18008->8011/tcp                                              codetrans-vllm-service
```

If any issues are encountered during deployment, refer to the [Troubleshooting](../../../../README_miscellaneous.md#troubleshooting) section.

### Validate the Pipeline

Once the CodeTrans services are running, test the pipeline using the following command:

```bash
DATA='{"language_from": "Python","language_to": "Java","source_code": '\
'"print(\"Hello, World!\");\n}"}'

curl http://${HOST_IP}:${CODETRANS_BACKEND_SERVICE_PORT}/v1/codetrans \
  -H "Content-Type: application/json" \
  -d "$DATA"
```

**Note** : Access the CodeTrans UI by web browser through this URL: `http://${HOST_IP_EXTERNAL}:${CODETRANS_NGINX_PORT}`

### Cleanup the Deployment

To stop the containers associated with the deployment, execute the following command:

```bash
# if used TGI
docker compose -f compose.yaml down
# if used vLLM
# docker compose -f compose_vllm.yaml down
```

## CodeTrans Docker Compose Files

In the context of deploying an ChatQnA pipeline on an Intel® Xeon® platform, we can pick and choose different large language model serving frameworks, or single English TTS/multi-language TTS component. The table below outlines the various configurations that are available as part of the application. These configurations can be used as templates and can be extended to different components available in [GenAIComps](https://github.com/opea-project/GenAIComps.git).

| File                                     | Description                                                                           |
| ---------------------------------------- | ------------------------------------------------------------------------------------- |
| [compose.yaml](./compose.yaml)           | The LLM serving framework is TGI. Default compose file using TGI as serving framework |
| [compose_vllm.yaml](./compose_vllm.yaml) | The LLM serving framework is vLLM. Compose file using vllm as serving framework       |

## Validate MicroServices

LLM backend Service

In the first startup, this service will take more time to download, load and warm up the model. After it's finished, the service will be ready.

Try the command below to check whether the LLM serving is ready.

```bash
# vLLM service
docker logs codetrans-vllm-service 2>&1 | grep complete
# If the service is ready, you will get the response like below.
INFO:     Application startup complete.
```

```bash
# TGI service
docker logs codetrans-tgi-service | grep Connected
# If the service is ready, you will get the response like below.
2024-09-03T02:47:53.402023Z  INFO text_generation_router::server: router/src/server.rs:2311: Connected
```

Then try the `cURL` command below to validate services.

```bash
# either vLLM or TGI service
# for vllm service
export port=${CODETRANS_VLLM_SERVICE_PORT}
# for tgi service
export port=${CODETRANS_TGI_SERVICE_PORT}
curl http://${HOST_IP}:${port}/v1/chat/completions \
  -X POST \
  -d '{"inputs":"    ### System: Please translate the following Golang codes into  Python codes.    ### Original codes:    '\'''\'''\''Golang    \npackage main\n\nimport \"fmt\"\nfunc main() {\n    fmt.Println(\"Hello, World!\");\n    '\'''\'''\''    ### Translated codes:","parameters":{"max_new_tokens":17, "do_sample": true}}' \
  -H 'Content-Type: application/json'
```

2. LLM Microservice

   ```bash
   curl http://${HOST_IP}:${CODETRANS_LLM_SERVICE_PORT}/v1/chat/completions \
     -X POST \
     -d '{"query":"    ### System: Please translate the following Golang codes into  Python codes.    ### Original codes:    '\'''\'''\''Golang    \npackage main\n\nimport \"fmt\"\nfunc main() {\n    fmt.Println(\"Hello, World!\");\n    '\'''\'''\''    ### Translated codes:"}' \
     -H 'Content-Type: application/json'
   ```

3. MegaService

   ```bash
   curl http://${HOST_IP}:${CODETRANS_BACKEND_SERVICE_PORT}/v1/codetrans \
       -H "Content-Type: application/json" \
       -d '{"language_from": "Golang","language_to": "Python","source_code": "package main\n\nimport \"fmt\"\nfunc main() {\n    fmt.Println(\"Hello, World!\");\n}"}'
   ```

4. Nginx Service

   ```bash
   curl http://${HOST_IP}:${NGINX_PORT}/v1/codetrans \
       -H "Content-Type: application/json" \
       -d '{"language_from": "Golang","language_to": "Python","source_code": "package main\n\nimport \"fmt\"\nfunc main() {\n    fmt.Println(\"Hello, World!\");\n}"}'
   ```

## Conclusion

This guide should enable developer to deploy the default configuration or any of the other compose yaml files for different configurations. It also highlights the configurable parameters that can be set before deployment.
