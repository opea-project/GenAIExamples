# Example Translation Deployment on Intel® Gaudi® Platform

This document outlines the deployment process for a Translation service utilizing the [GenAIComps](https://github.com/opea-project/GenAIComps.git) microservice pipeline on Intel Gaudi server. This example includes the following sections:

- [Translation Quick Start Deployment](#translation-quick-start-deployment): Demonstrates how to quickly deploy a Translation service/pipeline on Intel® Gaudi® platform.
- [Translation Docker Compose Files](#translation-docker-compose-files): Describes some example deployments and their docker compose files.
- [Translation Service Configuration](#translation-service-configuration): Describes the service and possible configuration changes.

## Translation Quick Start Deployment

This section describes how to quickly deploy and test the Translation service manually on Intel® Gaudi® platform. The basic steps are:

1. [Access the Code](#access-the-code)
2. [Generate a HuggingFace Access Token](#generate-a-huggingface-access-token)
3. [Configure the Deployment Environment](#configure-the-deployment-environment)
4. [Deploy the Service Using Docker Compose](#deploy-the-service-using-docker-compose)
5. [Check the Deployment Status](#check-the-deployment-status)
6. [Test the Pipeline](#test-the-pipeline)
7. [Cleanup the Deployment](#cleanup-the-deployment)

### Access the Code

Clone the GenAIExample repository and access the Translation Intel® Gaudi® platform Docker Compose files and supporting scripts:

```
git clone https://github.com/opea-project/GenAIExamples.git
cd GenAIExamples/Translation/docker_compose/intel/hpu/gaudi/
```

Checkout a released version, such as v1.2:

```
git checkout v1.2
```

### Generate a HuggingFace Access Token

Some HuggingFace resources, such as some models, are only accessible if you have an access token. If you do not already have a HuggingFace access token, you can create one by first creating an account by following the steps provided at [HuggingFace](https://huggingface.co/) and then generating a [user access token](https://huggingface.co/docs/transformers.js/en/guides/private#step-1-generating-a-user-access-token).

### Configure the Deployment Environment

To set up environment variables for deploying Translation service, source the _set_env.sh_ script in this directory:

```
cd ../../../
source set_env.sh
cd intel/hpu/gaudi/
```

The set_env.sh script will prompt for required and optional environment variables used to configure the Translation service. If a value is not entered, the script will use a default value for the same. It will also generate a env file defining the desired configuration. Consult the section on [Translation Service configuration](#translation-service-configuration) for information on how service specific configuration parameters affect deployments.

### Deploy the Service Using Docker Compose

To deploy the Translation service, execute the `docker compose up` command with the appropriate arguments. For a default deployment, execute:

```bash
docker compose up -d
```

The Translation docker images should automatically be downloaded from the `OPEA registry` and deployed on the Intel® Gaudi® Platform:

```
[+] Running 5/5
 ✔ Container tgi-gaudi-server                  Healthy                                                          222.4s
 ✔ Container llm-textgen-gaudi-server          Started                                                          221.7s
 ✔ Container translation-gaudi-backend-server  Started                                                          222.0s
 ✔ Container translation-gaudi-ui-server       Started                                                          222.2s
 ✔ Container translation-gaudi-nginx-server    Started                                                          222.6s
```

### Check the Deployment Status

After running docker compose, check if all the containers launched via docker compose have started:

```
docker ps -a
```

For the default deployment, the following 5 containers should be running:

```
CONTAINER ID   IMAGE                                 COMMAND                  CREATED         STATUS                   PORTS                                       NAMES
097f577b3a53   opea/nginx:latest                     "/docker-entrypoint.…"   5 minutes ago   Up About a minute        0.0.0.0:80->80/tcp, :::80->80/tcp           translation-gaudi-nginx-server
0578b7034af3   opea/translation-ui:latest            "docker-entrypoint.s…"   5 minutes ago   Up About a minute        0.0.0.0:5173->5173/tcp, :::5173->5173/tcp   translation-gaudi-ui-server
bc23dd5b9cb0   opea/translation:latest               "python translation.…"   5 minutes ago   Up About a minute        0.0.0.0:8888->8888/tcp, :::8888->8888/tcp   translation-gaudi-backend-server
2cf6fabaa7c7   opea/llm-textgen:latest               "bash entrypoint.sh"     5 minutes ago   Up About a minute        0.0.0.0:9000->9000/tcp, :::9000->9000/tcp   llm-textgen-gaudi-server
f4764d0c1817   ghcr.io/huggingface/tgi-gaudi:2.3.1   "/tgi-entrypoint.sh …"   5 minutes ago   Up 5 minutes (healthy)   0.0.0.0:8008->80/tcp, [::]:8008->80/tcp     tgi-gaudi-server
```

### Test the Pipeline

Once the Translation service are running, test the pipeline using the following command:

```bash
curl http://${host_ip}:8888/v1/translation -H "Content-Type: application/json" -d '{
     "language_from": "Chinese","language_to": "English","source_language": "我爱机器翻译。"}'
```

**Note** The value of _host_ip_ was set using the _set_env.sh_ script and can be found in the _.env_ file.

### Cleanup the Deployment

To stop the containers associated with the deployment, execute the following command:

```
docker compose -f compose.yaml down
```

```
[+] Running 6/6
 ✔ Container translation-gaudi-nginx-server    Removed                                                                                                                                                10.5s
 ✔ Container translation-gaudi-ui-server       Removed                                                                                                                                                10.3s
 ✔ Container translation-gaudi-backend-server  Removed                                                                                                                                                10.4s
 ✔ Container llm-textgen-gaudi-server          Removed                                                                                                                                                10.4s
 ✔ Container tgi-gaudi-server                  Removed                                                                                                                                                12.0s
 ✔ Network gaudi_default                       Removed                                                                                                                                                 0.4s
```

All the Translation containers will be stopped and then removed on completion of the "down" command.

## Translation Docker Compose Files

The compose.yaml is default compose file using tgi as serving framework

| Service Name                     | Image Name                          |
| -------------------------------- | ----------------------------------- |
| tgi-service                      | ghcr.io/huggingface/tgi-gaudi:2.3.1 |
| llm                              | opea/llm-textgen:latest             |
| translation-gaudi-backend-server | opea/translation:latest             |
| translation-gaudi-ui-server      | opea/translation-ui:latest          |
| translation-gaudi-nginx-server   | opea/nginx:latest                   |

## Translation Service Configuration

The table provides a comprehensive overview of the Translation service utilized across various deployments as illustrated in the example Docker Compose files. Each row in the table represents a distinct service, detailing its possible images used to enable it and a concise description of its function within the deployment architecture.

| Service Name                     | Possible Image Names                | Optional | Description                                                                                     |
| -------------------------------- | ----------------------------------- | -------- | ----------------------------------------------------------------------------------------------- |
| tgi-service                      | ghcr.io/huggingface/tgi-gaudi:2.3.1 | No       | Specific to the TGI deployment, focuses on text generation inference using Gaudi hardware.      |
| llm                              | opea/llm-textgen:latest             | No       | Handles large language model (LLM) tasks                                                        |
| translation-gaudi-backend-server | opea/translation:latest             | No       | Serves as the backend for the Translation service, with variations depending on the deployment. |
| translation-gaudi-ui-server      | opea/translation-ui:latest          | No       | Provides the user interface for the Translation service.                                        |
| translation-gaudi-nginx-server   | opea/nginx:latest                   | No       | Acts as a reverse proxy, managing traffic between the UI and backend services.                  |
