# Deploying ChatQnA on AMD ROCm GPU

This document outlines the single node deployment process for a ChatQnA application utilizing the [GenAIComps](https://github.com/opea-project/GenAIComps.git) microservices on Intel Xeon server and AMD GPU. The steps include pulling Docker images, container deployment via Docker Compose, and service execution using microservices `llm`.

Note: The default LLM is `meta-llama/Meta-Llama-3-8B-Instruct`. Before deploying the application, please make sure either you've requested and been granted the access to it on [Huggingface](https://huggingface.co/meta-llama/Meta-Llama-3-8B-Instruct) or you've downloaded the model locally from [ModelScope](https://www.modelscope.cn/models).

## Table of Contents

1. [ChatQnA Quick Start Deployment](#chatqna-quick-start-deployment)
2. [ChatQnA Docker Compose Files](#chatqna-docker-compose-files)
3. [Validate Microservices](#validate-microservices)
4. [Conclusion](#conclusion)

## ChatQnA Quick Start Deployment

This section describes how to quickly deploy and test the ChatQnA service manually on an AMD ROCm GPU. The basic steps are:

1. [Access the Code](#access-the-code)
2. [Configure the Deployment Environment](#configure-the-deployment-environment)
3. [Deploy the Services Using Docker Compose](#deploy-the-services-using-docker-compose)
4. [Check the Deployment Status](#check-the-deployment-status)
5. [Validate the Pipeline](#validate-the-pipeline)
6. [Cleanup the Deployment](#cleanup-the-deployment)

### Access the Code

Clone the GenAIExample repository and access the ChatQnA AMD ROCm GPU platform Docker Compose files and supporting scripts:

```bash
git clone https://github.com/opea-project/GenAIExamples.git
cd GenAIExamples/ChatQnA
```

Then checkout a released version, such as v1.3:

```bash
git checkout v1.3
```

### Configure the Deployment Environment

To set up environment variables for deploying ChatQnA services, set up some parameters specific to the deployment environment and source the `set_env_*.sh` script in this directory:

- if used vLLM - set_env_vllm.sh
- if used vLLM with FaqGen - set_env_faqgen_vllm.sh
- if used TGI - set_env.sh
- if used TGI with FaqGen - set_env_faqgen.sh

Set the values of the variables:

- **HOST_IP, HOST_IP_EXTERNAL** - These variables are used to configure the name/address of the service in the operating system environment for the application services to interact with each other and with the outside world.

  If your server uses only an internal address and is not accessible from the Internet, then the values for these two variables will be the same and the value will be equal to the server's internal name/address.

  If your server uses only an external, Internet-accessible address, then the values for these two variables will be the same and the value will be equal to the server's external name/address.

  If your server is located on an internal network, has an internal address, but is accessible from the Internet via a proxy/firewall/load balancer, then the HOST_IP variable will have a value equal to the internal name/address of the server, and the EXTERNAL_HOST_IP variable will have a value equal to the external name/address of the proxy/firewall/load balancer behind which the server is located.

  We set these values in the file set_env\*\*\*\*.sh

- **Variables with names like "**\*\*\*\*\*\*\_PORT"\*\* - These variables set the IP port numbers for establishing network connections to the application services.
  The values shown in the file set_env.sh or set_env_vllm.sh they are the values used for the development and testing of the application, as well as configured for the environment in which the development is performed. These values must be configured in accordance with the rules of network access to your environment's server, and must not overlap with the IP ports of other applications that are already in use.

Setting variables in the operating system environment:

```bash
export HUGGINGFACEHUB_API_TOKEN="Your_HuggingFace_API_Token"
source ./set_env_*.sh # replace the script name with the appropriate one
```

Consult the section on [ChatQnA Service configuration](#chatqna-configuration) for information on how service specific configuration parameters affect deployments.

### Deploy the Services Using Docker Compose

To deploy the ChatQnA services, execute the `docker compose up` command with the appropriate arguments. For a default deployment with TGI, execute the command below. It uses the 'compose.yaml' file.

```bash
cd docker_compose/amd/gpu/rocm
# if used TGI
docker compose -f compose.yaml up -d
# if used TGI with FaqGen
# docker compose -f compose_faqgen.yaml up -d
# if used vLLM
# docker compose -f compose_vllm.yaml up -d
# if used vLLM with FaqGen
# docker compose -f compose_faqgen_vllm.yaml up -d
```

To enable GPU support for AMD GPUs, the following configuration is added to the Docker Compose file:

- compose_vllm.yaml - for vLLM-based application
- compose_faqgen_vllm.yaml - for vLLM-based application with FaqGen
- compose.yaml - for TGI-based
- compose_faqgen.yaml - for TGI-based application with FaqGen

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

| Microservice    | Deployment Guide                                                                                                   |
| --------------- | ------------------------------------------------------------------------------------------------------------------ |
| vLLM            | [vLLM build guide](https://github.com/opea-project/GenAIComps/tree/main/comps/third_parties/vllm#build-docker)     |
| TGI             | [TGI project](https://github.com/huggingface/text-generation-inference.git)                                        |
| LLM             | [LLM build guide](https://github.com/opea-project/GenAIComps/tree/main/comps/llms)                                 |
| Redis Vector DB | [Redis](https://github.com/redis/redis.git)                                                                        |
| Dataprep        | [Dataprep build guide](https://github.com/opea-project/GenAIComps/tree/main/comps/dataprep/src/README_redis.md)    |
| TEI Embedding   | [TEI guide](https://github.com/huggingface/text-embeddings-inference.git)                                          |
| Retriever       | [Retriever build guide](https://github.com/opea-project/GenAIComps/tree/main/comps/retrievers/src/README_redis.md) |
| TEI Reranking   | [TEI guide](https://github.com/huggingface/text-embeddings-inference.git)                                          |
| MegaService     | [MegaService guide](../../../../README.md)                                                                         |
| UI              | [UI guide](../../../../ui/react/README.md)                                                                         |
| Nginx           | [Nginx guide](https://github.com/opea-project/GenAIComps/tree/main/comps/third_parties/nginx)                      |

### Check the Deployment Status

After running docker compose, check if all the containers launched via docker compose have started:

```bash
docker ps -a
```

For the default deployment with TGI, the following 9 containers should have started:

```
CONTAINER ID   IMAGE                                                   COMMAND                  CREATED          STATUS                    PORTS                                                                                      NAMES
eaf24161aca8   opea/nginx:latest                                       "/docker-entrypoint.…"   37 seconds ago   Up 5 seconds              0.0.0.0:18104->80/tcp, [::]:18104->80/tcp                                                  chatqna-nginx-server
2fce48a4c0f4   opea/chatqna-ui:latest                                  "docker-entrypoint.s…"   37 seconds ago   Up 5 seconds              0.0.0.0:18101->5173/tcp, [::]:18101->5173/tcp                                              chatqna-ui-server
613c384979f4   opea/chatqna:latest                                     "bash entrypoint.sh"     37 seconds ago   Up 5 seconds              0.0.0.0:18102->8888/tcp, [::]:18102->8888/tcp                                              chatqna-backend-server
05512bd29fee   opea/dataprep:latest                                    "sh -c 'python $( [ …"   37 seconds ago   Up 36 seconds (healthy)   0.0.0.0:18103->5000/tcp, [::]:18103->5000/tcp                                              chatqna-dataprep-service
49844d339d1d   opea/retriever:latest                                   "python opea_retriev…"   37 seconds ago   Up 36 seconds             0.0.0.0:7000->7000/tcp, [::]:7000->7000/tcp                                                chatqna-retriever
75b698fe7de0   ghcr.io/huggingface/text-embeddings-inference:cpu-1.5   "text-embeddings-rou…"   37 seconds ago   Up 36 seconds             0.0.0.0:18808->80/tcp, [::]:18808->80/tcp                                                  chatqna-tei-reranking-service
342f01bfdbb2   ghcr.io/huggingface/text-generation-inference:2.3.1-rocm"python3 /workspace/…"   37 seconds ago   Up 36 seconds             0.0.0.0:18008->8011/tcp, [::]:18008->8011/tcp                                              chatqna-tgi-service
6081eb1c119d   redis/redis-stack:7.2.0-v9                              "/entrypoint.sh"         37 seconds ago   Up 36 seconds             0.0.0.0:6379->6379/tcp, [::]:6379->6379/tcp, 0.0.0.0:8001->8001/tcp, [::]:8001->8001/tcp   chatqna-redis-vector-db
eded17420782   ghcr.io/huggingface/text-embeddings-inference:cpu-1.5   "text-embeddings-rou…"   37 seconds ago   Up 36 seconds             0.0.0.0:18090->80/tcp, [::]:18090->80/tcp                                                  chatqna-tei-embedding-service
```

if used TGI with FaqGen:

```
CONTAINER ID   IMAGE                                                   COMMAND                  CREATED          STATUS                    PORTS                                                                                      NAMES
eaf24161aca8   opea/nginx:latest                                       "/docker-entrypoint.…"   37 seconds ago   Up 5 seconds              0.0.0.0:18104->80/tcp, [::]:18104->80/tcp                                                  chatqna-nginx-server
2fce48a4c0f4   opea/chatqna-ui:latest                                  "docker-entrypoint.s…"   37 seconds ago   Up 5 seconds              0.0.0.0:18101->5173/tcp, [::]:18101->5173/tcp                                              chatqna-ui-server
613c384979f4   opea/chatqna:latest                                     "bash entrypoint.sh"     37 seconds ago   Up 5 seconds              0.0.0.0:18102->8888/tcp, [::]:18102->8888/tcp                                              chatqna-backend-server
e0ef1ea67640   opea/llm-faqgen:latest                                  "bash entrypoint.sh"     37 seconds ago   Up 36 seconds             0.0.0.0:18011->9000/tcp, [::]:18011->9000/tcp                                              chatqna-llm-faqgen
05512bd29fee   opea/dataprep:latest                                    "sh -c 'python $( [ …"   37 seconds ago   Up 36 seconds (healthy)   0.0.0.0:18103->5000/tcp, [::]:18103->5000/tcp                                              chatqna-dataprep-service
49844d339d1d   opea/retriever:latest                                   "python opea_retriev…"   37 seconds ago   Up 36 seconds             0.0.0.0:7000->7000/tcp, [::]:7000->7000/tcp                                                chatqna-retriever
75b698fe7de0   ghcr.io/huggingface/text-embeddings-inference:cpu-1.5   "text-embeddings-rou…"   37 seconds ago   Up 36 seconds             0.0.0.0:18808->80/tcp, [::]:18808->80/tcp                                                  chatqna-tei-reranking-service
342f01bfdbb2   ghcr.io/huggingface/text-generation-inference:2.3.1-rocm"python3 /workspace/…"   37 seconds ago   Up 36 seconds             0.0.0.0:18008->8011/tcp, [::]:18008->8011/tcp                                              chatqna-tgi-service
6081eb1c119d   redis/redis-stack:7.2.0-v9                              "/entrypoint.sh"         37 seconds ago   Up 36 seconds             0.0.0.0:6379->6379/tcp, [::]:6379->6379/tcp, 0.0.0.0:8001->8001/tcp, [::]:8001->8001/tcp   chatqna-redis-vector-db
eded17420782   ghcr.io/huggingface/text-embeddings-inference:cpu-1.5   "text-embeddings-rou…"   37 seconds ago   Up 36 seconds             0.0.0.0:18090->80/tcp, [::]:18090->80/tcp                                                  chatqna-tei-embedding-service
```

if used vLLM:

```
CONTAINER ID   IMAGE                                                   COMMAND                  CREATED          STATUS                    PORTS                                                                                      NAMES
eaf24161aca8   opea/nginx:latest                                       "/docker-entrypoint.…"   37 seconds ago   Up 5 seconds              0.0.0.0:18104->80/tcp, [::]:18104->80/tcp                                                  chatqna-nginx-server
2fce48a4c0f4   opea/chatqna-ui:latest                                  "docker-entrypoint.s…"   37 seconds ago   Up 5 seconds              0.0.0.0:18101->5173/tcp, [::]:18101->5173/tcp                                              chatqna-ui-server
613c384979f4   opea/chatqna:latest                                     "bash entrypoint.sh"     37 seconds ago   Up 5 seconds              0.0.0.0:18102->8888/tcp, [::]:18102->8888/tcp                                              chatqna-backend-server
05512bd29fee   opea/dataprep:latest                                    "sh -c 'python $( [ …"   37 seconds ago   Up 36 seconds (healthy)   0.0.0.0:18103->5000/tcp, [::]:18103->5000/tcp                                              chatqna-dataprep-service
49844d339d1d   opea/retriever:latest                                   "python opea_retriev…"   37 seconds ago   Up 36 seconds             0.0.0.0:7000->7000/tcp, [::]:7000->7000/tcp                                                chatqna-retriever
75b698fe7de0   ghcr.io/huggingface/text-embeddings-inference:cpu-1.5   "text-embeddings-rou…"   37 seconds ago   Up 36 seconds             0.0.0.0:18808->80/tcp, [::]:18808->80/tcp                                                  chatqna-tei-reranking-service
342f01bfdbb2   opea/vllm-rocm:latest                                   "python3 /workspace/…"   37 seconds ago   Up 36 seconds             0.0.0.0:18008->8011/tcp, [::]:18008->8011/tcp                                              chatqna-vllm-service
6081eb1c119d   redis/redis-stack:7.2.0-v9                              "/entrypoint.sh"         37 seconds ago   Up 36 seconds             0.0.0.0:6379->6379/tcp, [::]:6379->6379/tcp, 0.0.0.0:8001->8001/tcp, [::]:8001->8001/tcp   chatqna-redis-vector-db
eded17420782   ghcr.io/huggingface/text-embeddings-inference:cpu-1.5   "text-embeddings-rou…"   37 seconds ago   Up 36 seconds             0.0.0.0:18090->80/tcp, [::]:18090->80/tcp                                                  chatqna-tei-embedding-service
```

if used vLLM with FaqGen:

```
CONTAINER ID   IMAGE                                                   COMMAND                  CREATED          STATUS                    PORTS                                                                                      NAMES
eaf24161aca8   opea/nginx:latest                                       "/docker-entrypoint.…"   37 seconds ago   Up 5 seconds              0.0.0.0:18104->80/tcp, [::]:18104->80/tcp                                                  chatqna-nginx-server
2fce48a4c0f4   opea/chatqna-ui:latest                                  "docker-entrypoint.s…"   37 seconds ago   Up 5 seconds              0.0.0.0:18101->5173/tcp, [::]:18101->5173/tcp                                              chatqna-ui-server
613c384979f4   opea/chatqna:latest                                     "bash entrypoint.sh"     37 seconds ago   Up 5 seconds              0.0.0.0:18102->8888/tcp, [::]:18102->8888/tcp                                              chatqna-backend-server
e0ef1ea67640   opea/llm-faqgen:latest                                  "bash entrypoint.sh"     37 seconds ago   Up 36 seconds             0.0.0.0:18011->9000/tcp, [::]:18011->9000/tcp                                              chatqna-llm-faqgen
05512bd29fee   opea/dataprep:latest                                    "sh -c 'python $( [ …"   37 seconds ago   Up 36 seconds (healthy)   0.0.0.0:18103->5000/tcp, [::]:18103->5000/tcp                                              chatqna-dataprep-service
49844d339d1d   opea/retriever:latest                                   "python opea_retriev…"   37 seconds ago   Up 36 seconds             0.0.0.0:7000->7000/tcp, [::]:7000->7000/tcp                                                chatqna-retriever
75b698fe7de0   ghcr.io/huggingface/text-embeddings-inference:cpu-1.5   "text-embeddings-rou…"   37 seconds ago   Up 36 seconds             0.0.0.0:18808->80/tcp, [::]:18808->80/tcp                                                  chatqna-tei-reranking-service
342f01bfdbb2   opea/vllm-rocm:latest                                   "python3 /workspace/…"   37 seconds ago   Up 36 seconds             0.0.0.0:18008->8011/tcp, [::]:18008->8011/tcp                                              chatqna-vllm-service
6081eb1c119d   redis/redis-stack:7.2.0-v9                              "/entrypoint.sh"         37 seconds ago   Up 36 seconds             0.0.0.0:6379->6379/tcp, [::]:6379->6379/tcp, 0.0.0.0:8001->8001/tcp, [::]:8001->8001/tcp   chatqna-redis-vector-db
eded17420782   ghcr.io/huggingface/text-embeddings-inference:cpu-1.5   "text-embeddings-rou…"   37 seconds ago   Up 36 seconds             0.0.0.0:18090->80/tcp, [::]:18090->80/tcp                                                  chatqna-tei-embedding-service
```

If any issues are encountered during deployment, refer to the [Troubleshooting](../../../../README_miscellaneous.md#troubleshooting) section.

### Validate the Pipeline

Once the ChatQnA services are running, test the pipeline using the following command:

```bash
curl http://${HOST_IP}:${CHATQNA_BACKEND_SERVICE_PORT}/v1/chatqna \
  -H "Content-Type: application/json" \
  -d '{"messages": "What is the revenue of Nike in 2023?"}'
```

**Note** : Access the ChatQnA UI by web browser through this URL: `http://${HOST_IP_EXTERNAL}:${CHATQNA_NGINX_PORT}`

### Cleanup the Deployment

To stop the containers associated with the deployment, execute the following command:

```bash
# if used TGI
docker compose -f compose.yaml down
# if used TGI with FaqGen
# docker compose -f compose_faqgen.yaml down
# if used vLLM
# docker compose -f compose_vllm.yaml down
# if used vLLM with FaqGen
# docker compose -f compose_faqgen_vllm.yaml down


```

## ChatQnA Docker Compose Files

In the context of deploying an ChatQnA pipeline on an Intel® Xeon® platform, we can pick and choose different large language model serving frameworks, or single English TTS/multi-language TTS component. The table below outlines the various configurations that are available as part of the application. These configurations can be used as templates and can be extended to different components available in [GenAIComps](https://github.com/opea-project/GenAIComps.git).

| File                                                   | Description                                                                                                              |
| ------------------------------------------------------ | ------------------------------------------------------------------------------------------------------------------------ |
| [compose.yaml](./compose.yaml)                         | The LLM serving framework is TGI. Default compose file using TGI as serving framework and redis as vector database       |
| [compose_faqgen.yaml](./compose_faqgen.yaml)           | The LLM serving framework is TGI with FaqGen. All other configurations remain the same as the default                    |
| [compose_vllm.yaml](./compose_vllm.yaml)               | The LLM serving framework is vLLM. Compose file using vllm as serving framework and redis as vector database             |
| [compose_faqgen_vllm.yaml](./compose_faqgen_vllm.yaml) | The LLM serving framework is vLLM with FaqGen. Compose file using vllm as serving framework and redis as vector database |

## Validate MicroServices

1. TEI Embedding Service

   ```bash
   curl http://${HOST_IP}:${CHATQNA_TEI_EMBEDDING_PORT}/embed \
   -X POST \
   -d '{"inputs":"What is Deep Learning?"}' \
   -H 'Content-Type: application/json'
   ```

2. Retriever Microservice

   ```bash
   export your_embedding=$(python3 -c "import random; embedding = [random.uniform(-1, 1) for _ in range(768)]; print(embedding)")
   curl http://${HOST_IP}:${CHATQNA_REDIS_RETRIEVER_PORT}/v1/retrieval \
     -X POST \
     -d "{\"text\":\"test\",\"embedding\":${your_embedding}}" \
     -H 'Content-Type: application/json'
   ```

3. TEI Reranking Service

   ```bash
   curl http://${HOST_IP}:${CHATQNA_TEI_RERANKING_PORT}/rerank \
   -X POST \
   -d '{"query":"What is Deep Learning?", "texts": ["Deep Learning is not...", "Deep learning is..."]}' \
   -H 'Content-Type: application/json'
   ```

4. vLLM/TGI Service

   If you use vLLM:

   ```bash
   DATA='{"model": "meta-llama/Meta-Llama-3-8B-Instruct", '\
   '"messages": [{"role": "user", "content": "What is a Deep Learning?"}], "max_tokens": 64}'

   curl http://${HOST_IP}:${CHATQNA_VLLM_SERVICE_PORT}/v1/chat/completions \
     -X POST \
     -d "$DATA" \
     -H 'Content-Type: application/json'
   ```

   If you use TGI:

   ```bash
   DATA='{"inputs":"What is a Deep Learning?",'\
   '"parameters":{"max_new_tokens":64,"do_sample": true}}'

   curl http://${HOST_IP}:${CHATQNA_TGI_SERVICE_PORT}/generate \
   -X POST \
   -d "$DATA" \
   -H 'Content-Type: application/json'
   ```

5. LLM Service (if your used application with FaqGen)

   ```bash
   DATA='{"messages":"Text Embeddings Inference (TEI) is a toolkit for deploying and serving open source '\
   'text embeddings and sequence classification models. TEI enables high-performance extraction for the most '\
   'popular models, including FlagEmbedding, Ember, GTE and E5.","max_tokens": 128}'

   curl http://${HOST_IP}:${CHATQNA_LLM_FAQGEN_PORT}/v1/faqgen \
     -X POST \
     -d "$DATA" \
     -H 'Content-Type: application/json'
   ```

## Conclusion

This guide should enable developers to deploy the default configuration or any of the other compose yaml files for different configurations. It also highlights the configurable parameters that can be set before deployment.
