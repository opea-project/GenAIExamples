# Example Translation Deployment on AMD EPYC™ Platform

This document outlines the deployment process for a Translation service utilizing the [GenAIComps](https://github.com/opea-project/GenAIComps.git) microservice pipeline on AMD EPYC™ Processors. This example includes the following sections:

- [Translation Quick Start Deployment](#translation-quick-start-deployment): Demonstrates how to quickly deploy a Translation service/pipeline on AMD EPYC™ platform.
- [Translation Docker Compose Files](#translation-docker-compose-files): Describes some example deployments and their docker compose files.
- [Translation Service Configuration](#translation-service-configuration): Describes the service and possible configuration changes.

## Translation Quick Start Deployment

This section describes how to quickly deploy and test the Translation service manually on AMD EPYC™ platform. The basic steps are:

1. [Access the Code](#access-the-code)
2. [Install Docker](#install-docker)
3. [Determine your host's external IP address](#determine-your-host-external-ip-address)
4. [Generate a HuggingFace Access Token](#generate-a-huggingface-access-token)
5. [Configure the Deployment Environment](#configure-the-deployment-environment)
6. [Deploy the Service Using Docker Compose](#deploy-the-service-using-docker-compose)
7. [Check the Deployment Status](#check-the-deployment-status)
8. [Test the Pipeline](#test-the-pipeline)
9. [Cleanup the Deployment](#cleanup-the-deployment)

### Access the Code

Clone the GenAIExample repository and access the Translation AMD EPYC™ platform Docker Compose files and supporting scripts:

```
git clone https://github.com/opea-project/GenAIExamples.git
cd GenAIExamples/Translation/docker_compose/amd/cpu/epyc/
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
export HF_TOKEN="Your_HuggingFace_API_Token"
```

### Configure the Deployment Environment

To set up environment variables for deploying Translation service, source the set_env.sh script in this directory:

```
source set_env.sh
```

The set_env.sh script will prompt for required and optional environment variables used to configure the Translation service. If a value is not entered, the script will use a default value for the same. It will also generate a env file defining the desired configuration. Consult the section on [Translation Service configuration](#translation-service-configuration) for information on how service specific configuration parameters affect deployments.

### Deploy the Service Using Docker Compose

To deploy the Translation service, execute the `docker compose up` command with the appropriate arguments. For a default deployment, execute:

```bash
docker compose up -d
```

The Translation docker images should automatically be downloaded from the `OPEA registry` and deployed on the AMD EPYC™ Platform:

```
[+] Running 6/6
 ✔ Network epyc_default                       Created                                                                   0.1s
 ✔ Container tgi-service                      Healthy                                                                 328.1s
 ✔ Container llm-textgen-server               Started                                                                 323.5s
 ✔ Container translation-epyc-backend-server  Started                                                                 323.7s
 ✔ Container translation-epyc-ui-server       Started                                                                 324.0s
 ✔ Container translation-epyc-nginx-server    Started                                                                 324.2s
```

### Check the Deployment Status

After running docker compose, check if all the containers launched via docker compose have started:

```
docker ps -a
```

For the default deployment, the following 5 containers should be running:

```
CONTAINER ID   IMAGE                                                           COMMAND                  CREATED         STATUS                   PORTS                                       NAMES
89a39f7c917f   opea/nginx:latest                                               "/docker-entrypoint.…"   7 minutes ago   Up About a minute        0.0.0.0:80->80/tcp, :::80->80/tcp           translation-epyc-nginx-server
68b8b86a737e   opea/translation-ui:latest                                      "docker-entrypoint.s…"   7 minutes ago   Up About a minute        0.0.0.0:5173->5173/tcp, :::5173->5173/tcp   translation-epyc-ui-server
8400903275b5   opea/translation:latest                                         "python translation.…"   7 minutes ago   Up About a minute        0.0.0.0:8888->8888/tcp, :::8888->8888/tcp   translation-epyc-backend-server
2da5545cb18c   opea/llm-textgen:latest                                         "bash entrypoint.sh"     7 minutes ago   Up About a minute        0.0.0.0:9000->9000/tcp, :::9000->9000/tcp   llm-textgen-server
dee02c1fb538   ghcr.io/huggingface/text-generation-inference:2.4.0-intel-cpu   "text-generation-lau…"   7 minutes ago   Up 7 minutes (healthy)   0.0.0.0:8008->80/tcp, [::]:8008->80/tcp     tgi-service
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
 ✔ Container translation-epyc-nginx-server    Removed                                                            10.4s
 ✔ Container translation-epyc-ui-server       Removed                                                            10.3s
 ✔ Container translation-epyc-backend-server  Removed                                                            10.3s
 ✔ Container llm-textgen-server               Removed                                                            10.3s
 ✔ Container tgi-service                      Removed                                                             2.8s
 ✔ Network epyc_default                       Removed                                                             0.4s
```

All the Translation containers will be stopped and then removed on completion of the "down" command.

## Translation Docker Compose Files

The compose.yaml is default compose file using tgi as serving framework

| Service Name                    | Image Name                                                    |
| ------------------------------- | ------------------------------------------------------------- |
| tgi-service                     | ghcr.io/huggingface/text-generation-inference:2.4.0-intel-cpu |
| llm                             | opea/llm-textgen:latest                                       |
| translation-epyc-backend-server | opea/translation:latest                                       |
| translation-epyc-ui-server      | opea/translation-ui:latest                                    |
| translation-epyc-nginx-server   | opea/nginx:latest                                             |

## Translation Service Configuration

The table provides a comprehensive overview of the Translation service utilized across various deployments as illustrated in the example Docker Compose files. Each row in the table represents a distinct service, detailing its possible images used to enable it and a concise description of its function within the deployment architecture.

| Service Name                    | Possible Image Names                                          | Optional | Description                                                                                     |
| ------------------------------- | ------------------------------------------------------------- | -------- | ----------------------------------------------------------------------------------------------- |
| tgi-service                     | ghcr.io/huggingface/text-generation-inference:2.4.0-intel-cpu | No       | Specific to the TGI deployment, focuses on text generation inference.                           |
| llm                             | opea/llm-textgen:latest                                       | No       | Handles large language model (LLM) tasks                                                        |
| translation-epyc-backend-server | opea/translation:latest                                       | No       | Serves as the backend for the Translation service, with variations depending on the deployment. |
| translation-epyc-ui-server      | opea/translation-ui:latest                                    | No       | Provides the user interface for the Translation service.                                        |
| translation-epyc-nginx-server   | opea/nginx:latest                                             | No       | Acts as a reverse proxy, managing traffic between the UI and backend services.                  |

## Conclusion

This guide should enable developer to deploy the default configuration or any of the other compose yaml files for different configurations. It also highlights the configurable parameters that can be set before deployment.
