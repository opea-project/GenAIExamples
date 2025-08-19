# Deploying AgentQnA on Intel® Gaudi® Processors

This document outlines the single node deployment process for a AgentQnA application utilizing the [GenAIComps](https://github.com/opea-project/GenAIComps.git) microservices on Intel Gaudi® server. The steps include pulling Docker images, container deployment via Docker Compose, and service execution using microservices `agent`.

## Table of Contents

1. [AgentQnA Quick Start Deployment](#agentqna-quick-start-deployment)
2. [Configuration Parameters](#configuration-parameters)
3. [AgentQnA Docker Compose Files](#agentqna-docker-compose-files)
4. [Validate Services](#validate-services)
5. [Interact with the agent system with UI](#interact-with-the-agent-system-with-ui)
6. [Register other tools with the AI agent](#register-other-tools-with-the-ai-agent)
7. [Conclusion](#conclusion)

## AgentQnA Quick Start Deployment

This section describes how to quickly deploy and test the AgentQnA service manually on an Intel® Gaudi® processor. The basic steps are:

1. [Access the Code](#access-the-code)
2. [Configure the Deployment Environment](#configure-the-deployment-environment)
3. [Deploy the Services Using Docker Compose](#deploy-the-services-using-docker-compose)
4. [Ingest Data into the Vector Database](#ingest-data-into-the-vector-database)
5. [Cleanup the Deployment](#cleanup-the-deployment)

### Access the Code

Clone the GenAIExample repository and access the AgentQnA Intel® Gaudi® platform Docker Compose files and supporting scripts:

```bash
export WORKDIR=<your-work-directory>
cd $WORKDIR
git clone https://github.com/opea-project/GenAIExamples.git
cd GenAIExamples/AgentQnA
```

To checkout a released version, such as v1.4:

```bash
git checkout v1.4
```

### Configure the Deployment Environment

To set up environment variables for deploying AgentQnA services, set up some parameters specific to the deployment environment and source the `set_env.sh` script in this directory:

```bash
export host_ip="External_Public_IP"           # ip address of the node
export HF_TOKEN="Your_HuggingFace_API_Token"  # the huggingface API token you applied
export http_proxy="Your_HTTP_Proxy"           # http proxy if any
export https_proxy="Your_HTTPs_Proxy"         # https proxy if any
export no_proxy=localhost,127.0.0.1,$host_ip  # additional no proxies if needed
```

#### [Optional] OPENAI_API_KEY to use OpenAI models or Intel® AI for Enterprise Inference

To use OpenAI models, generate a key following these [instructions](https://platform.openai.com/api-keys).

To use a remote server running Intel® AI for Enterprise Inference, contact the cloud service provider or owner of the on-prem machine for a key to access the desired model on the server.

Then set the environment variable `OPENAI_API_KEY` with the key contents:

```bash
export OPENAI_API_KEY=<your-openai-key>
```

#### Then, set up environment variables for the selected hardware using the corresponding `set_env.sh`

```bash
source $WORKDIR/GenAIExamples/AgentQnA/docker_compose/intel/hpu/gaudi/set_env.sh
```

### Deploy the Services Using Docker Compose

We make it convenient to launch the whole system with docker compose, which includes microservices for LLM, agents, UI, retrieval tool, vector database, dataprep, and telemetry. There are 3 docker compose files, which make it easy for users to pick and choose. Users can choose a different retrieval tool other than the `DocIndexRetriever` example provided in our GenAIExamples repo. Users can choose not to launch the telemetry containers.

On Gaudi, `meta-llama/Meta-Llama-3.3-70B-Instruct` will be served using vllm. The command below will launch the multi-agent system with the `DocIndexRetriever` as the retrieval tool for the Worker RAG agent.

```bash
cd $WORKDIR/GenAIExamples/AgentQnA/docker_compose/intel/hpu/gaudi/
docker compose -f $WORKDIR/GenAIExamples/DocIndexRetriever/docker_compose/intel/cpu/xeon/compose.yaml -f compose.yaml up -d
```

> **Note**: To enable the web search tool, skip this step and proceed to the "[Optional] Web Search Tool Support" section.

To enable Open Telemetry Tracing, compose.telemetry.yaml file need to be merged along with default compose.yaml file.
Gaudi example with Open Telemetry feature:

```bash
cd $WORKDIR/GenAIExamples/AgentQnA/docker_compose/intel/hpu/gaudi/
docker compose -f $WORKDIR/GenAIExamples/DocIndexRetriever/docker_compose/intel/cpu/xeon/compose.yaml -f compose.yaml -f compose.telemetry.yaml up -d
```

#### [Optional] Web Search Tool Support

<details>
<summary> Instructions </summary>
A web search tool is supported in this example and can be enabled by running docker compose with the `compose.webtool.yaml` file.
The Google Search API is used. Follow the [instructions](https://python.langchain.com/docs/integrations/tools/google_search) to create an API key and enable the Custom Search API on a Google account. The environment variables `GOOGLE_CSE_ID` and `GOOGLE_API_KEY` need to be set.

```bash
cd $WORKDIR/GenAIExamples/AgentQnA/docker_compose/intel/hpu/gaudi/
export GOOGLE_CSE_ID="YOUR_ID"
export GOOGLE_API_KEY="YOUR_API_KEY"
docker compose -f $WORKDIR/GenAIExamples/DocIndexRetriever/docker_compose/intel/cpu/xeon/compose.yaml -f compose.yaml -f compose.webtool.yaml up -d
```

</details>

#### Build image from source

Please refer to the table below to build different microservices from source:

| Microservice | Deployment Guide                                                                                                                                 |
| ------------ | ------------------------------------------------------------------------------------------------------------------------------------------------ |
| Agent        | [Agent build guide](https://github.com/opea-project/GenAIComps/blob/main/comps/agent/src/README.md#21-build-docker-image-for-agent-microservice) |
| UI           | [Basic UI build guide](../../../../README_miscellaneous.md#build-ui-docker-image)                                                                |

### Ingest Data into the Vector Database

The `run_ingest_data.sh` script will use an example jsonl file to ingest example documents into a vector database. Other ways to ingest data and other types of documents supported can be found in the OPEA dataprep microservice located in the opea-project/GenAIComps repo.

```bash
cd  $WORKDIR/GenAIExamples/AgentQnA/retrieval_tool/
bash run_ingest_data.sh
```

> **Note**: This is a one-time operation.

### Cleanup the Deployment

To stop the containers associated with the deployment, execute the following command:

```bash
# for OpenAI Models
docker compose -f compose_openai.yaml down
# for Models on Remote Server
docker compose -f compose_remote.yaml down
```

## Configuration Parameters

Key parameters are configured via environment variables set before running `docker compose up`.

| Environment Variable                    | Description                                                                               | Default (Set Externally)                        |
| :-------------------------------------- | :---------------------------------------------------------------------------------------- | :---------------------------------------------- |
| `ip_address`                            | External IP address of the host machine. **Required.**                                    | `your_external_ip_address`                      |
| `OPENAI_API_KEY`                        | Your OpenAI API key for model access. **Required.**                                       | `your_openai_api_key`                           |
| `model`                                 | Hugging Face model ID for the AgentQnA LLM. Configured within `compose.yaml` environment. | `gpt-4o-mini-2024-07-18`                        |
| `TOOLSET_PATH`                          | Local path to the tool Yaml file. Configured in `compose.yaml`.                           | `$WORKDIR/GenAIExamples/AgentQnA/tools/`        |
| `CRAG_SERVER`                           | CRAG server URL. Derived from `ip_address` and port `8080`.                               | `http://${ip_address}:8080`                     |
| `WORKER_AGENT_URL`                      | Worker agent URL. Derived from `ip_address` and port `9095`.                              | `http://${ip_address}:9095/v1/chat/completions` |
| `SQL_AGENT_URL`                         | SQL agent URL. Derived from `ip_address` and port `9096`.                                 | `http://${ip_address}:9096/v1/chat/completions` |
| `http_proxy` / `https_proxy`/`no_proxy` | Network proxy settings (if required).                                                     | `""`                                            |

## AgentQnA Docker Compose Files

In the context of deploying a AgentQnA pipeline on an Intel® Gaudi® platform, we can pick and choose different large language model serving frameworks. The table below outlines the various configurations that are available as part of the application. These configurations can be used as templates and can be extended to different components available in [GenAIComps](https://github.com/opea-project/GenAIComps.git).

| File                                               | Description                                                         |
| -------------------------------------------------- | ------------------------------------------------------------------- |
| [compose.yaml](./compose.yaml)                     | Default compose file using vLLM as the serving framework            |
| [compose.webtool.yaml](./compose.webtool.yaml)     | This compose file is used to start a supervisor agent with webtools |
| [compose.telemetry.yaml](./compose.telemetry.yaml) | This compose file is used to enable telemetry related services      |

## Validate Services

1. First look at logs for each of the agent docker containers:

```bash
# worker RAG agent
docker logs rag-agent-endpoint

# worker SQL agent
docker logs sql-agent-endpoint

# supervisor agent
docker logs react-agent-endpoint
```

Look for the message "HTTP server setup successful" to confirm the agent docker container has started successfully.</p>

2. Use python to validate each agent is working properly:

```bash
# RAG worker agent
python $WORKDIR/GenAIExamples/AgentQnA/tests/test.py --prompt "Tell me about Michael Jackson song Thriller" --agent_role "worker" --ext_port 9095

# SQL agent
python $WORKDIR/GenAIExamples/AgentQnA/tests/test.py --prompt "How many employees in company" --agent_role "worker" --ext_port 9096

# supervisor agent: this will test a two-turn conversation
python $WORKDIR/GenAIExamples/AgentQnA/tests/test.py --agent_role "supervisor" --ext_port 9090
```

## Interact with the agent system with UI

The UI microservice is launched in the previous step with the other microservices.
To see the UI, open a web browser to `http://${ip_address}:5173` to access the UI. Note the `ip_address` here is the host IP of the UI microservice.

1. Click on the arrow above `Get started`. Create an admin account with a name, email, and password.
2. Add an OpenAI-compatible API endpoint. In the upper right, click on the circle button with the user's initial, go to `Admin Settings`->`Connections`. Under `Manage OpenAI API Connections`, click on the `+` to add a connection. Fill in these fields:

- **URL**: `http://${ip_address}:9090/v1`, do not forget the `v1`
- **Key**: any value
- **Model IDs**: any name i.e. `opea-agent`, then press `+` to add it

Click "Save".

![opea-agent-setting](../../../../assets/img/opea-agent-setting.png)

3. Test OPEA agent with UI. Return to `New Chat` and ensure the model (i.e. `opea-agent`) is selected near the upper left. Enter in any prompt to interact with the agent.

![opea-agent-test](../../../../assets/img/opea-agent-test.png)

## Register other tools with the AI agent

The [tools](../../../../tools) folder contains YAML and Python files for additional tools for the supervisor and worker agents. Refer to the "Provide your own tools" section in the instructions [here](https://github.com/opea-project/GenAIComps/tree/main/comps/agent/src/README.md) to add tools and customize the AI agents.

## Conclusion

This guide provides a comprehensive workflow for deploying, configuring, and validating the AgentQnA system on Intel® Gaudi® processors, enabling flexible integration with both OpenAI-compatible and remote LLM services.
