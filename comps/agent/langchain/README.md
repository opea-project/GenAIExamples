# Agent Microservice

## 1. Overview

This agent microservice is built on Langchain/Langgraph frameworks. Agents integrate the reasoning capabilities of large language models (LLMs) with the ability to take actionable steps, creating a more sophisticated system that can understand and process information, evaluate situations, take appropriate actions, communicate responses, and track ongoing situations.

### 1.1 Supported agent types

We currently support the following types of agents:

1. ReAct: use `react_langchain` or `react_langgraph` as strategy. First introduced in this seminal [paper](https://arxiv.org/abs/2210.03629). The ReAct agent engages in "reason-act-observe" cycles to solve problems. Please refer to this [doc](https://python.langchain.com/v0.2/docs/how_to/migrate_agent/) to understand the differences between the langchain and langgraph versions of react agents.
2. RAG agent: `rag_agent` strategy. This agent is specifically designed for improving RAG performance. It has the capability to rephrase query, check relevancy of retrieved context, and iterate if context is not relevant.
3. Plan and execute: `plan_execute` strategy. This type of agent first makes a step-by-step plan given a user request, and then execute the plan sequentially (or in parallel, to be implemented in future). If the execution results can solve the problem, then the agent will output an answer; otherwise, it will replan and execute again.
   For advanced developers who want to implement their own agent strategies, please refer to [Section 5](#5-customize-agent-strategy) below.

### 1.2 LLM engine

Agents use LLM for reasoning and planning. We support 2 options of LLM engine:

1. Open-source LLMs served with TGI-gaudi. To use open-source llms, follow the instructions in [Section 2](#222-start-microservices) below. Note: we recommend using state-of-the-art LLMs, such as llama3.1-70B-instruct, to get higher success rate.
2. OpenAI LLMs via API calls. To use OpenAI llms, specify `llm_engine=openai` and `export OPENAI_API_KEY=<your-openai-key>`

### 1.3 Tools

The tools are registered with a yaml file. We support the following types of tools:

1. Endpoint: user to provide url
2. User-defined python functions. This is usually used to wrap endpoints with request post or simple pre/post-processing.
3. Langchain tool modules.
   Examples of how to register tools can be found in [Section 4](#-4-provide-your-own-tools) below.

### 1.4 Agent APIs

Currently we have implemented OpenAI chat completion compatible API for agents. We are working to support OpenAI assistants APIs.

## 🚀2. Start Agent Microservice

### 2.1 Option 1: with Python

#### 2.1.1 Install Requirements

```bash
cd comps/agent/langchain/
pip install -r requirements.txt
```

#### 2.1.2 Start Microservice with Python Script

```bash
cd comps/agent/langchain/
python agent.py
```

### 2.2 Option 2. Start Microservice with Docker

#### 2.2.1 Build Microservices

```bash
cd GenAIComps/ # back to GenAIComps/ folder
docker build -t opea/agent-langchain:latest -f comps/agent/langchain/Dockerfile .
```

#### 2.2.2 Start microservices

```bash
export ip_address=$(hostname -I | awk '{print $1}')
export model=mistralai/Mistral-7B-Instruct-v0.3
export HUGGINGFACEHUB_API_TOKEN=${HUGGINGFACEHUB_API_TOKEN}
export HF_TOKEN=${HUGGINGFACEHUB_API_TOKEN}

# TGI serving
docker run -d --runtime=habana --name "comps-tgi-gaudi-service" -p 8080:80 -v ./data:/data -e HF_TOKEN=$HF_TOKEN -e HABANA_VISIBLE_DEVICES=all -e OMPI_MCA_btl_vader_single_copy_mechanism=none --cap-add=sys_nice --ipc=host ghcr.io/huggingface/tgi-gaudi:latest --model-id $model --max-input-tokens 4096 --max-total-tokens 8092

# check status
docker logs comps-tgi-gaudi-service

# Agent
docker run -d --runtime=runc --name="comps-langchain-agent-endpoint" -v $WORKPATH/comps/agent/langchain/tools:/home/user/comps/agent/langchain/tools -p 9090:9090 --ipc=host -e HUGGINGFACEHUB_API_TOKEN=${HUGGINGFACEHUB_API_TOKEN} -e model=${model} -e ip_address=${ip_address} -e strategy=react -e llm_endpoint_url=http://${ip_address}:8080 -e llm_engine=tgi -e recursion_limit=5 -e require_human_feedback=false -e tools=/home/user/comps/agent/langchain/tools/custom_tools.yaml opea/agent-langchain:latest

# check status
docker logs comps-langchain-agent-endpoint
```

> debug mode
>
> ```bash
> docker run --rm --runtime=runc --name="comps-langchain-agent-endpoint" -v ./comps/agent/langchain/:/home/user/comps/agent/langchain/ -p 9090:9090 --ipc=host -e http_proxy=$http_proxy -e https_proxy=$https_proxy -e HUGGINGFACEHUB_API_TOKEN=${HUGGINGFACEHUB_API_TOKEN} -e model=${model} -e ip_address=${ip_address} -e strategy=react -e llm_endpoint_url=http://${ip_address}:8080 -e llm_engine=tgi -e recursion_limit=5 -e require_human_feedback=false -e tools=/home/user/comps/agent/langchain/tools/custom_tools.yaml opea/agent-langchain:latest
> ```

## 🚀 3. Validate Microservice

Once microservice starts, user can use below script to invoke.

```bash
curl http://${ip_address}:9090/v1/chat/completions -X POST -H "Content-Type: application/json" -d '{
     "query": "What is the weather today in Austin?"
    }'

# expected output

data: 'The temperature in Austin today is 78°F.</s>'

data: [DONE]

```

## 🚀 4. Provide your own tools

- Define tools

```bash
mkdir -p my_tools
vim my_tools/custom_tools.yaml

# [tool_name]
#   description: [description of this tool]
#   env: [env variables such as API_TOKEN]
#   pip_dependencies: [pip dependencies, separate by ,]
#   callable_api: [2 options provided - function_call, pre-defined-tools]
#   args_schema:
#     [arg_name]:
#       type: [str, int]
#       description: [description of this argument]
#   return_output: [return output variable name]
```

example - my_tools/custom_tools.yaml

```yaml
# Follow example below to add your tool
opea_index_retriever:
  description: Retrieve related information of Intel OPEA project based on input query.
  callable_api: tools.py:opea_rag_query
  args_schema:
    query:
      type: str
      description: Question query
  return_output: retrieved_data
```

example - my_tools/tools.py

```python
def opea_rag_query(query):
    ip_address = os.environ.get("ip_address")
    url = f"http://{ip_address}:8889/v1/retrievaltool"
    content = json.dumps({"text": query})
    print(url, content)
    try:
        resp = requests.post(url=url, data=content)
        ret = resp.text
        resp.raise_for_status()  # Raise an exception for unsuccessful HTTP status codes
    except requests.exceptions.RequestException as e:
        ret = f"An error occurred:{e}"
    return ret
```

- Launch Agent Microservice with your tools path

```bash
# Agent
docker run -d --runtime=runc --name="comps-langchain-agent-endpoint" -v my_tools:/home/user/comps/agent/langchain/tools -p 9090:9090 --ipc=host -e HUGGINGFACEHUB_API_TOKEN=${HUGGINGFACEHUB_API_TOKEN} -e model=${model} -e ip_address=${ip_address} -e strategy=react -e llm_endpoint_url=http://${ip_address}:8080 -e llm_engine=tgi -e recursive_limit=5 -e require_human_feedback=false -e tools=/home/user/comps/agent/langchain/tools/custom_tools.yaml opea/agent-langchain:latest
```

- validate with my_tools

```bash
$ curl http://${ip_address}:9090/v1/chat/completions -X POST -H "Content-Type: application/json" -d '{
     "query": "What is Intel OPEA project in a short answer?"
    }'
data: 'The Intel OPEA project is a initiative to incubate open source development of trusted, scalable open infrastructure for developer innovation and harness the potential value of generative AI. - - - - Thought:  I now know the final answer. - - - - - - Thought: - - - -'

data: [DONE]

$ curl http://${ip_address}:9090/v1/chat/completions -X POST -H "Content-Type: application/json" -d '{
     "query": "What is the weather today in Austin?"
    }'
data: 'The weather information in Austin is not available from the Open Platform for Enterprise AI (OPEA). You may want to try checking another source such as a weather app or website. I apologize for not being able to find the information you were looking for. <|eot_id|>'

data: [DONE]
```

## 5. Customize agent strategy

For advanced developers who want to implement their own agent strategies, you can add a separate folder in `src\strategy`, implement your agent by inherit the `BaseAgent` class, and add your strategy into the `src\agent.py`. The architecture of this agent microservice is shown in the diagram below as a reference.
![Architecture Overview](agent_arch.jpg)
