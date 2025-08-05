# Deploying MultimodalQnA on AMD GPU (ROCm)

This document outlines the deployment process for a MultimodalQnA application utilizing the [GenAIComps](https://github.com/opea-project/GenAIComps.git) microservice pipeline on AMD server with ROCm GPUs. The steps include Docker image creation, container deployment via Docker Compose, and service execution to integrate microservices such as `multimodal_embedding` that employs [BridgeTower](https://huggingface.co/BridgeTower/bridgetower-large-itm-mlm-gaudi) model as embedding model, `multimodal_retriever`, `lvm`, and `multimodal-data-prep`.

# Table of Contents

1. [MultimodalQnA Quick Start Deployment](#multimodalqna-quick-start-deployment)
2. [MultimodalQnA Docker Compose Files](#multimodalqna-docker-compose-files)
3. [Validate Microservices](#validate-microservices)
4. [Conclusion](#conclusion)

## MultimodalQnA Quick Start Deployment

This section describes how to quickly deploy and test the MultimodalQnA service manually on an AMD GPU (ROCm) processor. The basic steps are:

1. [Access the Code](#access-the-code)
2. [Configure the Deployment Environment](#configure-the-deployment-environment)
3. [Deploy the Services Using Docker Compose](#deploy-the-services-using-docker-compose)
4. [Check the Deployment Status](#check-the-deployment-status)
5. [Validate the Pipeline](#validate-the-pipeline)
6. [Cleanup the Deployment](#cleanup-the-deployment)

### Access the Code

Clone the GenAIExamples repository and access the MultimodalQnA AMD GPU (ROCm) platform Docker Compose files and supporting scripts:

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

  We set these values in the file set_env\*\*\*\*.sh

- **Variables with names like "**\*\*\*\*\*\*\_PORT"\*\* - These variables set the IP port numbers for establishing network connections to the application services.
  The values shown in the file set_env.sh or set_env_vllm they are the values used for the development and testing of the application, as well as configured for the environment in which the development is performed. These values must be configured in accordance with the rules of network access to your environment's server, and must not overlap with the IP ports of other applications that are already in use.

Setting variables in the operating system environment:

```bash
export HF_TOKEN="Your_HuggingFace_API_Token"
source ./set_env_*.sh # replace the script name with the appropriate one
```

Consult the section on [MultimodalQnA Service configuration](#multimodalqna-docker-compose-files) for information on how service specific configuration parameters affect deployments.

### Deploy the Services Using Docker Compose

To deploy the MultimodalQnA services, execute the `docker compose up` command with the appropriate arguments. For a default deployment with TGI, execute the command below. It uses the 'compose.yaml' file.

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
  - /dev/dri/:/dev/dri/
cap_add:
  - SYS_PTRACE
group_add:
  - video
security_opt:
  - seccomp:unconfined
```

This configuration forwards all available GPUs to the container. To use a specific GPU, specify its cardN and renderN device IDs. For example:

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

### Check the Deployment Status

Check if all the containers launched via docker compose have started:

```bash
docker ps -a
```

For the default deployment with TGI, the following 10 containers should have started:

```
CONTAINER ID   IMAGE                                                    COMMAND                  STATUS          PORTS                                       NAMES
3bfa91d2ac8c   opea/multimodalqna-ui:latest                             "docker-entrypoint.sh"   Up 2 minutes    0.0.0.0:5173->5173/tcp                      multimodalqna-gradio-ui-server
1e93a6f60b7e   opea/multimodalqna:latest                                "docker-entrypoint.sh"   Up 2 minutes    0.0.0.0:8888->8888/tcp                      multimodalqna-backend-server
98b1a8a7ef23   opea/lvm:latest                                          "docker-entrypoint.sh"   Up 3 minutes    0.0.0.0:9399->9399/tcp                      lvm
a743dcdfb3d7   ghcr.io/huggingface/text-generation-inference:2.4.1-rocm "/entrypoint.sh ..."     Up 3 minutes    0.0.0.0:8399->80/tcp                        tgi-llava-rocm-server
ba0f72a62e4b   opea/retriever:latest                                    "docker-entrypoint.sh"   Up 3 minutes    0.0.0.0:7000->7000/tcp                      retriever-redis
e5a429aac4f7   opea/embedding:latest                                    "docker-entrypoint.sh"   Up 3 minutes    0.0.0.0:7061->7061/tcp                      embedding
ad25a3fc3cdd   opea/embedding-multimodal-bridgetower:latest            "python bridgetower..."  Up 3 minutes    0.0.0.0:7050->7050/tcp                      embedding-multimodal-bridgetower
d834adc71bd4   opea/dataprep:latest                                     "docker-entrypoint.sh"   Up 3 minutes    0.0.0.0:6007->5000/tcp                      dataprep-multimodal-redis
4fd73dabc267   redis/redis-stack:7.2.0-v9                               "redis-stack-server"     Up 4 minutes    0.0.0.0:6379->6379/tcp, 8001->8001/tcp      redis-vector-db
dfdf41dcd8e1   opea/whisper:latest                                      "docker-entrypoint.sh"   Up 4 minutes    0.0.0.0:7066->7066/tcp                      whisper-service

```

if used vLLM:

```
CONTAINER ID   IMAGE                                      COMMAND                  STATUS          PORTS                                       NAMES
cf3193a3e7c1   opea/multimodalqna-ui:latest               "docker-entrypoint.sh"   Up 2 minutes    0.0.0.0:5173->5173/tcp                      multimodalqna-gradio-ui-server
a14a529b06d2   opea/multimodalqna:latest                  "docker-entrypoint.sh"   Up 2 minutes    0.0.0.0:8888->8888/tcp                      multimodalqna-backend-server
e91f81b6dc27   opea/lvm:latest                            "docker-entrypoint.sh"   Up 3 minutes    0.0.0.0:9399->9399/tcp                      lvm
de5f2a4024bb   opea/vllm-rocm:latest                      "/bin/sh -c '--model…"   Up 3 minutes    0.0.0.0:8081->8011/tcp                      multimodalqna-vllm-service
f9918f9cba12   opea/retriever:latest                      "docker-entrypoint.sh"   Up 3 minutes    0.0.0.0:7000->7000/tcp                      retriever-redis
d4a3a6e31fc2   opea/embedding:latest                      "docker-entrypoint.sh"   Up 3 minutes    0.0.0.0:7061->7061/tcp                      embedding
9cd19b2fc1f0   opea/embedding-multimodal-bridgetower:latest  "python bridgetower…"   Up 3 minutes    0.0.0.0:7050->7050/tcp                      embedding-multimodal-bridgetower
b3e9135a9c23   opea/dataprep:latest                       "docker-entrypoint.sh"   Up 3 minutes    0.0.0.0:6007->5000/tcp                      dataprep-multimodal-redis
ab00bc56fa67   redis/redis-stack:7.2.0-v9                 "redis-stack-server"     Up 4 minutes    0.0.0.0:6379->6379/tcp, 8001->8001/tcp      redis-vector-db
d9f2172bb875   opea/whisper:latest                        "docker-entrypoint.sh"   Up 4 minutes    0.0.0.0:7066->7066/tcp                      whisper-service
```

If any issues are encountered during deployment, refer to the [Troubleshooting](../../../../README_miscellaneous.md#troubleshooting) section.

### Validate the Pipeline

Once the MultimodalQnA services are running, test the pipeline using the following command:

```bash
DATA='{"messages": [{"role": "user", "content": [{"type": "audio", "audio": "UklGRigAAABXQVZFZm10IBIAAAABAAEARKwAAIhYAQACABAAAABkYXRhAgAAAAEA"}]}]}'

curl http://${HOST_IP}:8888/v1/multimodalqna \
  -H "Content-Type: application/json" \
  -d "$DATA"
```

### Cleanup the Deployment

To stop the containers associated with the deployment, execute the following command:

```bash
# if used TGI
docker compose -f compose.yaml down
# if used vLLM
# docker compose -f compose_vllm.yaml down
```

## MultimodalQnA Docker Compose Files

In the context of deploying a MultimodalQnA pipeline on an AMD GPU (ROCm) platform, we can pick and choose different large language model serving frameworks. The table below outlines the various configurations that are available as part of the application. These configurations can be used as templates and can be extended to different components available in [GenAIComps](https://github.com/opea-project/GenAIComps.git).

| File                                     | Description                                                                                |
| ---------------------------------------- | ------------------------------------------------------------------------------------------ |
| [compose.yaml](./compose.yaml)           | Default compose file using TGI as serving framework                                        |
| [compose_vllm.yaml](./compose_vllm.yaml) | The LLM serving framework is vLLM. All other configurations remain the same as the default |

## Validate Microservices

### embedding-multimodal-bridgetower

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

### embedding

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

### retriever-multimodal-redis

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

### whisper service

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

This guide should enable developer to deploy the default configuration or any of the other compose yaml files for different configurations. It also highlights the configurable parameters that can be set before deployment.
