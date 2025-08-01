# Deploying SearchQnA on AMD EPYC™ Processors

This document details the deployment process of the SearchQnA application on a single node, leveraging the [GenAIComps](https://github.com/opea-project/GenAIComps.git) microservices, optimized for AMD EPYC™ Processors.

## Table of Contents

1. [SearchQnA Quick Start Deployment](#searchqna-quick-start-deployment)
2. [SearchQnA Docker Compose Files](#searchqna-docker-compose-files)
3. [Validate Microservices](#validate-microservices)
4. [Conclusion](#conclusion)

## SearchQnA Quick Start Deployment

This section describes how to quickly deploy and test the SearchQnA service manually on an AMD EPYC™ processor. The basic steps are:

1. [Access the Code](#access-the-code)
2. [Install Docker](#install-docker)
3. [Determine your host's external IP address](#determine-your-host-external-ip-address)
4. [Generate a HuggingFace Access Token](#generate-a-huggingface-access-token)
5. [Configure the Deployment Environment](#configure-the-deployment-environment)
6. [Deploy the Services Using Docker Compose](#deploy-the-services-using-docker-compose)
7. [Check the Deployment Status](#check-the-deployment-status)
8. [Validate the Pipeline](#validate-the-pipeline)
9. [Cleanup the Deployment](#cleanup-the-deployment)

### Access the Code

Clone the GenAIExample repository and access the SearchQnA AMD EPYC™ platform Docker Compose files and supporting scripts:

```bash
git clone https://github.com/opea-project/GenAIExamples.git
cd GenAIExamples/SearchQnA/docker_compose/amd/cpu/epyc
```

### Install Docker

Ensure Docker is installed on your system. If Docker is not already installed, use the provided script to set it up:

    source ./install_docker.sh

This script installs Docker and its dependencies. After running it, verify the installation by checking the Docker version:

    docker --version

If Docker is already installed, this step can be skipped.

### Determine your host external IP address

Run the following command in your terminal to list network interfaces:

    ifconfig

Look for the inet address associated with your active network interface (e.g., enp99s0). For example:

    enp99s0: flags=4163<UP,BROADCAST,RUNNING,MULTICAST>  mtu 1500
        inet 10.101.16.119  netmask 255.255.255.0  broadcast 10.101.16.255

In this example, the (`host_ip`) would be (`10.101.16.119`).

    # Replace with your host's external IP address
    export host_ip="your_external_ip_address"

### Generate a HuggingFace Access Token

Some HuggingFace resources, such as some models, are only accessible if you have an access token. If you do not already have a HuggingFace access token, you can create one by first creating an account by following the steps provided at [HuggingFace](https://huggingface.co/) and then generating a [user access token](https://huggingface.co/docs/transformers.js/en/guides/private#step-1-generating-a-user-access-token).

```bash
export HF_TOKEN="your_huggingface_token"
```

### Configure the Deployment Environment

The model_cache directory, by default, stores models in the ./data directory. To change this, use the following command:

```bash
# Optional
export model_cache=/home/documentation/data_searchqna/data # Path to save cache models
```

To set up environment variables for deploying SearchQnA services, set up some parameters specific to the deployment environment and then source the `set_env.sh` script in this directory:

The environment variables `GOOGLE_CSE_ID` and `GOOGLE_API_KEY` must be set. To create an API key:

1. Open the (Google Cloud Console: Credentials.)[(https://console.cloud.google.com/apis/credentials)]
2. Click Create credentials → API key

To enable the Custom Search API:

1. To enable the Custom Search API on a Google account follow [here](https://programmablesearchengine.google.com/controlpanel/create)

```bash
export GOOGLE_API_KEY="your google api key"
export GOOGLE_CSE_ID="your cse id"
```

```bash
export http_proxy="Your_HTTP_Proxy"           # http proxy if any
export https_proxy="Your_HTTPs_Proxy"         # https proxy if any
export no_proxy=localhost,127.0.0.1,$host_ip  # additional no proxies if needed
export NGINX_PORT=${your_nginx_port}          # your usable port for nginx, 80 for example
```

Finally set the other environment variables

```bash
source ./set_env.sh
```

### Deploy the Services Using Docker Compose

To deploy the SearchQnA services, execute the `docker compose up` command with the appropriate arguments. For a default deployment, execute the command below. It uses the 'compose.yaml' file.

```bash
docker compose -f compose.yaml up -d
```

> **Note**: developers should build docker image from source when:
>
> - Developing off the git main branch (as the container's ports in the repo may be different > from the published docker image).
> - Unable to download the docker image.
> - Use a specific version of Docker image.

Please refer to the table below to build different microservices from source:

| Microservice | Deployment Guide                                                                                   |
| ------------ | -------------------------------------------------------------------------------------------------- |
| Embedding    | [Embedding build guide](https://github.com/opea-project/GenAIComps/tree/main/comps/embeddings/src) |
| Retriever    | [Retriever build guide](https://github.com/opea-project/GenAIComps/tree/main/comps/retrievers/src) |
| Reranking    | [Reranking build guide](https://github.com/opea-project/GenAIComps/tree/main/comps/rerankings/src) |
| LLM          | [LLM build guide](https://github.com/opea-project/GenAIComps/tree/main/comps/llms)                 |
| MegaService  | [MegaService build guide](../../../../README_miscellaneous.md#build-megaservice-docker-image)      |
| UI           | [Basic UI build guide](../../../../README_miscellaneous.md#build-ui-docker-image)                  |

### Check the Deployment Status

After running docker compose, check if all the containers launched via docker compose have started:

```bash
docker ps -a
```

For the default deployment, the following containers should have started

If any issues are encountered during deployment, refer to the [Troubleshooting](../../../../README_miscellaneous.md#troubleshooting) section.

### Validate the Pipeline

Once the SearchQnA services are running, test the pipeline using the following command:

```bash
curl http://${host_ip}:3008/v1/searchqna -H "Content-Type: application/json" -d '{
     "messages": "What is the latest news? Give me also the source link.",
     "stream": "true"
     }'
```

**Note** : Access the SearchQnA UI by web browser through this URL: `http://${host_ip}:80`. Please confirm the `80` port is opened in the firewall. To validate each microservice used in the pipeline refer to the [Validate Microservices](#validate-microservices) section.

### Cleanup the Deployment

To stop the containers associated with the deployment, execute the following command:

```bash
docker compose -f compose.yaml down
```

## SearchQnA Docker Compose Files

When deploying a SearchQnA pipeline on an AMD EPYC™ platform, different large language model serving frameworks can be selected. The table below outlines the available configurations included in the application. These configurations can serve as templates and be extended to other components available in [GenAIComps](https://github.com/opea-project/GenAIComps.git).

| File                           | Description                                                                       |
| ------------------------------ | --------------------------------------------------------------------------------- |
| [compose.yaml](./compose.yaml) | Default compose file using vllm as serving framework and redis as vector database |

## Validate Microservices

1. Embedding backend Service

   ```bash
    curl http://${host_ip}:3001/embed \
        -X POST \
        -d '{"inputs":"What is Deep Learning?"}' \
        -H 'Content-Type: application/json'
   ```

2. Embedding Microservice

   ```bash
    curl http://${host_ip}:3002/v1/embeddings\
      -X POST \
      -d '{"text":"hello"}' \
      -H 'Content-Type: application/json'
   ```

3. Web Retriever Microservice

   ```bash
    export your_embedding=$(python3 -c "import random; embedding = [random.uniform(-1, 1) for _ in range(768)]; print(embedding)")
    curl http://${host_ip}:3003/v1/web_retrieval \
      -X POST \
      -d "{\"text\":\"What is the 2024 holiday schedule?\",\"embedding\":${your_embedding}}" \
      -H 'Content-Type: application/json'
   ```

4. Reranking backend Service

```bash
 # TEI Reranking service
  curl http://${host_ip}:3004/rerank \
      -X POST \
      -d '{"query":"What is Deep Learning?", "texts": ["Deep Learning is not...", "Deep learning is..."]}' \
      -H 'Content-Type: application/json'
```

5. Reranking Microservice

```bash
  curl http://${host_ip}:3005/v1/reranking\
    -X POST \
    -d '{"initial_query":"What is Deep Learning?", "retrieved_docs": [{"text":"Deep Learning is not..."}, {"text":"Deep learning is..."}]}' \
    -H 'Content-Type: application/json'
```

6. LLM backend Service

```bash
 # TGI service
  curl http://${host_ip}:3006/generate \
    -X POST \
    -d '{"inputs":"What is Deep Learning?","parameters":{"max_new_tokens":17, "do_sample": true}}' \
    -H 'Content-Type: application/json'
```

7. LLM Microservice

   ```bash
    curl http://${host_ip}:3007/v1/chat/completions\
      -X POST \
      -d '{"query":"What is Deep Learning?","max_tokens":17,"top_k":10,"top_p":0.95,"typical_p":0.95,"temperature":0.01,"repetition_penalty":1.03,"stream":true}' \
      -H 'Content-Type: application/json'
   ```

8. MegaService

   ```bash
    curl http://${host_ip}:3008/v1/searchqna -H "Content-Type: application/json" -d '{
        "messages": "What is the latest news? Give me also the source link.",
        "stream": "true"
        }'
   ```

9. Nginx Service

   ```bash
   curl http://${host_ip}:${NGINX_PORT}/v1/searchqna \
       -H "Content-Type: application/json" \
       -d '{
        "messages": "What is the latest news? Give me also the source link.",
        "stream": "true"
        }'
   ```

## Conclusion

This guide should enable developer to deploy the default configuration or any of the other compose yaml files for different configurations. It also highlights the configurable parameters that can be set before deployment.
