# Workflow Executor Agent

## Quick Start: Key Configuration Variables

Before proceeding, here are some key configuration variables needed for the workflow executor agent.

- **SDK_BASE_URL**: The URL to your platform workflow serving API.

  Example: `http://<your-server-ip>:5000/`

  This is where the agent will send workflow execution requests.

- **SERVING_TOKEN**: The authentication bearer token which is used in the `RequestHandler` class as `api_key`. This is used for authenticating API requests. 3rd party platforms can design their serving workflow API this way for user authentication.

  More details can be found in the code [handle_requests.py](tools/utils/handle_requests.py#L23)

> **How to get these values:**
>
> - If you are using the provided example workflow API, refer to the test [README.md](tests/README.md)
> - For your own platform, refer to your API documentation or administrator for the correct values. If you are a platform provider you may refer to [Workflow Building Platform](#workflow-building-platform) section for prerequisites on setting up a serving workflow.

For more info on using these variables, refer to the [Microservice Setup](#microservice-setup) section below on using the [Example Workflow API](tests/example_workflow/) for a working example.

Set these variables in your environment before starting the service.

## Overview

GenAI Workflow Executor Example showcases the capability to handle data/AI workflow operations via LangChain agents to execute custom-defined workflow-based tools. These workflow tools can be interfaced from any 3rd-party tools in the market (no-code/low-code/IDE) such as Alteryx, RapidMiner, Power BI, Intel Data Insight Automation which allows users to create complex data/AI workflow operations for different use-cases.

### Definitions

Before we begin, here are the definitions to some terms for clarity:

- servable/serving workflow - A workflow made ready to be executed through API. It should be able to accept parameter injection for workflow scheduling and have a way to retrieve the final output data. It should also have a unique workflow ID for referencing. For platform providers guide to create their own servable workflows compatible with this example, refer to [Workflow Building Platform](#workflow-building-platform)

- SDK Class - Performs requests to interface with a 3rd-party API to perform workflow operations on the servable workflow. Found in `tools/sdk.py`.

- workflow ID - A unique ID for the servable workflow.

- workflow instance - An instance created from the servable workflow. It is represented as a `Workflow` class created using `DataInsightAutomationSDK.create_workflow()` under `tools/sdk.py`. Contains methods to `start`, `get_status` and `get_results` from the workflow.

### Workflow Executor

Strategy - This example demonstrates a single React-LangGraph with a `Workflow Executor` tool to ingest a user prompt to execute workflows and return an agent reasoning response based on the workflow output data.

First the LLM extracts the relevant information from the user query based on the schema of the tool in `tools/tools.yaml`. Then the agent sends this `AgentState` to the `Workflow Executor` tool.

`Workflow Executor` tool requires a SDK class to call the servable workflow API. In the code, `DataInsightAutomationSDK` is the example class as seen under `tools/sdk.py` to interface with several high-level API's. There are 3 steps to this tool implementation:

1. Starts the workflow with workflow parameters and workflow id extracted from the user query.

2. Periodically checks the workflow status for completion or failure. This may be through a database which stores the current status of the workflow

3. Retrieves the output data from the workflow through a storage service.

The `AgentState` is sent back to the LLM for reasoning. Based on the output data, the LLM generates a response to answer the user's input prompt.

Below shows an illustration of this flow:

![image](https://github.com/user-attachments/assets/cb135042-1505-4aef-8822-c78c2f72aa2a)

### Workflow Serving for Agent

#### Workflow Building Platform

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

#### Using Servable Workflow

Once we have our servable workflow ready, the serving workflow API can be prepared to accept requests from the SDK class. Refer to [Start Agent Microservice](#start-agent-microservice) on how to do this.

To start prompting the agent microservice, we will use the following command for this churn prediction use-case:

```sh
curl http://${ip_address}:9090/v1/chat/completions -X POST -H "Content-Type: application/json" -d '{
     "query": "I have a data with gender Female, tenure 55, MonthlyAvgCharges 103.7. Predict if this entry will churn. My workflow id is '${workflow_id}'."
    }'
```

The user has to provide a `workflow_id` and workflow `params` in the query. Notice that the `query` string includes all the workflow `params` which the user has defined in the workflow. The LLM will extract these parameters into a dictionary format for the workflow `Serving Parameters` as shown below:

```python
params = {"gender": "Female", "tenure": 55, "MonthlyAvgCharges": 103.7}
```

These parameters will be passed into the `Workflow Executor` tool to start the workflow execution of specified `workflow_id`. Thus, everything will be handled via the microservice.

And finally here are the results from the microservice logs:

![image](https://github.com/user-attachments/assets/969fefb7-543d-427f-a56c-dc70e474ae60)

## Microservice Setup

### Start Agent Microservice

For an out-of-box experience there is an example workflow serving API service prepared for users under [Example Workflow API](tests/example_workflow/) to interface with the SDK. This section will guide users on setting up this service as well. Users may modify the logic, add your own database etc for your own use-case.

There are 3 services needed for the setup:

1. Agent microservice

2. LLM inference service - specified as `llm_endpoint_url`.

3. workflow serving API service - specified as `SDK_BASE_URL`

Workflow Executor will have a single docker image. First, build the agent docker image.

```sh
git clone https://github.com/opea-project/GenAIExamples.git
cd GenAIExamples//WorkflowExecAgent/docker_image_build/
docker compose -f build.yaml build --no-cache
```

Configure `GenAIExamples/WorkflowExecAgent/docker_compose/.env` file with the following. Replace the variables according to your usecase.

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

Launch service by running the docker compose command.

```sh
cd $WORKDIR/GenAIExamples/WorkflowExecAgent/docker_compose
docker compose -f compose.yaml up -d
```

To launch the example workflow API server, open a new terminal and run the following:

```sh
cd $WORKDIR/GenAIExamples/WorkflowExecAgent/tests/example_workflow
. launch_workflow_service.sh
```

`launch_workflow_service.sh` will setup all the packages locally and launch the uvicorn server to host the API on port 5000. For a Dockerfile method, please refer to `Dockerfile.example_workflow_api` file.

### Validate service

The agent microservice logs can be viewed using:

```sh
docker logs workflowexec-agent-endpoint
```

You should be able to see "HTTP server setup successful" upon successful startup.

You can validate the service using the following command:

```sh
curl http://${ip_address}:9090/v1/chat/completions -X POST -H "Content-Type: application/json" -d '{
     "query": "I have a data with gender Female, tenure 55, MonthlyCharges 103.7, TotalCharges 1840.75. Predict if this entry will churn. My workflow id is '${workflow_id}'."
    }'
```

Update the `query` with the workflow parameters, workflow id, etc based on the workflow context.

## Roadmap

Phase II: Agent memory integration to enable capability to store tool intermediate results, such as workflow instance key.

## Validated Configurations

| **Deploy Method** | **Hardware** |
| ----------------- | ------------ |
| Docker Compose    | Intel Xeon   |
