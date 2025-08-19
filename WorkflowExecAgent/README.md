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

| **Deploy Method** | **Hardware** |
| ----------------- | ------------ |
| Docker Compose    | Intel Xeon   |

## Roadmap

Phase II: Agent memory integration to enable the capability to store tool intermediate results, such as a workflow instance key.
