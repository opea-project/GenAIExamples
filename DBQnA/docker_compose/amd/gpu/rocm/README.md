# Example DBQnA Deployment on AMD GPU (ROCm)

This document outlines the deployment process for DBQnA application which helps generating a SQL query and its output given a NLP question, utilizing the [GenAIComps](https://github.com/opea-project/GenAIComps.git) microservice pipeline on an AMD GPU. This example includes the following sections:

- [DBQnA Quick Start Deployment](#dbqna-quick-start-deployment): Demonstrates how to quickly deploy a DBQnA service/pipeline on AMD GPU (ROCm).
- [DBQnA Docker Compose Files](#dbqna-docker-compose-files): Describes some example deployments and their docker compose files.

## DBQnA Quick Start Deployment

This section describes how to quickly deploy and test the DBQnA service manually on AMD GPU (ROCm). The basic steps are:

- [Example DBQnA Deployment on AMD GPU (ROCm)](#example-dbqna-deployment-on-amd-gpu-rocm)
  - [DBQnA Quick Start Deployment](#dbqna-quick-start-deployment)
    - [Access the Code](#access-the-code)
    - [Generate a HuggingFace Access Token](#generate-a-huggingface-access-token)
    - [Configure the Deployment Environment](#configure-the-deployment-environment)
    - [Deploy the Service Using Docker Compose](#deploy-the-service-using-docker-compose)
    - [Check the Deployment Status](#check-the-deployment-status)
    - [Test the Pipeline](#test-the-pipeline)
    - [Cleanup the Deployment](#cleanup-the-deployment)
  - [DBQnA Docker Compose Files](#dbqna-docker-compose-files)
  - [DBQnA Service Configuration for AMD GPUs](#dbqna-service-configuration-for-amd-gpus)

### Access the Code

Clone the GenAIExample repository and access the DBQnA AMD GPU (ROCm) Docker Compose files and supporting scripts:

```
git clone https://github.com/opea-project/GenAIExamples.git
cd GenAIExamples/DBQnA/docker_compose/
```

Checkout a released version, such as v1.3:

```
git checkout v1.3
```

### Generate a HuggingFace Access Token

Some HuggingFace resources, such as some models, are only accessible if you have an access token. If you do not already have a HuggingFace access token, you can create one by first creating an account by following the steps provided at [HuggingFace](https://huggingface.co/) and then generating a [user access token](https://huggingface.co/docs/transformers.js/en/guides/private#step-1-generating-a-user-access-token).
Docker image creation, container deployment via Docker Compose, and service execution to integrate microservices. We will publish the Docker images to Docker Hub soon, which will simplify the deployment process for this service.

### Configure the Deployment Environment

To set up environment variables for deploying DBQnA service, source the _set_env.sh_ script in this directory:

```
source amd/gpu/rocm/set_env.sh
```

The _set_env.sh_ script will prompt for required and optional environment variables used to configure the DBQnA service based on TGI. If a value is not entered, the script will use a default value for the same. It will also generate a _.env_ file defining the desired configuration.

### Deploy the Service Using Docker Compose

To deploy the DBQnA service, execute the `docker compose up` command with the appropriate arguments. For a default deployment, execute:

```bash
cd amd/gpu/rocm/
docker compose -f compose.yaml up -d
```

The DBQnA docker images should automatically be downloaded from the `OPEA registry` and deployed on the AMD GPU (ROCm)

### Check the Deployment Status

After running docker compose, check if all the containers launched via docker compose have started:

```
docker ps -a
```

For the default deployment, the following 4 containers should be running.

### Test the Pipeline

Once the DBQnA service are running, test the pipeline using the following command:

```bash
url="postgresql://${POSTGRES_USER}:${POSTGRES_PASSWORD}@${host_ip}:5442/${POSTGRES_DB}"
curl --connect-timeout 5 --max-time 120000 http://${host_ip}:9090/v1/text2query\
    -X POST \
    -d '{"query": "Find the total number of Albums.","conn_type": "sql", "conn_url": "'${url}'", "conn_user": "'${POSTGRES_USER}'","conn_password": "'${POSTGRES_PASSWORD}'","conn_dialect": "postgresql" }' \
    -H 'Content-Type: application/json')
```

### Cleanup the Deployment

To stop the containers associated with the deployment, execute the following command:

```
docker compose -f compose.yaml down
```

All the DBQnA containers will be stopped and then removed on completion of the "down" command.

## DBQnA Docker Compose Files

The compose.yaml is default compose file using tgi as serving framework

| Service Name      | Image Name                                               |
| ----------------- | -------------------------------------------------------- |
| dbqna-tgi-service | ghcr.io/huggingface/text-generation-inference:2.4.1-rocm |
| postgres          | postgres:latest                                          |
| text2sql          | opea/text2query-sql:latest                               |
| text2sql-react-ui | opea/text2sql-react-ui:latest                            |

## DBQnA Service Configuration for AMD GPUs

The table provides a comprehensive overview of the DBQnA service utilized across various deployments as illustrated in the example Docker Compose files. Each row in the table represents a distinct service, detailing its possible images used to enable it and a concise description of its function within the deployment architecture.

| Service Name      | Possible Image Names                                     | Optional | Description                                                                                         |
| ----------------- | -------------------------------------------------------- | -------- | --------------------------------------------------------------------------------------------------- |
| dbqna-tgi-service | ghcr.io/huggingface/text-generation-inference:2.4.1-rocm | No       | Specific to the TGI deployment, focuses on text generation inference using AMD GPU (ROCm) hardware. |
| postgres          | postgres:latest                                          | No       | Provides the relational database backend for storing and querying data used by the DBQnA pipeline.  |
| text2sql          | opea/text2query-sql:latest                               | No       | Handles text-to-SQL conversion tasks.                                                               |
| text2sql-react-ui | opea/text2sql-react-ui:latest                            | No       | Provides the user interface for the DBQnA service.                                                  |
