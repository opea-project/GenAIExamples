# Example Edge Craft Retrieval-Augmented Generation Deployment on Intel® Arc® Platform

This document outlines the deployment process for Edge Craft Retrieval-Augmented Generation service on Intel Arc server. This example includes the following sections:

- [EdgeCraftRAG Quick Start Deployment](#edgecraftrag-quick-start-deployment): Demonstrates how to quickly deploy a Edge Craft Retrieval-Augmented Generation service/pipeline on Intel® Arc® platform.
- [EdgeCraftRAG Docker Compose Files](#edgecraftrag-docker-compose-files): Describes some example deployments and their docker compose files.
- [EdgeCraftRAG Service Configuration](#edgecraftrag-service-configuration): Describes the service and possible configuration changes.

## EdgeCraftRAG Quick Start Deployment

This section describes how to quickly deploy and test the EdgeCraftRAG service manually on Intel® Arc® platform. The basic steps are:

1. [Prerequisites](#prerequisites)
2. [Access the Code](#access-the-code)
3. [Generate a HuggingFace Access Token](#generate-a-huggingface-access-token)
4. [Configure the Deployment Environment](#configure-the-deployment-environment)
5. [Deploy the Service Using Docker Compose](#deploy-the-service-using-docker-compose)
6. [Check the Deployment Status](#check-the-deployment-status)
7. [Test the Pipeline](#test-the-pipeline)
8. [Cleanup the Deployment](#cleanup-the-deployment)

### Prerequisites

EC-RAG supports vLLM deployment(default method) and local OpenVINO deployment for Intel Arc GPU. Prerequisites are shown as below:  
Hardware: Intel Arc A770  
OS: Ubuntu Server 22.04.1 or newer (at least 6.2 LTS kernel)  
Driver & libraries: please refer to [Installing Client GPUs](https://dgpu-docs.intel.com/driver/client/overview.html) for detailed driver & libraries setup

Below steps are based on **vLLM** as inference engine, if you want to choose **OpenVINO**, please refer to [OpenVINO Local Inference](../../../../docs/Advanced_Setup.md#openvino-local-inference)

### Access the Code

Clone the GenAIExample repository and access the EdgeCraftRAG Intel® Arc® platform Docker Compose files and supporting scripts:

```
git clone https://github.com/opea-project/GenAIExamples.git
cd GenAIExamples/EdgeCraftRAG/docker_compose/intel/gpu/arc/
```

Checkout a released version, such as v1.3:

```
git checkout v1.3
```

### Generate a HuggingFace Access Token

Some HuggingFace resources, such as some models, are only accessible if you have an access token. If you do not already have a HuggingFace access token, you can create one by first creating an account by following the steps provided at [HuggingFace](https://huggingface.co/) and then generating a [user access token](https://huggingface.co/docs/transformers.js/en/guides/private#step-1-generating-a-user-access-token).

### Configure the Deployment Environment

Below steps are for single Intel Arc GPU inference, if you want to setup multi Intel Arc GPUs inference, please refer to [Multi-ARC Setup](../../../../docs/Advanced_Setup.md#multi-arc-setup)
To set up environment variables for deploying EdgeCraftRAG service, source the set_env.sh script in this directory:

```
source set_env.sh
```

For more advanced env variables and configurations, please refer to [Prepare env variables for vLLM deployment](../../../../docs/Advanced_Setup.md#prepare-env-variables-for-vllm-deployment)

### Deploy the Service Using Docker Compose

To deploy the EdgeCraftRAG service, execute the `docker compose up` command with the appropriate arguments. For a default deployment, execute:

```bash
docker compose up -d
```

The EdgeCraftRAG docker images should automatically be downloaded from the `OPEA registry` and deployed on the Intel® Arc® Platform

### Check the Deployment Status

After running docker compose, check if all the containers launched via docker compose have started:

```
docker ps -a
```

For the default deployment, the following 5 containers should be running:

### Test the Pipeline

Once the EdgeCraftRAG service are running, test the pipeline using the following command:

```bash
curl http://${host_ip}:16011/v1/chatqna -H 'Content-Type: application/json' -d '{
     "messages":"What is the test id?","max_tokens":5 }'
```

For detailed operations on UI and EC-RAG settings, please refer to [Explore_Edge_Craft_RAG](../../../../docs/Explore_Edge_Craft_RAG.md)

**Note** The value of _host_ip_ was set using the _set_env.sh_ script and can be found in the _.env_ file.

### Cleanup the Deployment

To stop the containers associated with the deployment, execute the following command:

```
docker compose -f compose.yaml down
```

All the EdgeCraftRAG containers will be stopped and then removed on completion of the "down" command.

## EdgeCraftRAG Docker Compose Files

The compose.yaml is default compose file using tgi as serving framework

| Service Name        | Image Name                               |
| ------------------- | ---------------------------------------- |
| etcd                | quay.io/coreos/etcd:v3.5.5               |
| minio               | minio/minio:RELEASE.2023-03-20T20-16-18Z |
| milvus-standalone   | milvusdb/milvus:v2.4.6                   |
| edgecraftrag-server | opea/edgecraftrag-server:latest          |
| edgecraftrag-ui     | opea/edgecraftrag-ui:latest              |
| ecrag               | opea/edgecraftrag:latest                 |

## EdgeCraftRAG Service Configuration

The table provides a comprehensive overview of the EdgeCraftRAG service utilized across various deployments as illustrated in the example Docker Compose files. Each row in the table represents a distinct service, detailing its possible images used to enable it and a concise description of its function within the deployment architecture.

| Service Name        | Possible Image Names                     | Optional | Description                                                                                      |
| ------------------- | ---------------------------------------- | -------- | ------------------------------------------------------------------------------------------------ |
| etcd                | quay.io/coreos/etcd:v3.5.5               | No       | Provides distributed key-value storage for service discovery and configuration management.       |
| minio               | minio/minio:RELEASE.2023-03-20T20-16-18Z | No       | Provides object storage services for storing documents and model files.                          |
| milvus-standalone   | milvusdb/milvus:v2.4.6                   | No       | Provides vector database capabilities for managing embeddings and similarity search.             |
| edgecraftrag-server | opea/edgecraftrag-server:latest          | No       | Serves as the backend for the EdgeCraftRAG service, with variations depending on the deployment. |
| edgecraftrag-ui     | opea/edgecraftrag-ui:latest              | No       | Provides the user interface for the EdgeCraftRAG service.                                        |
| ecrag               | opea/edgecraftrag:latest                 | No       | Acts as a reverse proxy, managing traffic between the UI and backend services.                   |
