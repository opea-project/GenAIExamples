# Workflow Executor Agent

## Table of Contents

1. [Overview](#overview)
2. [Deployment Options](#deployment-options)
3. [Roadmap](#roadmap)

## Overview

GenAI Workflow Executor Example showcases the capability to handle data/AI workflow operations via LangChain agents to execute custom-defined workflow-based tools. These workflow tools can be interfaced from any 3rd-party tools in the market (no-code/low-code/IDE) such as Alteryx, RapidMiner, Power BI, and Intel Data Insight Automation, which allows users to create complex data/AI workflow operations for different use-cases.

### Definitions

Before we begin, here are the definitions for some terms for clarity:

- **Servable/Serving Workflow**: A workflow made ready to be executed through an API. It should be able to accept parameter injection for workflow scheduling and have a way to retrieve the final output data. It should also have a unique workflow ID for referencing.
- **SDK Class**: Performs requests to interface with a 3rd-party API to perform workflow operations on the servable workflow. Found in `tools/sdk.py`.
- **Workflow ID**: A unique ID for the servable workflow.
- **Workflow Instance**: An instance created from the servable workflow. It is represented as a `Workflow` class created using `DataInsightAutomationSDK.create_workflow()` under `tools/sdk.py`. It contains methods to `start`, `get_status`, and `get_results` from the workflow.

### Workflow Executor Strategy

This example demonstrates a single ReAct-LangGraph with a `Workflow Executor` tool to ingest a user prompt, execute workflows, and return an agent-reasoned response based on the workflow output data.

First, the LLM extracts the relevant information from the user query based on the schema of the tool in `tools/tools.yaml`. Then the agent sends this `AgentState` to the `Workflow Executor` tool.

The `Workflow Executor` tool requires an SDK class to call the servable workflow API. In the code, `DataInsightAutomationSDK` is the example class (as seen under `tools/sdk.py`) to interface with several high-level APIs. There are 3 steps to this tool implementation:

1.  Starts the workflow with workflow parameters and a workflow ID extracted from the user query.
2.  Periodically checks the workflow status for completion or failure. This may be through a database which stores the current status of the workflow.
3.  Retrieves the output data from the workflow through a storage service.

The `AgentState` is sent back to the LLM for reasoning. Based on the output data, the LLM generates a response to answer the user's input prompt.

Below is an illustration of this flow:

![image](https://github.com/user-attachments/assets/cb135042-1505-4aef-8822-c78c2f72aa2a)

### Workflow Serving for Agent

The first step is to prepare a servable workflow using a platform with the capabilities to do so.

As an example, here we have a Churn Prediction use-case workflow as the serving workflow for the agent execution. It is created through Intel Data Insight Automation platform. The image below shows a snapshot of the Churn Prediction workflow.

![image](https://github.com/user-attachments/assets/c067f8b3-86cf-4abc-a8bd-51a98de8172d)

The workflow contains 2 paths which can be seen in the workflow illustrated, the top and bottom paths.

1. Top path (Training path) - Ends at the random forest classifier node is the training path. The data is cleaned through a series of nodes and used to train a random forest model for prediction.

2. Bottom path (Inference path) - where trained random forest model is used for inferencing based on input parameter.

For this agent workflow execution, the inferencing path is executed to yield the final output result of the `Model Predictor` node. The same output is returned to the `Workflow Executor` tool through the `Langchain API Serving` node.

There are `Serving Parameters` in the workflow, which are the tool input variables used to start a workflow instance at runtime obtained from `params` the LLM extracts from the user query. Below shows the parameter configuration option for the Intel Data Insight Automation workflow UI.

<img src="https://github.com/user-attachments/assets/ce8ef01a-56ff-4278-b84d-b6e4592b28c6" alt="image" width="500"/>

Manually running the workflow yields the tabular data output as shown below:

![image](https://github.com/user-attachments/assets/241c1aba-2a24-48da-8005-ec7bfe657179)

In the workflow serving for agent, this output will be returned to the `Workflow Executor` tool. The LLM can then answer the user's original question based on this output.

When the workflow is configured as desired, transform this into a servable workflow. We turn this workflow into a servable workflow format so that it can be called through API to perform operations on it. Data Insight Automation has tools to do this for its own workflows.

> [!NOTE]
> Remember to create a unique workflow ID along with the servable workflow.

## Deployment Options

The table below lists currently available deployment options. They outline in detail the implementation of this example on selected hardware.

| Category               | Deployment Option | Description                                                                       |
| ---------------------- | ----------------- | --------------------------------------------------------------------------------- |
| On-premise Deployments | Docker compose    | [WorkflowExecAgent deployment on Xeon](./docker_compose/intel/cpu/xeon/README.md) |
|                        | Kubernetes        | Work-in-progress                                                                  |

## Validated Configurations

<<<<<<< HEAD
| **Deploy Method** | **Hardware** |
| ----------------- | ------------ |
| Docker Compose    | Intel Xeon   |
=======
![image](https://github.com/user-attachments/assets/969fefb7-543d-427f-a56c-dc70e474ae60)

## Microservice Setup

### Start Agent Microservice

Workflow Executor will have a single docker image.

(Optional) Build the agent docker image with the most latest changes.  
By default, Workflow Executor uses public [opea/vllm](https://hub.docker.com/r/opea/agent) docker image if no local built image exists.

```sh
export WORKDIR=$PWD
git clone https://github.com/opea-project/GenAIComps.git
cd GenAIExamples//WorkflowExecAgent/docker_image_build/
git clone https://github.com/opea-project/GenAIExamples.git
docker compose -f build.yaml build --no-cache
```

<details>
<summary> Using Remote LLM Endpoints </summary>
When models are deployed on a remote server, a base URL and an API key are required to access them. To set up a remote server and acquire the base URL and API key, refer to <a href="https://www.intel.com/content/www/us/en/products/docs/accelerator-engines/enterprise-ai.html"> Intel® AI for Enterprise Inference </a> offerings.

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

Configure `GenAIExamples/WorkflowExecAgent/docker_compose/.env` file with the following. Replace the variables according to your usecase.

```sh
export SDK_BASE_URL=${SDK_BASE_URL}
export SERVING_TOKEN=${SERVING_TOKEN}
export HF_TOKEN=${HF_TOKEN}
export llm_engine=vllm
export llm_endpoint_url=${llm_endpoint_url}
export api_key=${llm_endpoint_api_key:-""}
export ip_address=$(hostname -I | awk '{print $1}')
export model=${LLM_MODEL_ID:-"mistralai/Mistral-7B-Instruct-v0.3"}
export recursion_limit=${recursion_limit}
export temperature=0
export max_new_tokens=1000
export WORKDIR=${WORKDIR}
export TOOLSET_PATH=$WORKDIR/GenAIExamples/WorkflowExecAgent/tools/
export http_proxy=${http_proxy}
export https_proxy=${https_proxy}
```

> Note: SDK_BASE_URL and SERVING_TOKEN can be obtained from Intel Data Insight Automation platform.  
> For llm_endpoint_url, both local vllm service or an remote vllm endpoint work for the example.

Launch service by running the docker compose command.

```sh
cd $WORKDIR/GenAIExamples/WorkflowExecAgent/docker_compose
docker compose -f compose.yaml up -d
```

### Validate service

The microservice logs can be viewed using:

```sh
docker logs workflowexec-agent-endpoint
```

You should be able to see "HTTP server setup successful" upon successful startup.

You can validate the service using the following command:

```sh
curl http://${ip_address}:9090/v1/chat/completions -X POST -H "Content-Type: application/json" -d '{
     "query": "I have a data with gender Female, tenure 55, MonthlyAvgCharges 103.7. Predict if this entry will churn. My workflow id is '${workflow_id}'."
    }'
```

Update the `query` with the workflow parameters, workflow id, etc based on the workflow context.
>>>>>>> 5b864ae7 (Enable Remote Endpoints for LLM using Intel Enterprise Inference)

## Roadmap

Phase II: Agent memory integration to enable the capability to store tool intermediate results, such as a workflow instance key.
