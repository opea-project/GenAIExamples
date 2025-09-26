# Example DBQnA Deployment on Intel® Xeon® Platform

This document outlines the deployment process for DBQnA application which helps generating a SQL query and its output given a NLP question, utilizing the [GenAIComps](https://github.com/opea-project/GenAIComps.git) microservice pipeline on an Intel Xeon server.

- [DBQnA Quick Start Deployment](#dbqna-quick-start-deployment): Demonstrates how to quickly deploy a DBQnA service/pipeline on Intel® Xeon® platform.
- [DBQnA Docker Compose Files](#dbqna-docker-compose-files): Describes some example deployments and their docker compose files.

## DBQnA Quick Start Deployment

This section describes how to quickly deploy and test the DBQnA service manually on Intel® Xeon® platform. The basic steps are:

- [Example DBQnA Deployment on Intel® Xeon® Platform](#example-dbqna-deployment-on-intel-xeon-platform)
  - [DBQnA Quick Start Deployment](#dbqna-quick-start-deployment)
    - [Access the Code](#access-the-code)
    - [Generate a HuggingFace Access Token](#generate-a-huggingface-access-token)
    - [Configure the Deployment Environment](#configure-the-deployment-environment)
    - [Deploy the Service Using Docker Compose](#deploy-the-service-using-docker-compose)
    - [Check the Deployment Status](#check-the-deployment-status)
    - [Test the Pipeline](#test-the-pipeline)
    - [Cleanup the Deployment](#cleanup-the-deployment)
  - [DBQnA Docker Compose Files](#dbqna-docker-compose-files)
  - [DBQnA Service Configuration](#dbqna-service-configuration)

### Access the Code

Clone the GenAIExample repository and access the DBQnA Intel® Xeon® platform Docker Compose files and supporting scripts:

```
git clone https://github.com/opea-project/GenAIExamples.git
cd GenAIExamples/DBQnA/docker_compose/intel/cpu/xeon/
```

Checkout a released version, such as v1.3:

```
git checkout v1.3
```

### Generate a HuggingFace Access Token

Some HuggingFace resources, such as some models, are only accessible if you have an access token. If you do not already have a HuggingFace access token, you can create one by first creating an account by following the steps provided at [HuggingFace](https://huggingface.co/) and then generating a [user access token](https://huggingface.co/docs/transformers.js/en/guides/private#step-1-generating-a-user-access-token).

### Configure the Deployment Environment

To set up environment variables for deploying DBQnA service, source the set_env.sh script in this directory:

```
source set_env.sh
```

The set*env.sh script will prompt for required and optional environment variables used to configure the DBQnA service. If a value is not entered, the script will use a default value for the same. It will also generate a *.env\_ file defining the desired configuration.

### Deploy the Service Using Docker Compose

To deploy the DBQnA service, execute the `docker compose up` command with the appropriate arguments. For a default deployment, execute:

```bash
docker compose up -d
```

The DBQnA docker images should automatically be downloaded from the `OPEA registry` and deployed on the Intel® Xeon® Platform:

```
[+] Running 5/5
 ✔ Network xeon_default                  Created                                                                            0.1s
 ✔ Container tgi-service                 Started                                                                            5.9s
 ✔ Container postgres-container          Started                                                                            5.8s
 ✔ Container text2sql-service            Started                                                                            6.0s
 ✔ Container dbqna-xeon-react-ui-server  Started                                                                            0.9s
```

### Check the Deployment Status

After running docker compose, check if all the containers launched via docker compose have started:

```
docker ps -a
```

For the default deployment, the following 5 containers should be running:

```
CONTAINER ID   IMAGE                                                                                       COMMAND                  CREATED         STATUS         PORTS                                       NAMES
2728db31368b   opea/text2sql-react-ui:latest                                                               "nginx -g 'daemon of…"   9 minutes ago   Up 9 minutes   0.0.0.0:5174->80/tcp, :::5174->80/tcp       dbqna-xeon-react-ui-server
0ab75b92c300   postgres:latest                                                                             "docker-entrypoint.s…"   9 minutes ago   Up 9 minutes   0.0.0.0:5442->5432/tcp, :::5442->5432/tcp   postgres-container
2662a69b515b   ghcr.io/huggingface/text-generation-inference:2.4.0-intel-cpu                               "text-generation-lau…"   9 minutes ago   Up 9 minutes   0.0.0.0:8008->80/tcp, :::8008->80/tcp       tgi-service
bb44512be80e   opea/text2query-sql:latest                                                                  "python opea_text2sq…"   9 minutes ago   Up 9 minutes   0.0.0.0:9090->8080/tcp, :::9090->8080/tcp   text2sql-service
```

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

```
[+] Running 5/5
 ✔ Container postgres-container          Removed                                                                 0.5s
 ✔ Container tgi-service                 Removed                                                                 2.9s
 ✔ Container dbqna-xeon-react-ui-server  Removed                                                                 0.6s
 ✔ Container text2sql-service            Removed                                                                10.3s
 ✔ Network xeon_default                  Removed                                                                 0.4s
```

All the DBQnA containers will be stopped and then removed on completion of the "down" command.

## DBQnA Docker Compose Files

The compose.yaml is default compose file using tgi as serving framework

| Service Name               | Image Name                                                    |
| -------------------------- | ------------------------------------------------------------- |
| tgi-service                | ghcr.io/huggingface/text-generation-inference:2.4.0-intel-cpu |
| postgres                   | postgres:latest                                               |
| text2sql                   | opea/text2query-sql:latest                                    |
| dbqna-xeon-react-ui-server | opea/text2sql-react-ui:latest                                 |

## DBQnA Service Configuration

The table provides a comprehensive overview of the DBQnA service utilized across various deployments as illustrated in the example Docker Compose files. Each row in the table represents a distinct service, detailing its possible images used to enable it and a concise description of its function within the deployment architecture.

| Service Name               | Possible Image Names                                          | Optional | Description                                                                                         |
| -------------------------- | ------------------------------------------------------------- | -------- | --------------------------------------------------------------------------------------------------- |
| tgi-service                | ghcr.io/huggingface/text-generation-inference:2.4.0-intel-cpu | No       | Specific to the TGI deployment, focuses on text generation inference using AMD GPU (ROCm) hardware. |
| postgres                   | postgres:latest                                               | No       | Provides the relational database backend for storing and querying data used by the DBQnA pipeline.  |
| text2sql                   | opea/text2query-sql:latest                                    | No       | Handles text-to-SQL conversion tasks.                                                               |
| dbqna-xeon-react-ui-server | opea/text2sql-react-ui:latest                                 | No       | Provides the user interface for the DBQnA service.                                                  |
