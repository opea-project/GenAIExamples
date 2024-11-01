# Workflow Executor Agent

## Overview

GenAI Workflow Executor Example showcases the capability to handle data/AI workflow operations via LangChain agents to execute custom-defined workflow-based tools. These workflow tools can be interfaced from any 3rd-party tools in the market (no-code/low-code/IDE) such as Alteryx, RapidMiner, Power BI, Intel Data Insight Automation which allows users to create complex data/AI workflow operations for different use-cases.

### Workflow Executor

This example demonstrates a single React-LangGraph with a `Workflow Executor` tool to ingest a user prompt to execute workflows and return an agent reasoning response based on the workflow output data.

First the LLM extracts the relevant information from the user query based on the schema of the tool in `tools/tools.yaml`. Then the agent sends this `AgentState` to the `Workflow Executor` tool.

`Workflow Executor` tool uses `EasyDataSDK` class as seen under `tools/sdk.py` to interface with several high-level API's. There are 3 steps to this tool implementation:

1. Starts the workflow with workflow parameters and workflow id extracted from the user query.

2. Periodically checks the workflow status for completion or failure. This may be through a database which stores the current status of the workflow

3. Retrieves the output data from the workflow through a storage service.

The `AgentState` is sent back to the LLM for reasoning. Based on the output data, the LLM generates a response to answer the user's input prompt.

Below shows an illustration of this flow:

![image](https://github.com/user-attachments/assets/cb135042-1505-4aef-8822-c78c2f72aa2a)

### Workflow Serving for Agent

As an example, here we have a Churn Prediction use-case workflow as the serving workflow for the agent execution. It is created through Intel Data Insight Automation platform. The image below shows a snapshot of the Churn Prediction workflow.

![image](https://github.com/user-attachments/assets/c067f8b3-86cf-4abc-a8bd-51a98de8172d)

The workflow contains 2 paths which can be seen in the workflow illustrated, the top path and bottom path.

1. Top path - The training path which ends at the random forest classifier node is the training path. The data is cleaned through a series of nodes and used to train a random forest model for prediction.

2. Bottom path - The inference path where trained random forest model is used for inferencing based on input parameter.

For this agent workflow execution, the inferencing path is executed to yield the final output result of the `Model Predictor` node. The same output is returned to the `Workflow Executor` tool through the `Langchain API Serving` node.

There are `Serving Parameters` in the workflow, which are the tool input variables used to start a workflow instance obtained from `params` the LLM extracts from the user query. Below shows the parameter configuration option for the Intel Data Insight Automation workflow UI.

![image](https://github.com/user-attachments/assets/ce8ef01a-56ff-4278-b84d-b6e4592b28c6)

Manually running the workflow yields the tabular data output as shown below:

![image](https://github.com/user-attachments/assets/241c1aba-2a24-48da-8005-ec7bfe657179)

In the workflow serving for agent, this output will be returned to the `Workflow Executor` tool. The LLM can then answer the user's original question based on this output.

To start prompting the agent microservice, we will use the following command for this use case:

```sh
curl http://${ip_address}:9090/v1/chat/completions -X POST -H "Content-Type: application/json" -d '{
     "query": "I have a data with gender Female, tenure 55, MonthlyAvgCharges 103.7. Predict if this entry will churn. My workflow id is '${workflow_id}'."
    }'
```

The user has to provide a `workflow_id` and workflow `params` in the query. `workflow_id` a unique id used for serving the workflow to the microservice. Notice that the `query` string includes all the workflow `params` which the user has defined in the workflow. The LLM will extract these parameters into a dictionary format for the workflow `Serving Parameters` as shown below:

```python
params = {"gender": "Female", "tenure": 55, "MonthlyAvgCharges": 103.7}
```

These parameters will be passed into the `Workflow Executor` tool to start the workflow execution of specified `workflow_id`. Thus, everything will be handled via the microservice.

And finally here are the results from the microservice logs:

![image](https://github.com/user-attachments/assets/969fefb7-543d-427f-a56c-dc70e474ae60)

## Microservice Setup

### Start Agent Microservice

Workflow Executor will have a single docker image. First, build the agent docker image.

```sh
git clone https://github.com/opea-project/GenAIExamples.git
cd GenAIExamples//WorkflowExecAgent/docker_image_build/
docker compose -f build.yaml build --no-cache
```

Configure `GenAIExamples/WorkflowExecAgent/docker_compose/.env` file with the following. Replace the variables according to your usecase.

```sh
export SDK_BASE_URL=${SDK_BASE_URL}
export SERVING_TOKEN=${SERVING_TOKEN}
export HUGGINGFACEHUB_API_TOKEN=${HF_TOKEN}
export llm_engine=${llm_engine}
export llm_endpoint_url=${llm_endpoint_url}
export ip_address=$(hostname -I | awk '{print $1}')
export model="mistralai/Mistral-7B-Instruct-v0.3"
export recursion_limit=${recursion_limit}
export temperature=0
export max_new_tokens=1000
export WORKDIR=${WORKDIR}
export TOOLSET_PATH=$WORKDIR/GenAIExamples/WorkflowExecAgent/tools/
export http_proxy=${http_proxy}
export https_proxy=${https_proxy}
```

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

## Roadmap

Phase II: Agent memory integration to enable capability to store tool intermediate results, such as workflow instance key.
