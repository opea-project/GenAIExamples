# Example Translation Deployment on AMD GPU (ROCm)

This document outlines the deployment process for a Translation service utilizing the [GenAIComps](https://github.com/opea-project/GenAIComps.git) microservice pipeline on AMD GPU (ROCm). This example includes the following sections:

- [Translation Quick Start Deployment](#translation-quick-start-deployment): Demonstrates how to quickly deploy a Translation service/pipeline on AMD GPU (ROCm).
- [Translation Docker Compose Files](#translation-docker-compose-files): Describes some example deployments and their docker compose files.
- [Translation Service Configuration](#translation-service-configuration): Describes the service and possible configuration changes.

## Translation Quick Start Deployment

This section describes how to quickly deploy and test the Translation service manually on AMD GPU (ROCm). The basic steps are:

1. [Access the Code](#access-the-code)
2. [Generate a HuggingFace Access Token](#generate-a-huggingface-access-token)
3. [Configure the Deployment Environment](#configure-the-deployment-environment)
4. [Deploy the Service Using Docker Compose](#deploy-the-service-using-docker-compose)
5. [Check the Deployment Status](#check-the-deployment-status)
6. [Test the Pipeline](#test-the-pipeline)
7. [Cleanup the Deployment](#cleanup-the-deployment)

### Access the Code

Clone the GenAIExample repository and access the Translation AMD GPU (ROCm) Docker Compose files and supporting scripts:

```
git clone https://github.com/opea-project/GenAIExamples.git
cd GenAIExamples/Translation/docker_compose/amd/gpu/rocm/
```

Checkout a released version, such as v1.2:

```
git checkout v1.2
```

### Generate a HuggingFace Access Token

Some HuggingFace resources, such as some models, are only accessible if you have an access token. If you do not already have a HuggingFace access token, you can create one by first creating an account by following the steps provided at [HuggingFace](https://huggingface.co/) and then generating a [user access token](https://huggingface.co/docs/transformers.js/en/guides/private#step-1-generating-a-user-access-token).

### Configure the Deployment Environment

To set up environment variables for deploying Translation service, source the _set_env.sh_ or _set_env_vllm.sh_ script in this directory:

```
//with TGI:
source ./set_env.sh
```

```
//with VLLM:
source ./set_env_vllm.sh
```

The _set_env.sh_ script will prompt for required and optional environment variables used to configure the Translation service based on TGI. The _set_env_vllm.sh_ script will prompt for required and optional environment variables used to configure the Translation service based on VLLM. If a value is not entered, the script will use a default value for the same. It will also generate a _.env_ file defining the desired configuration. Consult the section on [Translation Service configuration](#translation-service-configuration) for information on how service specific configuration parameters affect deployments.

### Deploy the Service Using Docker Compose

To deploy the Translation service, execute the `docker compose up` command with the appropriate arguments. For a default deployment, execute:

```bash
//with TGI:
docker compose -f compose.yaml up -d
```

```bash
//with VLLM:
docker compose -f compose_vllm.yaml up -d
```

The Translation docker images should automatically be downloaded from the `OPEA registry` and deployed on the AMD GPU (ROCm)

### Check the Deployment Status

After running docker compose, check if all the containers launched via docker compose have started:

```
docker ps -a
```

For the default deployment, the following 5 containers should be running.

### Test the Pipeline

Once the Translation service are running, test the pipeline using the following command:

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

**Note** The value of _host_ip_ was set using the _set_env.sh_ script and can be found in the _.env_ file.

### Cleanup the Deployment

To stop the containers associated with the deployment, execute the following command:

```
//with TGI:
docker compose -f compose.yaml down
```

```bash
//with VLLM:
docker compose -f compose_vllm.yaml up -d
```

All the Translation containers will be stopped and then removed on completion of the "down" command.

## Translation Docker Compose Files

The compose.yaml is default compose file using tgi as serving framework

| Service Name               | Image Name                                               |
| -------------------------- | -------------------------------------------------------- |
| translation-tgi-service    | ghcr.io/huggingface/text-generation-inference:2.4.1-rocm |
| translation-llm            | opea/llm-textgen:latest                                  |
| translation-backend-server | opea/translation:latest                                  |
| translation-ui-server      | opea/translation-ui:latest                               |
| translation-nginx-server   | opea/nginx:latest                                        |

## Translation Service Configuration for AMD GPUs

To enable GPU support for AMD GPUs, the following configuration is added to the Docker Compose file:

- compose_vllm.yaml - for vLLM-based service
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

The table provides a comprehensive overview of the Translation service utilized across various deployments as illustrated in the example Docker Compose files. Each row in the table represents a distinct service, detailing its possible images used to enable it and a concise description of its function within the deployment architecture.

| Service Name               | Possible Image Names                                     | Optional | Description                                                                                         |
| -------------------------- | -------------------------------------------------------- | -------- | --------------------------------------------------------------------------------------------------- |
| translation-tgi-service    | ghcr.io/huggingface/text-generation-inference:2.4.1-rocm | No       | Specific to the TGI deployment, focuses on text generation inference using AMD GPU (ROCm) hardware. |
| translation-vllm-service   | opea/vllm-rocm:latest                                    | No       | Handles large language model (LLM) tasks, utilizing AMD GPU (ROCm) hardware.                        |
| translation-llm            | opea/llm-textgen:latest                                  | No       | Handles large language model (LLM) tasks                                                            |
| translation-backend-server | opea/translation:latest                                  | No       | Serves as the backend for the Translation service, with variations depending on the deployment.     |
| translation-ui-server      | opea/translation-ui:latest                               | No       | Provides the user interface for the Translation service.                                            |
| translation-nginx-server   | opea/nginx:latest                                        | No       | A cts as a reverse proxy, managing traffic between the UI and backend services.                     |

**How to Identify GPU Device IDs:**
Use AMD GPU driver utilities to determine the correct `cardN` and `renderN` IDs for your GPU.
