# Example Productivity Suite Deployment on Intel® Xeon® Platform

This document outlines the deployment process for OPEA Productivity Suite utilizing the [GenAIComps](https://github.com/opea-project/GenAIComps.git) microservice pipeline on Intel Xeon server.This example includes the following sections:

- [Productivity Suite Quick Start Deployment](#productivity-suite-quick-start-deployment): Demonstrates how to quickly deploy a Productivity Suite service/pipeline on Intel® Xeon® platform.
- [Productivity Suite Docker Compose Files](#productivity-suite-docker-compose-files): Describes some example deployments and their docker compose files.
- [Productivity Suite Service Configuration](#productivity-suite-service-configuration): Describes the service and possible configuration changes.

## Productivity Suite Quick Start Deployment

This section describes how to quickly deploy and test the Productivity Suite service manually on Intel® Xeon® platform. The basic steps are:

- [Example Productivity Suite Deployment on Intel® Xeon® Platform](#example-productivity-suite-deployment-on-intel-xeon-platform)
  - [Productivity Suite Quick Start Deployment](#productivity-suite-quick-start-deployment)
    - [Access the Code](#access-the-code)
    - [Generate a HuggingFace Access Token](#generate-a-huggingface-access-token)
    - [Configure the Deployment Environment](#configure-the-deployment-environment)
    - [Deploy the Service Using Docker Compose](#deploy-the-service-using-docker-compose)
    - [Check the Deployment Status](#check-the-deployment-status)
    - [Setup Keycloak](#setup-keycloak)
    - [Test the Pipeline](#test-the-pipeline)
    - [Cleanup the Deployment](#cleanup-the-deployment)
  - [Productivity Suite Docker Compose Files](#productivity-suite-docker-compose-files)
  - [Productivity Suite Service Configuration](#productivity-suite-service-configuration)
    - [Running LLM models with remote endpoints](#running-llm-models-with-remote-endpoints)

### Access the Code

Clone the GenAIExample repository and access the Productivity Suite Intel® Xeon® platform Docker Compose files and supporting scripts:

```
git clone https://github.com/opea-project/GenAIExamples.git
cd GenAIExamples/ProductivitySuite/docker_compose/intel/cpu/xeon/
```

Checkout a released version, such as v1.3:

```
git checkout v1.3
```

### Generate a HuggingFace Access Token

Some HuggingFace resources, such as some models, are only accessible if you have an access token. If you do not already have a HuggingFace access token, you can create one by first creating an account by following the steps provided at [HuggingFace](https://huggingface.co/) and then generating a [user access token](https://huggingface.co/docs/transformers.js/en/guides/private#step-1-generating-a-user-access-token).

### Configure the Deployment Environment

To set up environment variables for deploying Productivity Suite service, source the set_env.sh script in this directory:

```
export host_ip=<ip-address-of-the-machine>
source set_env.sh
```

The set_env.sh script will prompt for required and optional environment variables used to configure the Productivity Suite service. If a value is not entered, the script will use a default value for the same. It will also generate a env file defining the desired configuration. Consult the section on [Productivity Suite Service configuration](#productivity-suite-service-configuration) for information on how service specific configuration parameters affect deployments.

### Deploy the Service Using Docker Compose

To deploy the Productivity Suite service, execute the `docker compose up` command with the appropriate arguments. For a default deployment, execute:

```bash
docker compose up -d
```

The Productivity Suite docker images should automatically be downloaded from the `OPEA registry` and deployed on the Intel® Xeon® Platform:

```
[+] Running 19/19
 ✔ Network xeon_default                               Created                                         0.1s
 ✔ Container tgi-service                              Healthy                                       165.2s
 ✔ Container promptregistry-mongo-server              Started                                         1.0s
 ✔ Container redis-vector-db                          Started                                         1.7s
 ✔ Container tei-reranking-server                     Healthy                                        61.5s
 ✔ Container chathistory-mongo-server                 Started                                         1.7s
 ✔ Container tgi_service_codegen                      Healthy                                       165.7s
 ✔ Container tei-embedding-server                     Healthy                                        12.0s
 ✔ Container keycloak-server                          Started                                         0.8s
 ✔ Container whisper-server                           Started                                         1.4s
 ✔ Container productivity-suite-xeon-react-ui-server  Started                                         2.1s
 ✔ Container mongodb                                  Started                                         1.2s
 ✔ Container dataprep-redis-server                    Healthy                                        22.9s
 ✔ Container retriever-redis-server                   Started                                         2.2s
 ✔ Container llm-textgen-server-codegen               Started                                       166.0s
 ✔ Container docsum-xeon-llm-server                   Started                                       165.5s
 ✔ Container codegen-xeon-backend-server              Started                                       166.3s
 ✔ Container docsum-xeon-backend-server               Started                                       165.9s
 ✔ Container chatqna-xeon-backend-server              Started                                       165.9s
```

### Check the Deployment Status

After running docker compose, check if all the containers launched via docker compose have started:

```
docker ps -a
```

For the default deployment, the following 5 containers should be running:

```
CONTAINER ID   IMAGE                                                                                       COMMAND                  CREATED         STATUS                   PORTS                                                                                  NAMES
8e3c0e9398ae   opea/chatqna:latest                                                                         "bash entrypoint.sh"     8 minutes ago   Up 5 minutes             0.0.0.0:8888->8888/tcp, :::8888->8888/tcp                                              chatqna-xeon-backend-server
cc317e6feb89   opea/docsum:latest                                                                          "python docsum.py"       8 minutes ago   Up 5 minutes             0.0.0.0:8890->8888/tcp, :::8890->8888/tcp                                              docsum-xeon-backend-server
683dd7cacef2   opea/codegen:latest                                                                         "python codegen.py"      8 minutes ago   Up 5 minutes             0.0.0.0:7778->7778/tcp, :::7778->7778/tcp                                              codegen-xeon-backend-server
a38d8d906cd0   opea/llm-docsum:latest                                                                      "python opea_docsum_…"   8 minutes ago   Up 5 minutes             0.0.0.0:9003->9000/tcp, :::9003->9000/tcp                                              docsum-xeon-llm-server
f0a61333ae16   opea/llm-textgen:latest                                                                     "bash entrypoint.sh"     8 minutes ago   Up 5 minutes             0.0.0.0:9001->9000/tcp, :::9001->9000/tcp                                              llm-textgen-server-codegen
a942446f47c1   opea/dataprep:latest                                                                        "sh -c 'python $( [ …"   8 minutes ago   Up 8 minutes (healthy)   0.0.0.0:6007->5000/tcp, :::6007->5000/tcp                                              dataprep-redis-server
f77b9b69fcaf   opea/retriever:latest                                                                       "python opea_retriev…"   8 minutes ago   Up 8 minutes             0.0.0.0:7001->7000/tcp, :::7001->7000/tcp                                              retriever-redis-server
0324b9efd729   opea/productivity-suite-react-ui-server:latest                                              "/docker-entrypoint.…"   8 minutes ago   Up 8 minutes             0.0.0.0:5174->80/tcp, :::5174->80/tcp                                                  productivity-suite-xeon-react-ui-server
747e09a5afea   ghcr.io/huggingface/text-generation-inference:2.4.0-intel-cpu                               "text-generation-lau…"   8 minutes ago   Up 8 minutes (healthy)   0.0.0.0:8028->80/tcp, :::8028->80/tcp                                                  tgi_service_codegen
ea7444faa8b2   ghcr.io/huggingface/text-generation-inference:2.4.0-intel-cpu                               "text-generation-lau…"   8 minutes ago   Up 8 minutes (healthy)   0.0.0.0:9009->80/tcp, :::9009->80/tcp                                                  tgi-service
8fdb186853ac   opea/whisper:latest                                                                         "python whisper_serv…"   8 minutes ago   Up 8 minutes             0.0.0.0:7066->7066/tcp, :::7066->7066/tcp                                              whisper-server
7982f2d1ff89   mongo:7.0.11                                                                                "docker-entrypoint.s…"   8 minutes ago   Up 8 minutes             0.0.0.0:27017->27017/tcp, :::27017->27017/tcp                                          mongodb
9fb471c452ec   quay.io/keycloak/keycloak:25.0.2                                                            "/opt/keycloak/bin/k…"   8 minutes ago   Up 8 minutes             8443/tcp, 0.0.0.0:8080->8080/tcp, :::8080->8080/tcp, 9000/tcp                          keycloak-server
a00ac544abb7   ghcr.io/huggingface/text-embeddings-inference:cpu-1.6                                       "/bin/sh -c 'apt-get…"   8 minutes ago   Up 8 minutes (healthy)   0.0.0.0:6006->80/tcp, :::6006->80/tcp                                                  tei-embedding-server
87c2996111d5   redis/redis-stack:7.2.0-v9                                                                  "/entrypoint.sh"         8 minutes ago   Up 8 minutes             0.0.0.0:6379->6379/tcp, :::6379->6379/tcp, 0.0.0.0:8001->8001/tcp, :::8001->8001/tcp   redis-vector-db
536b71e4ec67   opea/chathistory:latest                                                                     "python opea_chathis…"   8 minutes ago   Up 8 minutes             0.0.0.0:6012->6012/tcp, :::6012->6012/tcp                                              chathistory-mongo-server
8d56c2b03431   opea/promptregistry:latest                                                                  "python opea_prompt_…"   8 minutes ago   Up 8 minutes             0.0.0.0:6018->6018/tcp, :::6018->6018/tcp                                              promptregistry-mongo-server
c48921438848   ghcr.io/huggingface/text-embeddings-inference:cpu-1.6                                       "/bin/sh -c 'apt-get…"   8 minutes ago   Up 8 minutes (healthy)   0.0.0.0:8808->80/tcp, :::8808->80/tcp                                                  tei-reranking-server
```

### Setup Keycloak

Please refer to **[keycloak_setup_guide](keycloak_setup_guide.md)** for more detail related to Keycloak configuration setup.

### Test the Pipeline

Once the Productivity Suite service are running, test the pipeline using the following command:

ChatQnA MegaService

```bash
curl http://${host_ip}:8888/v1/chatqna -H "Content-Type: application/json" -d '{
    "messages": "What is the revenue of Nike in 2023?"
    }'
```

DocSum MegaService

```bash
curl http://${host_ip}:8890/v1/docsum -H "Content-Type: application/json" -d '{
    "messages": "Text Embeddings Inference (TEI) is a toolkit for deploying and serving open source text embeddings and sequence classification models. TEI enables high-performance extraction for the most popular models, including FlagEmbedding, Ember, GTE and E5.",
    "type": "text"
    }'
```

CodeGen MegaService

```bash
curl http://${host_ip}:7778/v1/codegen -H "Content-Type: application/json" -d '{
      "messages": "def print_hello_world():"
      }'
```

### Cleanup the Deployment

To stop the containers associated with the deployment, execute the following command:

```
docker compose -f compose.yaml down
```

```
[+] Running 19/19
 ✔ Container mongodb                                  Removed                                                     0.5s
 ✔ Container codegen-xeon-backend-server              Removed                                                    10.4s
 ✔ Container docsum-xeon-backend-server               Removed                                                    10.6s
 ✔ Container whisper-server                           Removed                                                     1.3s
 ✔ Container promptregistry-mongo-server              Removed                                                    10.8s
 ✔ Container chatqna-xeon-backend-server              Removed                                                    11.0s
 ✔ Container productivity-suite-xeon-react-ui-server  Removed                                                     0.6s
 ✔ Container keycloak-server                          Removed                                                     0.7s
 ✔ Container chathistory-mongo-server                 Removed                                                    10.9s
 ✔ Container llm-textgen-server-codegen               Removed                                                    10.4s
 ✔ Container docsum-xeon-llm-server                   Removed                                                    10.4s
 ✔ Container tei-reranking-server                     Removed                                                    13.0s
 ✔ Container tei-embedding-server                     Removed                                                    12.8s
 ✔ Container dataprep-redis-server                    Removed                                                    12.9s
 ✔ Container retriever-redis-server                   Removed                                                    12.3s
 ✔ Container tgi_service_codegen                      Removed                                                     3.1s
 ✔ Container tgi-service                              Removed                                                     3.1s
 ✔ Container redis-vector-db                          Removed                                                     0.5s
 ✔ Network xeon_default                               Removed                                                     0.3s
```

All the Productivity Suite containers will be stopped and then removed on completion of the "down" command.

## Productivity Suite Docker Compose Files

The compose.yaml is default compose file using tgi as serving framework

| Service Name                            | Image Name                                                    |
| --------------------------------------- | ------------------------------------------------------------- |
| chathistory-mongo-server                | opea/chathistory:latest                                       |
| chatqna-xeon-backend-server             | opea/chatqna:latest                                           |
| codegen-xeon-backend-server             | opea/codegen:latest                                           |
| dataprep-redis-server                   | opea/dataprep:latest                                          |
| docsum-xeon-backend-server              | opea/docsum:latest                                            |
| docsum-xeon-llm-server                  | opea/llm-docsum:latest                                        |
| keycloak-server                         | quay.io/keycloak/keycloak:25.0.2                              |
| llm-textgen-server-codegen              | opea/llm-textgen:latest                                       |
| mongodb                                 | mongo:7.0.11                                                  |
| productivity-suite-xeon-react-ui-server | opea/productivity-suite-react-ui-server:latest                |
| promptregistry-mongo-server             | opea/promptregistry:latest                                    |
| redis-vector-db                         | redis/redis-stack:7.2.0-v9                                    |
| retriever-redis-server                  | opea/retriever:latest                                         |
| tei-embedding-server                    | ghcr.io/huggingface/text-embeddings-inference:cpu-1.6         |
| tei-reranking-server                    | ghcr.io/huggingface/text-embeddings-inference:cpu-1.6         |
| tgi_service_codegen                     | ghcr.io/huggingface/text-generation-inference:2.4.0-intel-cpu |
| tgi-service                             | ghcr.io/huggingface/text-generation-inference:2.4.0-intel-cpu |
| whisper-server                          | opea/whisper:latest                                           |

## Productivity Suite Service Configuration

The table provides a comprehensive overview of the Productivity Suite service utilized across various deployments as illustrated in the example Docker Compose files. Each row in the table represents a distinct service, detailing its possible images used to enable it and a concise description of its function within the deployment architecture.

| Service Name                            | Possible Image Names                                          | Optional | Description                                                                                                      |
| --------------------------------------- | ------------------------------------------------------------- | -------- | ---------------------------------------------------------------------------------------------------------------- |
| chathistory-mongo-server                | opea/chathistory:latest                                       | No       | Handles chat history storage and retrieval using MongoDB.                                                        |
| chatqna-xeon-backend-server             | opea/chatqna:latest                                           | No       | Handles question answering and chat interactions.                                                                |
| codegen-xeon-backend-server             | opea/codegen:latest                                           | No       | Handles code generation tasks.                                                                                   |
| dataprep-redis-server                   | opea/dataprep:latest                                          | No       | Handles data preparation and preprocessing tasks for downstream services.                                        |
| docsum-xeon-backend-server              | opea/docsum:latest                                            | No       | Handles document summarization tasks.                                                                            |
| docsum-xeon-llm-server                  | opea/llm-docsum:latest                                        | No       | Handles large language model (LLM) based document summarization.                                                 |
| keycloak-server                         | quay.io/keycloak/keycloak:25.0.2                              | No       | Handles authentication and authorization using Keycloak.                                                         |
| llm-textgen-server-codegen              | opea/llm-textgen:latest                                       | No       | Handles large language model (LLM) text generation tasks, providing inference APIs for code and text completion. |
| mongodb                                 | mongo:7.0.11                                                  | No       | Provides persistent storage for application data using MongoDB.                                                  |
| productivity-suite-xeon-react-ui-server | opea/productivity-suite-react-ui-server:latest                | No       | Hosts the web-based user interface for interacting with the Productivity Suite services.                         |
| promptregistry-mongo-server             | opea/promptregistry:latest                                    | No       | Manages storage and retrieval of prompt templates and related metadata.                                          |
| redis-vector-db                         | redis/redis-stack:7.2.0-v9                                    | No       | Offers in-memory data storage and vector database capabilities for fast retrieval and caching.                   |
| retriever-redis-server                  | opea/retriever:latest                                         | No       | Handles retrieval-augmented generation tasks, enabling efficient document and context retrieval.                 |
| tei-embedding-server                    | ghcr.io/huggingface/text-embeddings-inference:cpu-1.6         | No       | Provides text embedding and sequence classification services for downstream NLP tasks.                           |
| tei-reranking-server                    | ghcr.io/huggingface/text-embeddings-inference:cpu-1.6         | No       | Performs reranking of retrieved documents or results using embedding-based similarity.                           |
| tgi_service_codegen                     | ghcr.io/huggingface/text-generation-inference:2.4.0-intel-cpu | No       | Serves code generation models for inference, optimized for Intel Xeon CPUs.                                      |
| tgi-service                             | ghcr.io/huggingface/text-generation-inference:2.4.0-intel-cpu | No       | Specific to the TGI deployment, focuses on text generation inference using Xeon hardware.                        |
| whisper-server                          | opea/whisper:latest                                           | No       | Provides speech-to-text transcription services using Whisper models.                                             |

### Running LLM models with remote endpoints

When models are deployed on a remote server, a base URL and an API key are required to access them. To set up a remote server and acquire the base URL and API key, refer to [Intel® AI for Enterprise Inference](https://www.intel.com/content/www/us/en/developer/topic-technology/artificial-intelligence/enterprise-inference.html) offerings.

Set the following environment variables.

- `REMOTE_ENDPOINT` is the HTTPS endpoint of the remote server with the model of choice (i.e. https://api.example.com). **Note:** If the API for the models does not use LiteLLM, the second part of the model card needs to be appended to the URL. For example, set `REMOTE_ENDPOINT` to https://api.example.com/Llama-3.3-70B-Instruct if the model card is `meta-llama/Llama-3.3-70B-Instruct`.
- `API_KEY` is the access token or key to access the model(s) on the server.
- `LLM_MODEL_ID` is the model card which may need to be overwritten depending on what it is set to `set_env.sh`.

```bash
export DocSum_COMPONENT_NAME="OpeaDocSumvLLM"
export REMOTE_ENDPOINT=<https-endpoint-of-remote-server>
export API_KEY=<your-api-key>
export LLM_MODEL_ID=<model-card>
export LLM_MODEL_ID_CODEGEN=<model-card>
```

After setting these environment variables, run `docker compose` with `compose_remote.yaml`:

```bash
docker compose -f compose_remote.yaml up -d
```
