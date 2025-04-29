# Example Finance Agent deployments on AMD GPU (ROCm)

This document outlines the deployment process for a Finance Agent application utilizing OPEA components on an AMD GPU server.

This example includes the following sections:

- [Finance Agent Quick Start Deployment](#finance-agent-quick-start-deployment): Demonstrates how to quickly deploy a Finance Agent application/pipeline on AMD GPU platform.
- [Finance Agent Docker Compose Files](#finance-agent-docker-compose-files): Describes some example deployments and their docker compose files.
- [How to interact with the agent system with UI](#how-to-interact-with-the-agent-system-with-ui): Guideline for UI usage

## Finance Agent Quick Start Deployment

This section describes how to quickly deploy and test the Finance Agent service manually on an AMD GPU platform. The basic steps are:

1. [Access the Code](#access-the-code)
2. [Generate a HuggingFace Access Token](#generate-a-huggingface-access-token)
3. [Deploy the Services Using Docker Compose](#deploy-the-services-using-docker-compose)
4. [Check the Deployment Status](#check-the-deployment-status)
5. [Test the Pipeline](#test-the-pipeline)
6. [Cleanup the Deployment](#cleanup-the-deployment)

### Access the Code

Clone the GenAIExample repository and access the ChatQnA AMD GPU platform Docker Compose files and supporting scripts:

```
mkdir /path/to/your/workspace/
export WORKDIR=/path/to/your/workspace/
cd $WORKDIR
git clone https://github.com/opea-project/GenAIExamples.git
```

Checkout a released version, such as v1.4:

```
git checkout v1.4
```

### Generate a HuggingFace Access Token

Some HuggingFace resources, such as some models, are only accessible if you have an access token. If you do not already have a HuggingFace access token, you can create one by first creating an account by following the steps provided at [HuggingFace](https://huggingface.co/) and then generating a [user access token](https://huggingface.co/docs/transformers.js/en/guides/private#step-1-generating-a-user-access-token).

### Deploy the Services Using Docker Compose

#### 3.1 Launch vllm endpoint

Below is the command to launch a vllm endpoint on Gaudi that serves `meta-llama/Llama-3.3-70B-Instruct` model on AMD ROCm platform.

```bash
cd $WORKDIR/GenAIExamples/FinanceAgent/docker_compose/amd/gpu/rocm
bash launch_vllm.sh
```

#### 3.2 Prepare knowledge base

The commands below will upload some example files into the knowledge base. You can also upload files through UI.

First, launch the redis databases and the dataprep microservice.

```bash
# inside $WORKDIR/GenAIExamples/FinanceAgent/docker_compose/amd/gpu/rocm
bash launch_dataprep.sh
```

Validate datat ingest data and retrieval from database:

```bash
python $WORKPATH/tests/test_redis_finance.py --port 6007 --test_option ingest
python $WORKPATH/tests/test_redis_finance.py --port 6007 --test_option get
```

#### 3.3 Launch the multi-agent system

The command below will launch 3 agent microservices, 1 docsum microservice, 1 UI microservice.

```bash
# inside $WORKDIR/GenAIExamples/FinanceAgent/docker_compose/amd/gpu/rocm
bash launch_agents.sh
```

#### 3.4 Check the Deployment Status

After running docker compose, check if all the containers launched via docker compose have started:

```
docker ps -a
```

For the default deployment, the following 5 containers should have started:

```
CONTAINER ID   IMAGE                                                   COMMAND                  CREATED          STATUS                 PORTS                                                                                      NAMES
7e61978c3d75   opea/dataprep:latest                                    "sh -c 'python $( [ …"   31 seconds ago   Up 19 seconds          0.0.0.0:6007->5000/tcp, [::]:6007->5000/tcp                                                dataprep-redis-server-finance
0fee87aca791   redis/redis-stack:7.2.0-v9                              "/entrypoint.sh"         3 hours ago      Up 3 hours (healthy)   0.0.0.0:6380->6379/tcp, [::]:6380->6379/tcp, 0.0.0.0:8002->8001/tcp, [::]:8002->8001/tcp   redis-kv-store
debd549045f8   redis/redis-stack:7.2.0-v9                              "/entrypoint.sh"         3 hours ago      Up 3 hours (healthy)   0.0.0.0:6379->6379/tcp, :::6379->6379/tcp, 0.0.0.0:8001->8001/tcp, :::8001->8001/tcp       redis-vector-db
9cff469364d3   ghcr.io/huggingface/text-embeddings-inference:cpu-1.5   "/bin/sh -c 'apt-get…"   3 hours ago      Up 3 hours (healthy)   0.0.0.0:10221->80/tcp, [::]:10221->80/tcp                                                  tei-embedding-serving
13f71e678dbd   opea/vllm-rocm:latest                                   "python3 /workspace/…"   3 hours ago      Up 3 hours (healthy)   0.0.0.0:8086->8011/tcp, [::]:8086->8011/tcp                                                vllm-service
e5a219a77c95   opea/llm-docsum:latest                                  "bash entrypoint.sh"     3 hours ago      Up 2 seconds           0.0.0.0:33218->9000/tcp, [::]:33218->9000/tcp                                              docsum-llm-server
```

### 3.5 Validate agents

FinQA Agent:

```bash
export agent_port="9095"
prompt="What is Gap's revenue in 2024?"
python3 $WORKDIR/GenAIExamples/FinanceAgent/tests/test.py --prompt "$prompt" --agent_role "worker" --ext_port $agent_port
```

Research Agent:

```bash
export agent_port="9096"
prompt="generate NVDA financial research report"
python3 $WORKDIR/GenAIExamples/FinanceAgent/tests/test.py --prompt "$prompt" --agent_role "worker" --ext_port $agent_port --tool_choice "get_current_date" --tool_choice "get_share_performance"
```

Supervisor Agent single turns:

```bash
export agent_port="9090"
python3 $WORKDIR/GenAIExamples/FinanceAgent/tests/test.py --agent_role "supervisor" --ext_port $agent_port --stream
```

Supervisor Agent multi turn:

```bash
python3 $WORKDIR/GenAIExamples/FinanceAgent/tests/test.py --agent_role "supervisor" --ext_port $agent_port --multi-turn --stream

```

### Cleanup the Deployment

To stop the containers associated with the deployment, execute the following commands:

```
docker compose -f compose.yaml down
docker compose -f compose_vllm.yaml down
docker compose -f dataprep_compose.yaml down
```

All the Finance Agent containers will be stopped and then removed on completion of the "down" command.

## Finance Agent Docker Compose Files

In the context of deploying a Finance Agent pipeline on an AMD GPU platform, we can pick and choose different large language model serving frameworks. The table below outlines the various configurations that are available as part of the application.

| File                                             | Description                                                                           |
| ------------------------------------------------ | ------------------------------------------------------------------------------------- |
| [compose.yaml](./compose.yaml)                   | Default compose to run agent service                                                  |
| [compose_vllm.yaml](./compose_vllm.yaml)         | The LLM Service serving framework is vLLM.                                            |
| [dataprep_compose.yaml](./dataprep_compose.yaml) | Compose file to run Data Prep service such as Redis vector DB, Re-rancer and Embedder |

## How to interact with the agent system with UI

The UI microservice is launched in the previous step with the other microservices.
To see the UI, open a web browser to `http://${ip_address}:5175` to access the UI. Note the `ip_address` here is the host IP of the UI microservice.

1. Create Admin Account with a random value

2. Enter the endpoints in the `Connections` settings

   First, click on the user icon in the upper right corner to open `Settings`. Click on `Admin Settings`. Click on `Connections`.

   Then, enter the supervisor agent endpoint in the `OpenAI API` section: `http://${ip_address}:9090/v1`. Enter the API key as "empty". Add an arbitrary model id in `Model IDs`, for example, "opea_agent". The `ip_address` here should be the host ip of the agent microservice.

   Then, enter the dataprep endpoint in the `Icloud File API` section. You first need to enable `Icloud File API` by clicking on the button on the right to turn it into green and then enter the endpoint url, for example, `http://${ip_address}:6007/v1`. The `ip_address` here should be the host ip of the dataprep microservice.

   You should see screen like the screenshot below when the settings are done.

![opea-agent-setting](../../../../assets/ui_connections_settings.png)

3. Upload documents with UI

   Click on the `Workplace` icon in the top left corner. Click `Knowledge`. Click on the "+" sign to the right of `Icloud Knowledge`. You can paste an url in the left hand side of the pop-up window, or upload a local file by click on the cloud icon on the right hand side of the pop-up window. Then click on the `Upload Confirm` button. Wait till the processing is done and the pop-up window will be closed on its own when the data ingestion is done. See the screenshot below.

   Note: the data ingestion may take a few minutes depending on the length of the document. Please wait patiently and do not close the pop-up window.

![upload-doc-ui](../../../../assets/upload_doc_ui.png)

4. Test agent with UI

   After the settings are done and documents are ingested, you can start to ask questions to the agent. Click on the `New Chat` icon in the top left corner, and type in your questions in the text box in the middle of the UI.

   The UI will stream the agent's response tokens. You need to expand the `Thinking` tab to see the agent's reasoning process. After the agent made tool calls, you would also see the tool output after the tool returns output to the agent. Note: it may take a while to get the tool output back if the tool execution takes time.

![opea-agent-test](../../../../assets/opea-agent-test.png)
