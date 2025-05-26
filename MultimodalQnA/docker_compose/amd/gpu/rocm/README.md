# Deploying MultimodalQnA on AMD ROCm GPU

This document outlines the single node deployment process for a Multimodal application utilizing the [GenAIComps](https://github.com/opea-project/GenAIComps.git) microservices on Intel Xeon server and AMD GPU. The steps include pulling Docker images, container deployment via Docker Compose, and service execution using microservices `llm`.


Note: The default LLM model is Xkev/Llama-3.2V-11B-cot. Before you deploy the application, make sure to request and obtain access to this application on [Huggingface](https://huggingface.co/Xkev/Llama-3.2V-11B-cot). Alternatively, you can download the model locally from [ModelScope](https://www.modelscope.cn/models)..

## Table of Contents

1. [MultimodalQnA Quick Start Deployment](#multimodalqna-quick-start-deployment)
2. [MultimodalQnA Docker Compose Files](#multimodalqna-docker-compose-files)
3. [Validate Microservices](#validate-microservices)
4. [Conclusion](#conclusion)

## MultimodalQnA Quick Start Deployment

This section describes how to quickly deploy and test the MultimodalQnA Service manually on an AMD ROCm GPU. The basic steps are:

1. [Access the Code](#access-the-code)
2. [Configure the Deployment Environment](#configure-the-deployment-environment)
3. [Deploy the Services Using Docker Compose](#deploy-the-services-using-docker-compose)
4. [Check the Deployment Status](#check-the-deployment-status)
5. [Validate the Pipeline](#validate-the-pipeline)
6. [Cleanup the Deployment](#cleanup-the-deployment)

### Access the Code

Clone the GenAIExample repository and access the MultimodalQnA AMD ROCm GPU platform Docker Compose files and supporting scripts:

```bash
git clone https://github.com/opea-project/GenAIExamples.git
cd GenAIExamples/MultimodalQnA
```

Then checkout a released version, such as v1.3:

```bash
git checkout v1.3
```

### Configure the Deployment Environment

To set up environment variables for deploying MultimodalQnA services, set up some parameters specific to the deployment environment and source the `set_env_*.sh` script in this directory:

- if used vLLM - set_env_vllm.sh
- if used TGI - set_env.sh

Set the values of the variables:

- **HOST_IP, HOST_IP_EXTERNAL** - These variables are used to configure the name/address of the service in the operating system environment for the application services to interact with each other and with the outside world.

  If your server uses only an internal address and is not accessible from the Internet, then the values for these two variables will be the same and the value will be equal to the server's internal name/address.

  If your server uses only an external, Internet-accessible address, then the values for these two variables will be the same and the value will be equal to the server's external name/address.

  If your server is located on an internal network, has an internal address, but is accessible from the Internet via a proxy/firewall/load balancer, then the HOST_IP variable will have a value equal to the internal name/address of the server, and the EXTERNAL_HOST_IP variable will have a value equal to the external name/address of the proxy/firewall/load balancer behind which the server is located.

  We set these values in the file set_env*.sh

- **Variables with names like "***_PORT***" - These variables set the IP port numbers to establish network connections to the application services..
  The values shown in the file set_env.sh or set_env_vllm.sh they are the values used for the development and testing of the application, as well as configured for the environment in which the development is performed. These values must be configured in accordance with the rules of network access to your environment's server, and must not overlap with the IP ports of other applications that are already in use.

Setting variables in the operating system environment:

```bash
export HUGGINGFACEHUB_API_TOKEN="Your_HuggingFace_API_Token"
source ./set_env_*.sh # replace the script name with the appropriate one
```

Consult the section on [MultimodalQnA Service configuration](#multimodalqna-configuration) for information on how service specific configuration parameters affect deployments.

### Deploy the Services Using Docker Compose

To deploy the MultimodalQnA services, execute the `docker compose up` command with the appropriate arguments. For a default deployment with TGI, execute the command below. It uses the 'compose.yaml' file.

```bash
cd docker_compose/amd/gpu/rocm
# if used TGI
docker compose -f compose.yaml up -d

# if used vLLM

docker compose -f compose_vllm.yaml up -d
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
| whisper-service | [whisper build guide](https://github.com/opea-project/GenAIComps/tree/main/comps/third_parties/whisper/src)        |
| LVM             | [lvm build guide](https://github.com/opea-project/GenAIComps/blob/main/comps/lvms/src/)                            |
| Nginx           | [Nginx guide](https://github.com/opea-project/GenAIComps/tree/main/comps/third_parties/nginx)                      |

### Check the Deployment Status

After running docker compose, check if all the containers launched via docker compose have started:

```bash
docker ps -a
```

For the default deployment with TGI, the following 9 containers should have started:

```
CONTAINER ID   IMAGE                                                      COMMAND                  CREATED         STATUS                   PORTS                                                                                  NAMES
427c4dde68e2   opea/multimodalqna-ui:latest                               "python multimodalqn…"   2 minutes ago   Up About a minute        0.0.0.0:5173->5173/tcp, :::5173->5173/tcp                                              multimodalqna-gradio-ui-server
5cb2186d961a   opea/multimodalqna:latest                                  "python multimodalqn…"   2 minutes ago   Up About a minute        0.0.0.0:8888->8888/tcp, :::8888->8888/tcp                                              multimodalqna-backend-server
70e512d483e0   opea/dataprep:latest                                       "sh -c 'python $( [ …"   2 minutes ago   Up 2 minutes (healthy)   0.0.0.0:6007->5000/tcp, [::]:6007->5000/tcp                                            dataprep-multimodal-redis
86927af3de6d   opea/retriever:latest                                      "python opea_retriev…"   2 minutes ago   Up 2 minutes             0.0.0.0:7000->7000/tcp, :::7000->7000/tcp                                              retriever-redis
74cc8db43457   opea/embedding:latest                                      "sh -c 'python $( [ …"   2 minutes ago   Up About a minute        0.0.0.0:6000->6000/tcp, :::6000->6000/tcp                                              embedding
49a7c128752d   opea/lvm:latest                                            "python opea_lvm_mic…"   2 minutes ago   Up 2 minutes             0.0.0.0:9399->9399/tcp, :::9399->9399/tcp                                              lvm
0d66fda22534   ghcr.io/huggingface/text-generation-inference:2.4.1-rocm   "/tgi-entrypoint.sh …"   2 minutes ago   Up 24 seconds            0.0.0.0:8399->80/tcp, [::]:8399->80/tcp                                                tgi-llava-rocm-server
55908da067d7   opea/embedding-multimodal-bridgetower:latest               "python bridgetower_…"   2 minutes ago   Up 2 minutes (healthy)   0.0.0.0:6006->6006/tcp, :::6006->6006/tcp                                              embedding-multimodal-bridgetower
8a4283f61cf5   redis/redis-stack:7.2.0-v9                                 "/entrypoint.sh"         2 minutes ago   Up 2 minutes             0.0.0.0:6379->6379/tcp, :::6379->6379/tcp, 0.0.0.0:8001->8001/tcp, :::8001->8001/tcp   redis-vector-db
e9e5f1f3b57a   opea/whisper:latest                                        "python whisper_serv…"   2 minutes ago   Up 2 minutes             0.0.0.0:7066->7066/tcp, :::7066->7066/tcp                                              whisper-service
3923edad3acc   opea/vllm-rocm:latest                                      "python3 /workspace/…"   24 hours ago    Up 24 hours (healthy)    0.0.0.0:8086->8011/tcp, [::]:8086->8011/tcp                                            vllm-service
```

if used vLLM:

```
CONTAINER ID   IMAGE                                          COMMAND                  CREATED          STATUS                    PORTS                                                                                  NAMES
54f8a87b82be   opea/multimodalqna-ui:latest                   "python multimodalqn…"   42 seconds ago   Up 9 seconds              0.0.0.0:5173->5173/tcp, :::5173->5173/tcp                                              multimodalqna-gradio-ui-server
e533d862cf8e   opea/multimodalqna:latest                      "python multimodalqn…"   42 seconds ago   Up 9 seconds              0.0.0.0:8888->8888/tcp, :::8888->8888/tcp                                              multimodalqna-backend-server
e11e96d03e54   opea/dataprep:latest                           "sh -c 'python $( [ …"   42 seconds ago   Up 40 seconds (healthy)   0.0.0.0:6007->5000/tcp, [::]:6007->5000/tcp                                            dataprep-multimodal-redis
f5e670dae343   opea/lvm:latest                                "python opea_lvm_mic…"   42 seconds ago   Up 40 seconds             0.0.0.0:9399->9399/tcp, :::9399->9399/tcp                                              lvm
c81bd4792b22   opea/retriever:latest                          "python opea_retriev…"   42 seconds ago   Up 40 seconds             0.0.0.0:7000->7000/tcp, :::7000->7000/tcp                                              retriever-redis
220c1111d5e4   opea/embedding:latest                          "sh -c 'python $( [ …"   42 seconds ago   Up 15 seconds             0.0.0.0:6000->6000/tcp, :::6000->6000/tcp                                              embedding
ece52eea577f   opea/vllm-rocm:latest                          "python3 /workspace/…"   42 seconds ago   Up 41 seconds             0.0.0.0:8081->8011/tcp, [::]:8081->8011/tcp                                            multimodalqna-vllm-service
82bd3be58052   opea/embedding-multimodal-bridgetower:latest   "python bridgetower_…"   42 seconds ago   Up 41 seconds (healthy)   0.0.0.0:6006->6006/tcp, :::6006->6006/tcp                                              embedding-multimodal-bridgetower
bac14dac272d   opea/whisper:latest                            "python whisper_serv…"   42 seconds ago   Up 41 seconds             0.0.0.0:7066->7066/tcp, :::7066->7066/tcp                                              whisper-service
7d603688fc56   redis/redis-stack:7.2.0-v9                     "/entrypoint.sh"         42 seconds ago   Up 41 seconds             0.0.0.0:6379->6379/tcp, :::6379->6379/tcp, 0.0.0.0:8001->8001/tcp, :::8001->8001/tcp   redis-vector-db
```

### Validate the Pipeline

Once the MultimodalQnA services are running, test the pipeline using the following command:

```bash
DATA='{"messages": [{"role": "user", "content": [{"type": "audio", "audio": "UklGRigAAABXQVZFZm10IBIAAAABAAEARKwAAIhYAQACABAAAABkYXRhAgAAAAEA"}]}]}'

curl http://${HOST_IP}:${MULTIMODALQNA_BACKEND_SERVICE_PORT}/v1/multimodalqna \
  -H "Content-Type: application/json" \
  -d "$DATA"
```

Checking the response from the service. The response should be similar to text:

```textmate
{"id":"chatcmpl-75aK2KWCfxZmVcfh5tiiHj","object":"chat.completion","created":1743568232,"model":"multimodalqna","choices":[{"index":0,"message":{"role":"assistant","content":"There is no video segments retrieved given the query!"},"finish_reason":"stop","metadata":{"audio":"you"}}],"usage":{"prompt_tokens":0,"total_tokens":0,"completion_tokens":0}}
```

If the output lines in the "choices.text" keys contain words (tokens) containing meaning, then the service is considered launched successfully.

### Cleanup the Deployment

To stop the containers associated with the deployment, execute the following command:

```bash
# if used TGI
docker compose -f compose.yaml down

# if used vLLM
 docker compose -f compose_vllm.yaml down
```

## MultimodalQnA Docker Compose Files

In the context of deploying an MultimodalQnA pipeline on an AMD ROCm platform, we can pick and choose different large language model serving frameworks, or single English TTS/multi-language TTS component. The table below outlines the various configurations that are available as part of the application. These configurations can be used as templates and can be extended to different components available in [GenAIComps](https://github.com/opea-project/GenAIComps.git).

| File                                     | Description                                                                                                         |
| ---------------------------------------- | ------------------------------------------------------------------------------------------------------------------  | 
| [compose.yaml](./compose.yaml)           | The LLM serving framework is TGI. Default compose file using TGI as serving framework and redis as vector database. |
| [compose_vllm.yaml](./compose_vllm.yaml) | The LLM serving framework is vLLM. Compose file using vllm as serving framework and redis as vector database.       |

## Validate MicroServices

### 1. Embedding-multimodal-bridgetower

Text example:

```bash
curl http://${host_ip}:${EMM_BRIDGETOWER_PORT}/v1/encode \
     -X POST \
     -H "Content-Type:application/json" \
     -d '{"text":"This is example"}'
```

Checking the response from the service. The response should be similar to text:

```textmate
{"embedding":[0.036936961114406586,-0.0022056063171476126,0.0891181230545044,-0.019263656809926033,-0.049174826592206955,-0.05129311606287956,-0.07172256708145142,0.04365323856472969,0.03275766223669052,0.0059910244308412075,-0.0301326...,-0.0031989417038857937,0.042092420160770416]}
```

Image example:

```bash
curl http://${host_ip}:${EMM_BRIDGETOWER_PORT}/v1/encode \
     -X POST \
     -H "Content-Type:application/json" \
     -d '{"text":"This is example", "img_b64_str": "iVBORw0KGgoAAAANSUhEUgAAAAoAAAAKCAYAAACNMs+9AAAAFUlEQVR42mP8/5+hnoEIwDiqkL4KAcT9GO0U4BxoAAAAAElFTkSuQmCC"}'
```

Checking the response from the service. The response should be similar to text:

```textmate
{"embedding":[0.024372786283493042,-0.003916610032320023,0.07578050345182419,...,-0.046543147414922714]}
```

### 2. Embedding

Text example:

```bash
curl http://${host_ip}:$MM_EMBEDDING_PORT_MICROSERVICE/v1/embeddings \
    -X POST \
    -H "Content-Type: application/json" \
    -d '{"text" : "This is some sample text."}'
```

Checking the response from the service. The response should be similar to text:

```textmate
{"id":"4fb722012a2719e38188190e1cb37ed3","text":"This is some sample text.","embedding":[0.043303076177835464,-0.051807764917612076,...,-0.0005179636646062136,-0.0027774290647357702],"search_type":"similarity","k":4,"distance_threshold":null,"fetch_k":20,"lambda_mult":0.5,"score_threshold":0.2,"constraints":null,"url":null,"base64_image":null}
```

Image example:

```bash
curl http://${host_ip}:${EMM_BRIDGETOWER_PORT}/v1/encode \
     -X POST \
     -H "Content-Type:application/json" \
     -d '{"text":"This is example", "img_b64_str": "iVBORw0KGgoAAAANSUhEUgAAAAoAAAAKCAYAAACNMs+9AAAAFUlEQVR42mP8/5+hnoEIwDiqkL4KAcT9GO0U4BxoAAAAAElFTkSuQmCC"}'
```

Checking the response from the service. The response should be similar to text:

```textmate
{"id":"cce4eab623255c4c632fb920e277dcf7","text":"This is some sample text.","embedding":[0.02613169699907303,-0.049398183822631836,...,0.03544217720627785],"search_type":"similarity","k":4,"distance_threshold":null,"fetch_k":20,"lambda_mult":0.5,"score_threshold":0.2,"constraints":null,"url":"https://github.com/docarray/docarray/blob/main/tests/toydata/image-data/apple.png?raw=true","base64_image":"iVBORw0KGgoAAAANSUhEUgAAAoEAAAJqCAMAAABjDmrLAAAABGdBTUEAALGPC/.../BCU5wghOc4AQnOMEJTnCCE5zgBCc4wQlOcILzqvO/ARWd2ns+lvHkAAAAAElFTkSuQmCC"}
```

### 3. Retriever-multimodal-redis

set "your_embedding" variable:

```bash
export your_embedding=$(python3 -c "import random; embedding = [random.uniform(-1, 1) for _ in range(512)]; print(embedding)")
```

Test Redis retriever

```bash
curl http://${host_ip}:${REDIS_RETRIEVER_PORT}/v1/retrieval \
    -X POST \
    -H "Content-Type: application/json" \
    -d "{\"text\":\"test\",\"embedding\":${your_embedding}}"
```

Checking the response from the service. The response should be similar to text:

```textmate
{"id":"80a4f3fc5f5d5cd31ab1e3912f6b6042","retrieved_docs":[],"initial_query":"test","top_n":1,"metadata":[]}
```

### 4. Whisper service

```bash
curl http://${host_ip}:7066/v1/asr \
  -X POST \
  -d '{"audio": "UklGRigAAABXQVZFZm10IBIAAAABAAEARKwAAIhYAQACABAAAABkYXRhAgAAAAEA"}' \
  -H 'Content-Type: application/json'
```

Checking the response from the service. The response should be similar to text:

```textmate
{"asr_result":"you"}
```

## Conclusion

This guide should enable developers to deploy the default configuration or any of the other compose yaml files for different configurations. It also highlights the configurable parameters that can be set before deployment.
