# Deploy CodeTrans Application on AMD EPYC™ Processors with Docker Compose

This document outlines the single node deployment process for a CodeTrans application utilizing the [GenAIComps](https://github.com/opea-project/GenAIComps.git) microservices on AMD EPYC™ Processors. The steps include pulling Docker images, container deployment via Docker Compose, and service execution using microservices `llm`.

## Table of Contents

1. [CodeTrans Quick Start Deployment](#codetrans-quick-start-deployment)
2. [CodeTrans Docker Compose Files](#codetrans-docker-compose-files)
3. [Validate Microservices](#validate-microservices)
4. [Conclusion](#conclusion)

## CodeTrans Quick Start Deployment

This section describes how to quickly deploy and test the CodeTrans service manually on an AMD EPYC processor. The basic steps are:

1. [Access the Code](#access-the-code)
2. [Configure the Deployment Environment](#configure-the-deployment-environment)
3. [Deploy the Services Using Docker Compose](#deploy-the-services-using-docker-compose)
4. [Check the Deployment Status](#check-the-deployment-status)
5. [Validate the Pipeline](#validate-the-pipeline)
6. [Cleanup the Deployment](#cleanup-the-deployment)

### Access the Code

Clone the GenAIExample repository

```bash
git clone https://github.com/opea-project/GenAIExamples.git
cd GenAIExamples/CodeTrans
cd docker_compose/amd/cpu/epyc
```

### Configure the Deployment Environment

1.  **Install Docker:**
    Ensure Docker is installed on your system. If Docker is not already installed, use the provided script to set it up:

        source ./install_docker.sh

    This script installs Docker and its dependencies. After running it, verify the installation by checking the Docker version:

        docker --version

    If Docker is already installed, this step can be skipped.

2.  **Configure Environment:**  
    Set required environment variables in your shell:

    **_i) Determine your host's external IP address:_**  
     Run the following command in your terminal to list network interfaces:

        ifconfig

    Look for the inet address associated with your active network interface (e.g., enp99s0). For example:

        enp99s0: flags=4163<UP,BROADCAST,RUNNING,MULTICAST>  mtu 1500
          inet 10.101.16.119  netmask 255.255.255.0  broadcast 10.101.16.255

    In this example, the (`host_ip`) would be (`10.101.16.119`).

        # Replace with your host's external IP address
        export host_ip="your_external_ip_address"

    **_ii) Generate a HuggingFace Access Token:_**  
     Some HuggingFace resources, such as some models, are only accessible if you have an access token. If you do not already have a HuggingFace access token, you can create one by first creating an account by following the steps provided at [HuggingFace](https://huggingface.co/) and then generating a [user access token](https://huggingface.co/docs/transformers.js/en/guides/private#step-1-generating-a-user-access-token).

        # Replace with your Hugging Face Hub API token
        export HF_TOKEN="your_huggingface_token"

    **_iii) Set environment variables:_**
    The model_cache directory, by default, stores models in the ./data directory. To change this, use the following command:

        # Optional
        export model_cache=/home/documentation/data_codetrans/data # Path to save cache models

    Optional: Configure proxy settings if needed:

         ```bash
         export http_proxy="Your_HTTP_Proxy"           # http proxy if any
         export https_proxy="Your_HTTPs_Proxy"         # https proxy if any
         export no_proxy=localhost,127.0.0.1,$host_ip  # additional no proxies if needed
         export NGINX_PORT=${your_nginx_port}          # your usable port for nginx, 80 for example
         ```

    To set other environment variables:

         source set_env.sh

### Deploy the Services Using Docker Compose

To deploy the CodeTrans services, execute the `docker compose up` command with the appropriate arguments. For a default deployment, execute the command below. It uses the 'compose.yaml' file.

```bash
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
CONTAINER ID   IMAGE                      COMMAND                  CREATED         STATUS                   PORTS                                         NAMES
68497c3f3a6d   opea/nginx:latest          "/docker-entrypoint.…"   3 minutes ago   Up 49 seconds            0.0.0.0:80->80/tcp, [::]:80->80/tcp           codetrans-epyc-nginx-server
97eafa7f5979   opea/codetrans-ui:latest   "docker-entrypoint.s…"   3 minutes ago   Up 49 seconds            0.0.0.0:5173->5173/tcp, [::]:5173->5173/tcp   codetrans-epyc-ui-server
872287b18499   opea/codetrans:latest      "python code_transla…"   3 minutes ago   Up 50 seconds            0.0.0.0:7777->7777/tcp, [::]:7777->7777/tcp   codetrans-epyc-backend-server
2fbb6af847dd   opea/llm-textgen:latest    "bash entrypoint.sh"     3 minutes ago   Up 50 seconds            0.0.0.0:9000->9000/tcp, [::]:9000->9000/tcp   codetrans-epyc-llm-server
532cdf3c79ce   opea/vllm:latest           "python3 -m vllm.ent…"   3 minutes ago   Up 3 minutes (healthy)   0.0.0.0:8008->80/tcp, [::]:8008->80/tcp       codetrans-epyc-vllm-service
```

If any issues are encountered during deployment, refer to the [Troubleshooting](../../../../README_miscellaneous.md#troubleshooting) section.

### Validate the Pipeline

Once the CodeTrans services are running, test the pipeline using the following command:

```bash
curl http://${host_ip}:7777/v1/codetrans \
    -H "Content-Type: application/json" \
    -d '{"language_from": "Golang","language_to": "Python","source_code": "package main\n\nimport \"fmt\"\nfunc main() {\n    fmt.Println(\"Hello, World!\");\n}"}'
```

**Note** : Access the CodeTrans UI by web browser through this URL: `http://${host_ip}:80`. Please confirm the `80` port is opened in the firewall. To validate each microservie used in the pipeline refer to the [Validate Microservices](#validate-microservices) section.

### Cleanup the Deployment

To stop the containers associated with the deployment, execute the following command:

```bash
docker compose -f compose.yaml down
```

## Configuration Parameters

Key parameters are configured via environment variables set before running `docker compose up`.

| Environment Variable                    | Description                                                                                                           | Default (Set Externally)              |
| :-------------------------------------- | :-------------------------------------------------------------------------------------------------------------------- | :------------------------------------ |
| `HOST_IP`                               | External IP address of the host machine. **Required.**                                                                | `your_external_ip_address`            |
| `HF_TOKEN`                              | Your Hugging Face Hub token for model access. **Required.**                                                           | `your_huggingface_token`              |
| `LLM_MODEL_ID`                          | Hugging Face model ID for the CodeTrans LLM (used by TGI/vLLM service). Configured within `compose.yaml` environment. | `Qwen/Qwen2.5-Coder-7B-Instruct`      |
| `LLM_ENDPOINT`                          | Internal URL for the LLM serving endpoint (used by `codetrans-epyc-llm-server`). Configured in `compose.yaml`.        | `http://${HOST_IP}:8008`              |
| `LLM_COMPONENT_NAME`                    | LLM component name for the LLM Microservice.                                                                          | `OpeaTextGenService`                  |
| `BACKEND_SERVICE_ENDPOINT`              | External URL for the CodeTrans Gateway (MegaService). Derived from `HOST_IP` and port `7778`.                         | `http://${HOST_IP}:7777/v1/codetrans` |
| `FRONTEND_SERVICE_PORT`                 | Host port mapping for the frontend UI. Configured in `compose.yaml`.                                                  | `5173`                                |
| `BACKEND_SERVICE_PORT`                  | Host port mapping for the backend MegaService. Configured in `compose.yaml`.                                          | `7777`                                |
| `http_proxy` / `https_proxy`/`no_proxy` | Network proxy settings (if required).                                                                                 | `""`                                  |

## CodeTrans Docker Compose Files

In the context of deploying a CodeTrans pipeline on an AMD EPYC platform, we can pick and choose different large language model serving frameworks. The table below outlines the various configurations that are available as part of the application. These configurations can be used as templates and can be extended to different components available in [GenAIComps](https://github.com/opea-project/GenAIComps.git).

| File                                   | Description                                                                               |
| -------------------------------------- | ----------------------------------------------------------------------------------------- |
| [compose.yaml](./compose.yaml)         | Default compose file using vllm as serving framework and redis as vector database         |
| [compose_tgi.yaml](./compose_tgi.yaml) | The LLM serving framework is TGI. All other configurations remain the same as the default |

## Validate Microservices

1. LLM backend Service

   In the first startup, this service will take more time to download, load and warm up the model. After it's finished, the service will be ready.

   Try the command below to check whether the LLM serving is ready.

   ```bash
   # vLLM service
   docker logs codetrans-epyc-vllm-service 2>&1 | grep complete
   # If the service is ready, you will get the response like below.
   INFO:     Application startup complete.
   ```

   ```bash
   # TGI service
   docker logs codetrans-epyc-tgi-service | grep Connected
   # If the service is ready, you will get the response like below.
   2024-09-03T02:47:53.402023Z  INFO text_generation_router::server: router/src/server.rs:2311: Connected
   ```

   Then try the `cURL` command below to validate services.

   ```bash
   # either vLLM or TGI service
   curl http://${host_ip}:8008/v1/chat/completions \
     -X POST \
     -d '{
       "messages": [
         {"role": "system", "content": "Please translate the following Golang code into Python code."},
         {"role": "user", "content": "package main\n\nimport \"fmt\"\nfunc main() {\n    fmt.Println(\"Hello, World!\");\n"}
       ],
       "parameters": {
         "max_new_tokens": 17,
         "do_sample": true
       }
     }' \
     -H 'Content-Type: application/json'
   ```

2. LLM Microservice

   ```bash
   curl http://${host_ip}:9000/v1/chat/completions\
     -X POST \
     -d '{"query":"    ### System: Please translate the following Golang codes into  Python codes.    ### Original codes:    '\'''\'''\''Golang    \npackage main\n\nimport \"fmt\"\nfunc main() {\n    fmt.Println(\"Hello, World!\");\n    '\'''\'''\''    ### Translated codes:"}' \
     -H 'Content-Type: application/json'
   ```

3. MegaService

   ```bash
   curl http://${host_ip}:7777/v1/codetrans \
       -H "Content-Type: application/json" \
       -d '{"language_from": "Golang","language_to": "Python","source_code": "package main\n\nimport \"fmt\"\nfunc main() {\n    fmt.Println(\"Hello, World!\");\n}"}'
   ```

4. Nginx Service

   ```bash
   curl http://${host_ip}:${NGINX_PORT}/v1/codetrans \
       -H "Content-Type: application/json" \
       -d '{"language_from": "Golang","language_to": "Python","source_code": "package main\n\nimport \"fmt\"\nfunc main() {\n    fmt.Println(\"Hello, World!\");\n}"}'
   ```

### Profile Microservices

To further analyze MicroService Performance, users could follow the instructions to profile MicroServices.

#### 1. vLLM backend Service

Users could follow previous section to testing vLLM microservice or CodeTrans MegaService. By default, vLLM profiling is not enabled. Users could start and stop profiling by following commands.

##### Start vLLM profiling

```bash
curl http://${host_ip}:8008/start_profile \
  -H "Content-Type: application/json" \
  -d '{"model": "Qwen/Qwen2.5-Coder-7B-Instruct"}'
```

After vLLM profiling is started, users could start asking questions and get responses from vLLM MicroService

```bash
   curl http://${host_ip}:8008/v1/chat/completions \
     -X POST \
     -d '{
       "messages": [
         {"role": "system", "content": "Please translate the following Golang code into Python code."},
         {"role": "user", "content": "package main\n\nimport \"fmt\"\nfunc main() {\n    fmt.Println(\"Hello, World!\");\n"}
       ],
       "parameters": {
         "max_new_tokens": 17,
         "do_sample": true
       }
     }' \
     -H 'Content-Type: application/json'
```

##### Stop vLLM profiling

By following command, users could stop vLLM profiling and generate a \*.pt.trace.json.gz file as profiling result  
 under /mnt folder in codetrans-epyc-vllm-service docker instance.

```bash
curl http://${host_ip}:8008/stop_profile \
  -H "Content-Type: application/json" \
  -d '{"model": "Qwen/Qwen2.5-Coder-7B-Instruct"}'
```

After vllm profiling is stopped, users could use below command to get the \*.pt.trace.json.gz file under /mnt folder.

```bash
docker cp  codetrans-epyc-vllm-service:/mnt/ .
```

##### Check profiling result

Open a web browser and type "chrome://tracing" or "ui.perfetto.dev", and then load the json.gz file.

## Conclusion

This guide should enable developer to deploy the default configuration or any of the other compose yaml files for different configurations. It also highlights the configurable parameters that can be set before deployment.
