# Hierarchical Agentic RAG
## Overview
architecture diagram
### Advantages of Agentic RAG
TODO
### Supported APIs
Currently we support OpenAI chat completion compatible API. We are working to support OpenAI assistants APIs.

## Getting started
1. Build agent docker image
First, clone the opea GenAIComps repo
```
export WORKDIR=<your-work-directory>
cd $WORKDIR
git clone https://github.com/opea-project/GenAIComps.git
```
Then build the agent docker image. Both the supervisor agent and the worker agent will use the same docker image, but when we launch the two agents we will specify different strategies and register different tools.
```
cd GenAIComps
docker build -t opea/comps-agent-langchain:latest --build-arg https_proxy=$https_proxy --build-arg http_proxy=$http_proxy -f comps/agent/langchain/docker/Dockerfile .
```
2. Lanuch tool services
In this example, we will use some of the mock APIs provided in the Meta CRAG KDD Challenge to demonstrate the benefits of gaining additional context from mock knowledge graphs.
```
docker run -d -p=8080:8000 docker.io/aicrowd/kdd-cup-24-crag-mock-api:v0
```
3. Set up environment for this example
First, clone this repo
```
cd $WORKDIR
git clone https://github.com/opea-project/GenAIExamples.git
```
Second, set up env vars
```
export TOOLSET_PATH=$WORKDIR/GenAIExamples/HierarchicalAgenticRAG/tools/
# optional: OPANAI_API_KEY
export OPENAI_API_KEY=<your-openai-key>
```
4. Launch agent services
The configurations of the supervisor agent and the worker agent are defined in the docker-compose yaml file. We currently use openAI GPT-4o-mini as LLM, and we plan to add support for llama3.1-70B-instruct (served by TGI-Gaudi) in a subsequent release.
To use openai llm, run command below.
```
cd docker/openai/
bash launch_agent_service_openai.sh
```


## Validate services
First look at logs of the agent docker containers:
```
docker logs docgrader-agent-endpoint
docker logs react-agent-endpoint
```
You should see something like "HTTP server setup successful" if the docker containers are started successfully.</p>

Second, validate worker agent:
```
curl http://${ip_address}:9095/v1/chat/completions -X POST -H "Content-Type: application/json" -d '{
     "query": "Most recent album by Taylor Swift"
    }'
``` 
Third, validate supervisor agent:
```
curl http://${ip_address}:9090/v1/chat/completions -X POST -H "Content-Type: application/json" -d '{
     "query": "Most recent album by Taylor Swift"
    }'
```

## How to register your own tools with agent
You can take a look at the tools yaml and python files in this example. For more details, please refer to the "Provide your own tools" section in the instructions [here](https://github.com/minmin-intel/GenAIComps/tree/agent-comp-dev/comps/agent/langchain#4-provide-your-own-tools). 