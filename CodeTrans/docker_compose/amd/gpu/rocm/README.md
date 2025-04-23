# Deploy CodeTrans on AMD GPU (ROCm)

This document outlines the single node deployment process for a CodeTrans application utilizing the [GenAIComps](https://github.com/opea-project/GenAIComps.git) microservices on AMD GPU (ROCm) server. The steps include pulling Docker images, container deployment via Docker Compose, and service execution using microservices `llm`.

# Table of Contents

1. [CodeTrans Quick Start Deployment](#codetrans-quick-start-deployment)
2. [CodeTrans Docker Compose Files](#codetrans-docker-compose-files)
3. [Validate Microservices](#validate-microservices)
4. [Conclusion](#conclusion)

## CodeTrans Quick Start Deployment

This section describes how to quickly deploy and test the CodeTrans service manually on an AMD GPU (ROCm) processor. The basic steps are:

1. [Access the Code](#access-the-code)
2. [Configure the Deployment Environment](#configure-the-deployment-environment)
3. [Deploy the Services Using Docker Compose](#deploy-the-services-using-docker-compose)
4. [Check the Deployment Status](#check-the-deployment-status)
5. [Validate the Pipeline](#validate-the-pipeline)
6. [Cleanup the Deployment](#cleanup-the-deployment)

### Access the Code

Clone the GenAIExample repository and access the CodeTrans AMD GPU (ROCm) platform Docker Compose files and supporting scripts:

```bash
git clone https://github.com/opea-project/GenAIExamples.git
cd GenAIExamples/CodeTrans
```

Then checkout a released version, such as v1.2:

```bash
git checkout v1.2
```

### Configure the Deployment Environment

To set up environment variables for deploying CodeTrans services, set up some parameters specific to the deployment environment and source the `set_env.sh` script in this directory:

```bash
export host_ip="External_Public_IP"           # ip address of the node
export HUGGINGFACEHUB_API_TOKEN="Your_HuggingFace_API_Token"
export http_proxy="Your_HTTP_Proxy"           # http proxy if any
export https_proxy="Your_HTTPs_Proxy"         # https proxy if any
export no_proxy=localhost,127.0.0.1,$host_ip  # additional no proxies if needed
export NGINX_PORT=${your_nginx_port}          # your usable port for nginx, 80 for example
source ./set_env.sh
```

Consult the section on [CodeTrans Service configuration](#codetrans-configuration) for information on how service specific configuration parameters affect deployments.

### Deploy the Services Using Docker Compose

To deploy the CodeTrans services, execute the `docker compose up` command with the appropriate arguments. For a default deployment, execute the command below. It uses the 'compose.yaml' file.

```bash
cd docker_compose/amd/gpu/rocm
docker compose -f compose.yaml up -d
```

> **Note**: developers should build docker image from source when:
>
> - Developing off the git main branch (as the container's ports in the repo may be different > from the published docker image).
> - Unable to download the docker image.
> - Use a specific version of Docker image.

Please refer to the table below to build different microservices from source:

| Microservice | Deployment Guide                                                                                               |
| ------------ | -------------------------------------------------------------------------------------------------------------- |
| vLLM         | [vLLM build guide](https://github.com/opea-project/GenAIComps/tree/main/comps/third_parties/vllm#build-docker) |
| LLM          | [LLM build guide](https://github.com/opea-project/GenAIComps/tree/main/comps/llms)                             |
| MegaService  | [MegaService build guide](../../../../README_miscellaneous.md#build-megaservice-docker-image)                  |
| UI           | [Basic UI build guide](../../../../README_miscellaneous.md#build-ui-docker-image)                              |

### Check the Deployment Status

After running docker compose, check if all the containers launched via docker compose have started:

```bash
docker ps -a
```

For the default deployment, the following 5 containers should have started:

```
CONTAINER ID   IMAGE                                                   COMMAND                  CREATED        STATUS        PORTS                                                                                  NAMES
b3e1388fa2ca   opea/nginx:${RELEASE_VERSION}                           "/usr/local/bin/star…"   32 hours ago   Up 2 hours   0.0.0.0:80->80/tcp, :::80->80/tcp                                                      codetrans-nginx-server
3b5fa9a722da   opea/codetrans-ui:${RELEASE_VERSION}                    "docker-entrypoint.s…"   32 hours ago   Up 2 hours   0.0.0.0:5173->5173/tcp, :::5173->5173/tcp                                              codetrans-ui-server
d3b37f3d1faa   opea/codetrans:${RELEASE_VERSION}                       "python codetrans.py"    32 hours ago   Up 2 hours   0.0.0.0:7777->7777/tcp, :::7777->7777/tcp                                              codetrans-backend-server
24cae0db1a70   opea/llm-textgen:${RELEASE_VERSION}                     "bash entrypoint.sh"     32 hours ago   Up 2 hours   0.0.0.0:9000->9000/tcp, :::9000->9000/tcp                                              codetrans-llm-server
b98fa07a4f5c   opea/vllm:${RELEASE_VERSION}                            "python3 -m vllm.ent…"   32 hours ago   Up 2 hours   0.0.0.0:9009->80/tcp, :::9009->80/tcp                                                  codetrans-tgi-service
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

**Note** : Access the CodeTrans UI by web browser through this URL: `http://${host_ip}:80`. Please confirm the `80` port is opened in the firewall. To validate each microservie used in the pipeline refer to the [Validate Microservices](#validate-microservices) section.

### Cleanup the Deployment

To stop the containers associated with the deployment, execute the following command:

```bash
docker compose -f compose.yaml down
```

## CodeTrans Docker Compose Files

In the context of deploying a CodeTrans pipeline on an AMD GPU (ROCm) platform, we can pick and choose different large language model serving frameworks. The table below outlines the various configurations that are available as part of the application. These configurations can be used as templates and can be extended to different components available in [GenAIComps](https://github.com/opea-project/GenAIComps.git).

| File                                     | Description                                                                                |
| ---------------------------------------- | ------------------------------------------------------------------------------------------ |
| [compose.yaml](./compose.yaml)           | Default compose file using TGI as serving framework                                        |
| [compose_vllm.yaml](./compose_vllm.yaml) | The LLM serving framework is vLLM. All other configurations remain the same as the default |

## Validate Microservices

1. LLM backend Service

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
   curl http://${HOST_IP}:${CODETRANS_LLM_SERVICE_PORT}/v1/chat/completions\
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
