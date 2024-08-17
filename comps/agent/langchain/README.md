# langchain Agent Microservice

The langchain agent model refers to a framework that integrates the reasoning capabilities of large language models (LLMs) with the ability to take actionable steps, creating a more sophisticated system that can understand and process information, evaluate situations, take appropriate actions, communicate responses, and track ongoing situations.

![Architecture Overview](agent_arch.jpg)

## 🚀1. Start Microservice with Python（Option 1）

### 1.1 Install Requirements

```bash
cd comps/agent/langchain/
pip install -r requirements.txt
```

### 1.2 Start Microservice with Python Script

```bash
cd comps/agent/langchain/
python agent.py
```

## 🚀2. Start Microservice with Docker (Option 2)

### Build Microservices

```bash
cd GenAIComps/ # back to GenAIComps/ folder
docker build -t opea/comps-agent-langchain:latest -f comps/agent/langchain/docker/Dockerfile .
```

### start microservices

```bash
export ip_address=$(hostname -I | awk '{print $1}')
export model=meta-llama/Meta-Llama-3-8B-Instruct
export HUGGINGFACEHUB_API_TOKEN=${HUGGINGFACEHUB_API_TOKEN}
export HF_TOKEN=${HUGGINGFACEHUB_API_TOKEN}

# TGI serving
docker run -d --runtime=habana --name "comps-tgi-gaudi-service" -p 8080:80 -v ./data:/data -e HF_TOKEN=$HF_TOKEN -e HABANA_VISIBLE_DEVICES=all -e OMPI_MCA_btl_vader_single_copy_mechanism=none --cap-add=sys_nice --ipc=host ghcr.io/huggingface/tgi-gaudi:latest --model-id $model --max-input-tokens 4096 --max-total-tokens 8092

# check status
docker logs comps-tgi-gaudi-service

# Agent
docker run -d --runtime=runc --name="comps-langchain-agent-endpoint" -v $WORKPATH/comps/agent/langchain/tools:/home/user/comps/agent/langchain/tools -p 9090:9090 --ipc=host -e HUGGINGFACEHUB_API_TOKEN=${HUGGINGFACEHUB_API_TOKEN} -e model=${model} -e ip_address=${ip_address} -e strategy=react -e llm_endpoint_url=http://${ip_address}:8080 -e llm_engine=tgi -e recursion_limit=5 -e require_human_feedback=false -e tools=/home/user/comps/agent/langchain/tools/custom_tools.yaml opea/comps-agent-langchain:latest

# check status
docker logs comps-langchain-agent-endpoint
```

> debug mode
>
> ```bash
> docker run --rm --runtime=runc --name="comps-langchain-agent-endpoint" -v ./comps/agent/langchain/:/home/user/comps/agent/langchain/ -p 9090:9090 --ipc=host -e http_proxy=$http_proxy -e https_proxy=$https_proxy -e HUGGINGFACEHUB_API_TOKEN=${HUGGINGFACEHUB_API_TOKEN} --env-file ${agent_env} opea/comps-agent-langchain:latest
> ```

## 🚀3. Validate Microservice

Once microservice starts, user can use below script to invoke.

```bash
curl http://${ip_address}:9090/v1/chat/completions -X POST -H "Content-Type: application/json" -d '{
     "query": "What is the weather today in Austin?"
    }'

# expected output

data: 'The temperature in Austin today is 78°F.</s>'

data: [DONE]

```

## 🚀4. Provide your own tools

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
docker run -d --runtime=runc --name="comps-langchain-agent-endpoint" -v my_tools:/home/user/comps/agent/langchain/tools -p 9090:9090 --ipc=host -e HUGGINGFACEHUB_API_TOKEN=${HUGGINGFACEHUB_API_TOKEN} -e model=${model} -e ip_address=${ip_address} -e strategy=react -e llm_endpoint_url=http://${ip_address}:8080 -e llm_engine=tgi -e recursive_limit=5 -e require_human_feedback=false -e tools=/home/user/comps/agent/langchain/tools/custom_tools.yaml opea/comps-agent-langchain:latest
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
