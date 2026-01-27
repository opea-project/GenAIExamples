# Example BrowserUseAgent deployments on an Intel® Gaudi® Platform

This example covers the single-node on-premises deployment of the BrowserUseAgent example using OPEA components. This example begins with a Quick Start section and then documents how to modify deployments, leverage new models and configure the number of allocated devices.

**Note** This example requires access to a properly installed Intel® Gaudi® platform with a functional Docker service configured to use the habanalabs-container-runtime. Please consult the [Intel® Gaudi® software Installation Guide](https://docs.habana.ai/en/v1.20.1/Installation_Guide/Driver_Installation.html) for more information.

## Quick Start Deployment

This section describes how to quickly deploy and test the BrowserUseAgent service manually on an Intel® Gaudi® platform. The basic steps are:

1. [Access the Code](#access-the-code)
2. [Generate a HuggingFace Access Token](#generate-a-huggingface-access-token)
3. [Configure the Deployment Environment](#configure-the-deployment-environment)
4. [Deploy the Services Using Docker Compose](#deploy-the-services-using-docker-compose)
5. [Check the Deployment Status](#check-the-deployment-status)
6. [Test the Pipeline](#test-the-pipeline)
7. [Cleanup the Deployment](#cleanup-the-deployment)

### Access the Code

Clone the GenAIExample repository and access the BrowserUseAgent Intel® Gaudi® platform Docker Compose files and supporting scripts:

```bash
git clone https://github.com/opea-project/GenAIExamples.git
cd GenAIExamples/BrowserUseAgent/docker_compose/intel/hpu/gaudi/
```

Checkout a released version, such as v1.5:

```bash
git checkout v1.5
```

### Generate a HuggingFace Access Token

Some HuggingFace resources, such as some models, are only accessible if you have an access token. If you do not already have a HuggingFace access token, you can create one by first creating an account by following the steps provided at [HuggingFace](https://huggingface.co/) and then generating a [user access token](https://huggingface.co/docs/transformers.js/en/guides/private#step-1-generating-a-user-access-token).

### Configure the Deployment Environment

To set up environment variables for deploying BrowserUseAgent services, source the _setup_env.sh_ script in this directory:

```bash
source ./set_env.sh
```

The _set_env.sh_ script will prompt for required and optional environment variables used to configure the BrowserUseAgent services. If a value is not entered, the script will use a default value for the same. Users need to check if the values fit your deployment environment.

### Deploy the Services Using Docker Compose

To deploy the BrowserUseAgent services, execute the `docker compose up` command with the appropriate arguments. For a default deployment, execute:

```bash
docker compose up -d
```

The BrowserUseAgent docker images should automatically be downloaded from the `OPEA registry` and deployed on the Intel® Gaudi® Platform.

### Check the Deployment Status

After running docker compose, check if all the containers launched via docker compose have started:

```bash
docker ps -a
```

For the default deployment, the following 10 containers should have started:

```
CONTAINER ID   IMAGE                                                COMMAND                  CREATED         STATUS                            PORTS                                                                                                                                       NAMES
96cb590c749c   opea/browser-use-agent:latest                        "python browser_use_…"   9 seconds ago   Up 8 seconds                      0.0.0.0:8022->8022/tcp, :::8022->8022/tcp                                                                                                   browser-use-agent-server
8072e1c33a4b   opea/vllm-gaudi:1.22.0                               "python3 -m vllm.ent…"   9 seconds ago   Up 8 seconds (health: starting)   0.0.0.0:8008->80/tcp, [::]:8008->80/tcp                                                                                                     vllm-gaudi-server
```

### Test the Pipeline

If you don't have existing websites to test, follow the [guide](./../../../../tests/webarena/README.md) to deploy one in your local environment.

Once the BrowserUseAgent services are running, test the pipeline using the following command:

```bash
curl -X POST http://${host_ip}:${BROWSER_USE_AGENT_PORT}/v1/browser_use_agent \
    -H "Content-Type: application/json" \
    -d '{"task_prompt": "Navigate to http://10.7.4.57:8083/admin and login with the credentials: username: admin, password: admin1234. Then, find out What are the top-2 best-selling product in 2022?"}'
```

- Note that Update the `task_prompt` to match the evaluation question relevant to your configured website.

### Cleanup the Deployment

To stop the containers associated with the deployment, execute the following command:

```bash
docker compose -f compose.yaml down
```
