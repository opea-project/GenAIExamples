# Single node on-prem deployment AgentQnA on Gaudi

This example showcases a hierarchical multi-agent system for question-answering applications. We deploy the example on Gaudi using open-source LLMs.
For more details, please refer to the deployment guide [here](../../../../README.md).

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
   # for using open-source llms
   export HUGGINGFACEHUB_API_TOKEN=<your-HF-token>
   # Example export HF_CACHE_DIR=$WORKDIR so that no need to redownload every time
   export HF_CACHE_DIR=<directory-where-llms-are-downloaded>

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

4. Prepare SQL database
   In this example, we will use the Chinook SQLite database. Run the commands below.

   ```
   # Download data
   cd $WORKDIR
   git clone https://github.com/lerocha/chinook-database.git
   cp chinook-database/ChinookDatabase/DataSources/Chinook_Sqlite.sqlite $WORKDIR/GenAIExamples/AgentQnA/tests/
   ```

5. Launch Tool service
   In this example, we will use some of the mock APIs provided in the Meta CRAG KDD Challenge to demonstrate the benefits of gaining additional context from mock knowledge graphs.
   ```
   docker run -d -p=8080:8000 docker.io/aicrowd/kdd-cup-24-crag-mock-api:v0
   ```
6. Launch multi-agent system

   On Gaudi2 we will serve `meta-llama/Meta-Llama-3.1-70B-Instruct` using vllm.

   First build vllm-gaudi docker image.

   ```bash
   cd $WORKDIR
   git clone https://github.com/vllm-project/vllm.git
   cd ./vllm
   git checkout v0.6.6
   docker build --no-cache -f Dockerfile.hpu -t opea/vllm-gaudi:latest --shm-size=128g . --build-arg https_proxy=$https_proxy --build-arg http_proxy=$http_proxy
   ```

   Then launch vllm on Gaudi2 with the command below.

   ```bash
   vllm_port=8086
   model="meta-llama/Meta-Llama-3.1-70B-Instruct"
   docker run -d --runtime=habana --rm --name "vllm-gaudi-server" -e HABANA_VISIBLE_DEVICES=0,1,2,3 -p $vllm_port:8000 -v $vllm_volume:/data -e HF_TOKEN=$HF_TOKEN -e HUGGING_FACE_HUB_TOKEN=$HF_TOKEN -e HF_HOME=/data -e OMPI_MCA_btl_vader_single_copy_mechanism=none -e PT_HPU_ENABLE_LAZY_COLLECTIVES=true -e http_proxy=$http_proxy -e https_proxy=$https_proxy -e no_proxy=$no_proxy -e VLLM_SKIP_WARMUP=true --cap-add=sys_nice --ipc=host opea/vllm-gaudi:latest --model ${model} --max-seq-len-to-capture 16384 --tensor-parallel-size 4
   ```

   Then launch Agent microservices.

   ```bash
   cd $WORKDIR/GenAIExamples/AgentQnA/docker_compose/intel/hpu/gaudi/
   bash launch_agent_service_gaudi.sh
   ```

7. [Optional] Build `Agent` docker image if pulling images failed.

   If docker image pulling failed in Step 6 above, build the agent docker image with the commands below. After image build, try Step 6 again.

   ```
   git clone https://github.com/opea-project/GenAIComps.git
   cd GenAIComps
   docker build -t opea/agent:latest -f comps/agent/src/Dockerfile .
   ```

## Validate services

First look at logs of the agent docker containers:

```
# worker RAG agent
docker logs rag-agent-endpoint

# worker SQL agent
docker logs sql-agent-endpoint
```

```
# supervisor agent
docker logs react-agent-endpoint
```

You should see something like "HTTP server setup successful" if the docker containers are started successfully.</p>

Second, validate worker RAG agent:

```
curl http://${host_ip}:9095/v1/chat/completions -X POST -H "Content-Type: application/json" -d '{
     "messages": "Michael Jackson song Thriller"
    }'
```

Third, validate worker SQL agent:

```
curl http://${host_ip}:9095/v1/chat/completions -X POST -H "Content-Type: application/json" -d '{
     "messages": "How many employees are in the company?"
    }'
```

Finally, validate supervisor agent:

```
curl http://${host_ip}:9090/v1/chat/completions -X POST -H "Content-Type: application/json" -d '{
     "messages": "How many albums does Iron Maiden have?"
    }'
```

## How to register your own tools with agent

You can take a look at the tools yaml and python files in this example. For more details, please refer to the "Provide your own tools" section in the instructions [here](https://github.com/opea-project/GenAIComps/tree/main/comps/agent/src/README.md).
