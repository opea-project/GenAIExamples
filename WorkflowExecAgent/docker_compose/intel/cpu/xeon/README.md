# Deploying WorkflowExecAgent on Intel® Xeon® Processors

This document outlines the single node deployment process for a Workflow Executor Agent application utilizing the [GenAIComps](https://github.com/opea-project/GenAIComps.git) microservices on an Intel Xeon server. The steps include building a Docker image, container deployment via Docker Compose, and service execution.

## Table of Contents

1. [WorkflowExecAgent Quick Start Deployment](#workflowexecagent-quick-start-deployment)
2. [Configuration Parameters](#configuration-parameters)
3. [Validate Microservices](#validate-microservices)
4. [Conclusion](#conclusion)

## WorkflowExecAgent Quick Start Deployment

This section describes how to quickly deploy and test the Workflow Executor Agent service on an Intel® Xeon® processor. The basic steps are:

1. [Access the Code](#access-the-code)
2. [Configure the Deployment Environment](#configure-the-deployment-environment)
3. [Deploy the Services Using Docker Compose](#deploy-the-services-using-docker-compose)
4. [Check the Deployment Status](#check-the-deployment-status)
5. [Validate the Pipeline](#validate-the-pipeline)
6. [Cleanup the Deployment](#cleanup-the-deployment)

### Access the Code

Clone the GenAIExamples repository and access the WorkflowExecAgent Docker Compose files and supporting scripts:

```bash
git clone https://github.com/opea-project/GenAIExamples.git
cd GenAIExamples/WorkflowExecAgent
```

### Configure the Deployment Environment

To set up environment variables for deploying the agent, navigate to the docker compose directory and configure the `.env` file with the following. Replace the variables according to your use case.

```bash
cd docker_compose/
# Edit the .env file with your specific configuration
```

**`.env` file content:**

```sh
export wf_api_port=5000     # workflow serving API port to use
export SDK_BASE_URL=http://$(hostname -I | awk '{print $1}'):${wf_api_port}/      # The workflow server will use this example workflow API url
export SERVING_TOKEN=${SERVING_TOKEN}           # Authentication token. For example_workflow test, can be empty as no authentication required.
export ip_address=$(hostname -I | awk '{print $1}')
export HF_TOKEN=${HF_TOKEN}
export llm_engine=${llm_engine}
export llm_endpoint_url=${llm_endpoint_url}
export WORKDIR=${WORKDIR}
export TOOLSET_PATH=$WORKDIR/GenAIExamples/WorkflowExecAgent/tools/
export http_proxy=${http_proxy}
export https_proxy=${https_proxy}

# LLM variables
export model="mistralai/Mistral-7B-Instruct-v0.3"
export recursion_limit=${recursion_limit}
export temperature=0
export max_new_tokens=1000
```

<details>
<summary> Using Remote LLM Endpoints </summary>
When models are deployed on a remote server, a base URL and an API key are required to access them. To set up a remote server and acquire the base URL and API key, refer to <a href="https://www.intel.com/content/www/us/en/developer/topic-technology/artificial-intelligence/enterprise-inference.html"> Intel® AI for Enterprise Inference </a> offerings.

Set the following environment variables.

- `llm_endpoint_url` is the HTTPS endpoint of the remote server with the model of choice (i.e. https://api.inference.denvrdata.com). **Note:** If not using LiteLLM, the second part of the model card needs to be appended to the URL i.e. `/Llama-3.3-70B-Instruct` from `meta-llama/Llama-3.3-70B-Instruct`.
- `llm_endpoint_api_key` is the access token or key to access the model(s) on the server.
- `LLM_MODEL_ID` is the model card which may need to be overwritten depending on what it is set to `set_env.sh`.

```bash
export llm_endpoint_url=<https-endpoint-of-remote-server>
export llm_endpoint_api_key=<your-api-key>
export LLM_MODEL_ID=<model-card>
```

</details>

### Deploy the Services Using Docker Compose

For an out-of-the-box experience, this guide uses an example workflow serving API service. There are 3 services needed for the setup: the agent microservice, an LLM inference service, and the workflow serving API.

First, build the agent docker image:

```bash
cd ../docker_image_build/
docker compose -f build.yaml build --no-cache
```

Next, launch the agent microservice. This assumes you have a running LLM service and its endpoint is configured in the `.env` file.

```bash
cd ../docker_compose
docker compose -f compose.yaml up -d
```

Finally, to launch the example workflow API server for testing, open a new terminal and run the following:

```bash
cd ../tests/example_workflow
. ./launch_workflow_service.sh
```

> **Note**: `launch_workflow_service.sh` will set up all the packages locally and launch a uvicorn server. For a containerized method, please refer to the `Dockerfile.example_workflow_api` file.

### Check the Deployment Status

After running docker compose, check if the container launched via docker compose has started:

```bash
docker ps -a
```

The following container should have started:

```
CONTAINER ID   IMAGE                              COMMAND                  CREATED          STATUS          PORTS                                     NAMES
b3e1388fa2ca   opea/gent:latest     "/bin/bash /start.sh"    1 minute ago     Up 1 minute     0.0.0.0:9090->9090/tcp                    workflowexec-agent-endpoint
```

Also, ensure the manually launched `uvicorn` workflow server and your external LLM service are running. If any issues are encountered, check the service logs.

### Validate the Pipeline

Once the services are running, test the pipeline using the following command. The agent microservice logs can be viewed to see the full execution trace.

View logs with:

```bash
docker logs workflowexec-agent-endpoint
```

Send a request to the agent:

```bash
# Set your workflow_id, which for the example is '12345'
export workflow_id=12345
export ip_address=$(hostname -I | awk '{print $1}')

curl http://${ip_address}:9090/v1/chat/completions -X POST -H "Content-Type: application/json" -d '{
     "query": "I have a data with gender Female, tenure 55, MonthlyAvgCharges 103.7. Predict if this entry will churn. My workflow id is '${workflow_id}'."
    }'
```

Update the `query` with the workflow parameters and workflow ID based on your workflow's context.

### Cleanup the Deployment

To stop the container associated with the deployment, execute the following command:

```bash
docker compose -f compose.yaml down
```

Remember to also stop the manually launched `uvicorn` server (Ctrl+C in its terminal).

## Configuration Parameters

Key parameters are configured via environment variables in the `.env` file before running `docker compose up`.

| Environment Variable       | Description                                                                                                               | Default (Set in `.env`)              |
| :------------------------- | :------------------------------------------------------------------------------------------------------------------------ | :----------------------------------- | ------------------ |
| `SDK_BASE_URL`             | **Required.** The URL to your platform's workflow serving API.                                                            | `http://<your-ip>:<wf_api_port>/`    |
| `SERVING_TOKEN`            | Authentication bearer token used for the SDK to authenticate with the workflow serving API. Can be empty for the example. | `""`                                 |
| `HF_TOKEN`                 | Your Hugging Face Hub token for model access (if needed by the LLM service).                                              | `your_huggingface_token`             |
| `llm_endpoint_url`         | **Required.** The full URL of the running LLM inference service endpoint.                                                 | `your_llm_endpoint`                  |
| `wf_api_port`              | The port to use for the example workflow serving API.                                                                     | `5000`                               |
| `ip_address`               | The host IP address, used to construct default URLs.                                                                      | `$(hostname -I                       | awk '{print $1}')` |
| `model`                    | The name of the LLM model to be used for agent reasoning.                                                                 | `mistralai/Mistral-7B-Instruct-v0.3` |
| `http_proxy`/`https_proxy` | Network proxy settings (if required).                                                                                     | `""`                                 |

## Validate Microservices

1.  **Agent Microservice**

    You can view the logs to ensure the service has started correctly.

    ```bash
    docker logs workflowexec-agent-endpoint
    ```

    You should be able to see "HTTP server setup successful" upon a successful startup. Then, validate with a `curl` command as shown in the [Validate the Pipeline](#validate-the-pipeline) section.

2.  **Example Workflow API Service**

    This service is launched manually with `launch_workflow_service.sh`. You can validate it by sending a direct request from its [test script](https://github.com/opea-project/GenAIExamples/blob/main/WorkflowExecAgent/tests/test_sdk.py) or by observing its logs in the terminal where it was launched.

3.  **LLM Inference Service**

    This service is external to the `compose.yaml`. You should validate it based on the documentation for that specific service (e.g., vLLM, TGI). A successful `curl` request to the agent, which results in a reasoned response, implicitly validates that the connection to the LLM service is working.

## Conclusion

This guide should enable a developer to deploy the Workflow Executor Agent and test it against the provided example workflow API. It also highlights the key configurable parameters that can be adapted for custom workflows and different LLM backends.
