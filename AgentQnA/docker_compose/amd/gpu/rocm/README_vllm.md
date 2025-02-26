# Single node on-prem deployment with Docker Compose on AMD GPU

This example showcases a hierarchical multi-agent system for question-answering applications. We deploy the example on Xeon. For LLMs, we use OpenAI models via API calls. For instructions on using open-source LLMs, please refer to the deployment guide [here](../../../../README.md).

## Deployment with docker

1. First, clone this repo.
   ```
   export WORKDIR=<your-work-directory>
   cd $WORKDIR
   git clone https://github.com/opea-project/GenAIExamples.git
   ```
2. Set up environment for this example </br>

   ```
   # Example: host_ip="192.168.1.1" or export host_ip="External_Public_IP"
   export host_ip=$(hostname -I | awk '{print $1}')
   # if you are in a proxy environment, also set the proxy-related environment variables
   export http_proxy="Your_HTTP_Proxy"
   export https_proxy="Your_HTTPs_Proxy"
   # Example: no_proxy="localhost, 127.0.0.1, 192.168.1.1"
   export no_proxy="Your_No_Proxy"

   export TOOLSET_PATH=$WORKDIR/GenAIExamples/AgentQnA/tools/
   #OPANAI_API_KEY if you want to use OpenAI models
   export OPENAI_API_KEY=<your-openai-key>
   # Set AMD GPU settings
   export AGENTQNA_CARD_ID="card1"
   export AGENTQNA_RENDER_ID="renderD136"
   ```

3. Deploy the retrieval tool (i.e., DocIndexRetriever mega-service)

   First, launch the mega-service.

   ```
   cd $WORKDIR/GenAIExamples/AgentQnA/retrieval_tool
   bash launch_retrieval_tool.sh
   ```

   Then, ingest data into the vector database. Here we provide an example. You can ingest your own data.

   ```
   bash run_ingest_data.sh
   ```

4. Launch Tool service
   In this example, we will use some of the mock APIs provided in the Meta CRAG KDD Challenge to demonstrate the benefits of gaining additional context from mock knowledge graphs.
   ```
   docker run -d -p=8080:8000 docker.io/aicrowd/kdd-cup-24-crag-mock-api:v0
   ```
5. Launch `Agent` service

   ```
   cd $WORKDIR/GenAIExamples/AgentQnA/docker_compose/amd/gpu/rocm
   bash launch_agent_service_tgi_rocm.sh
   ```

6. [Optional] Build `Agent` docker image if pulling images failed.

   ```
   git clone https://github.com/opea-project/GenAIComps.git
   cd GenAIComps
   docker build -t opea/agent:latest -f comps/agent/src/Dockerfile .
   ```

## Validate services

First look at logs of the agent docker containers:

```
# worker agent
docker logs rag-agent-endpoint
```

```
# supervisor agent
docker logs react-agent-endpoint
```

You should see something like "HTTP server setup successful" if the docker containers are started successfully.</p>

Second, validate worker agent:

```
curl http://${host_ip}:9095/v1/chat/completions -X POST -H "Content-Type: application/json" -d '{
     "query": "Most recent album by Taylor Swift"
    }'
```

Third, validate supervisor agent:

```
curl http://${host_ip}:9090/v1/chat/completions -X POST -H "Content-Type: application/json" -d '{
     "query": "Most recent album by Taylor Swift"
    }'
```

## How to register your own tools with agent

You can take a look at the tools yaml and python files in this example. For more details, please refer to the "Provide your own tools" section in the instructions [here](https://github.com/opea-project/GenAIComps/tree/main/comps/agent/src/README.md).
