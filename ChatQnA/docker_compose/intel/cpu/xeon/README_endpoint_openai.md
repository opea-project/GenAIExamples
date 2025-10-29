# Build Mega Service of ChatQnA on Xeon with an LLM Endpoint

This document outlines the single node deployment process for a ChatQnA application utilizing the [GenAIComps](https://github.com/opea-project/GenAIComps.git) microservices on Intel Xeon server. The steps include pulling Docker images, container deployment via Docker Compose, and service execution to integrate microservices such as `embedding`, `retriever`, `rerank` and `llm`.

## Table of contents

1. [ChatQnA Quick Start Deployment](#chatqna-quick-start-Deployment)
2. [ChatQnA Docker Compose file Options](#chatqna-docker-compose-files)
3. [ChatQnA with Conversational UI](#chatqna-with-conversational-ui-optional)

## ChatQnA Quick Start Deployment

This section describes how to quickly deploy and test the ChatQnA service manually on an Intel® Xeon® processor. The basic steps are:

1. [Access the Code](#access-the-code)
2. [Generate a HuggingFace Access Token](#generate-a-huggingface-access-token)
3. [Configure the Deployment Environment](#configure-the-deployment-environment)
4. [Deploy the Services Using Docker Compose](#deploy-the-services-using-docker-compose)
5. [Check the Deployment Status](#check-the-deployment-status)
6. [Test the Pipeline](#test-the-pipeline)
7. [Cleanup the Deployment](#cleanup-the-deployment)

### Access the Code

Clone the GenAIExample repository and access the ChatQnA Intel® Gaudi® platform Docker Compose files and supporting scripts:

```
git clone https://github.com/opea-project/GenAIComps
cd GenAIComps

# Build the opea/llm-textgen image.

docker build \
  --no-cache \
  --build-arg https_proxy=$https_proxy \
  --build-arg http_proxy=$http_proxy \
  -t opea/llm-textgen:latest \
  -f comps/llms/src/text-generation/Dockerfile .


cd ../
git clone https://github.com/opea-project/GenAIExamples.git
cd GenAIExamples/ChatQnA/docker_compose/intel/cpu/xeon/
```

### Generate a HuggingFace Access Token

Some HuggingFace resources, such as some models, are only accessible if the developer have an access token. In the absence of a HuggingFace access token, the developer can create one by first creating an account by following the steps provided at [HuggingFace](https://huggingface.co/) and then generating a [user access token](https://huggingface.co/docs/transformers.js/en/guides/private#step-1-generating-a-user-access-token).

## Endpoint Access

An OpenAI-compatible endpoint is required e.g., OpenRouter.ai. Please obtain a valid API key.

### Configure the Deployment Environment

To set up environment variables for deploying ChatQnA services, set up some parameters specific to the deployment environment and source the _setup_env.sh_ script in this directory:

```bash
cd GenAIExamples/ChatQnA/docker_compose/intel/cpu/xeon
source set_env.sh # source environment variables then override below.

export host_ip="External_Public_IP" # e.g. export host_ip=$(hostname -I | awk '{print $1}')
export HF_TOKEN="Your_Huggingface_API_Token"
export OPENAI_API_KEY="key for openAI-like endpoint"

export LLM_MODEL_ID="" # e.g. "google/gemma-3-1b-it:free"
export LLM_ENDPOINT=""  # e.g. "https://openrouter.ai/api" (please make sure to omit /v1 suffix)
export no_proxy="" # Can set if any no proxy variables. See set_env.sh
```

Consult the section on [ChatQnA Service configuration](#chatqna-configuration) for information on how service specific configuration parameters affect deployments.

### Deploy the Services Using Docker Compose

To deploy the ChatQnA services, execute the `docker compose up` command with the appropriate arguments. For a default deployment, execute the command below. It uses the 'compose.yaml' file.

```bash
NGINX_PORT=8080 docker compose -f compose_endpoint_openai.yaml up -d
```

Usage of NGINX_PORT=8080 allows you to access the chat console on localhost:8080 since webbrowser may use port 80.

To enable Open Telemetry Tracing, compose.telemetry.yaml file need to be merged along with default compose.yaml file.  
CPU example with Open Telemetry feature:

> NOTE : To get supported Grafana Dashboard, please run download_opea_dashboard.sh following below commands.

```bash
./grafana/dashboards/download_opea_dashboard.sh
NGINX_PORT=8080 docker compose -f compose_endpoint_openai.yaml -f compose.telemetry.yaml up -d
```

**Note**: developers should build docker image from source when:

- Developing off the git main branch (as the container's ports in the repo may be different from the published docker image).
- Unable to download the docker image.
- Use a specific version of Docker image.

Please refer to the table below to build different microservices from source:

| Microservice | Deployment Guide                                                                              |
| ------------ | --------------------------------------------------------------------------------------------- |
| Dataprep     | https://github.com/opea-project/GenAIComps/tree/main/comps/dataprep                           |
| Embedding    | https://github.com/opea-project/GenAIComps/tree/main/comps/embeddings                         |
| Retriever    | https://github.com/opea-project/GenAIComps/tree/main/comps/retrievers                         |
| Reranker     | https://github.com/opea-project/GenAIComps/tree/main/comps/rerankings                         |
| LLM          | https://github.com/opea-project/GenAIComps/tree/main/comps/llms                               |
| Megaservice  | [Megaservice build guide](../../../../README_miscellaneous.md#build-megaservice-docker-image) |
| UI           | [Basic UI build guide](../../../../README_miscellaneous.md#build-ui-docker-image)             |

### Check the Deployment Status

After running docker compose, check if all the containers launched via docker compose have started:

```
docker ps -a
```

For the endpoint-based deployment, the following 9 containers should be running:

```bash
CONTAINER ID   IMAGE                                                   COMMAND                  CREATED          STATUS                    PORTS                                                                                  NAMES
04f0e3607457   opea/nginx:${RELEASE_VERSION}                           "/docker-entrypoint.…"   17 minutes ago   Up 16 minutes             0.0.0.0:8080->80/tcp, [::]:8080->80/tcp                                                chatqna-xeon-nginx-server
6d7fe1bfd0a5   opea/chatqna-ui:${RELEASE_VERSION}                      "docker-entrypoint.s…"   17 minutes ago   Up 16 minutes             0.0.0.0:5173->5173/tcp, :::5173->5173/tcp                                              chatqna-xeon-ui-server
71d01fe8bc94   opea/chatqna:${RELEASE_VERSION}                         "python chatqna.py"      17 minutes ago   Up 16 minutes             0.0.0.0:8888->8888/tcp, :::8888->8888/tcp                                              chatqna-xeon-backend-server
ea12fab1c70e   opea/retriever:${RELEASE_VERSION}                       "python opea_retriev…"   17 minutes ago   Up 17 minutes             0.0.0.0:7000->7000/tcp, :::7000->7000/tcp                                              retriever-redis-server
253622403ed6   opea/dataprep:${RELEASE_VERSION}                        "sh -c 'python $( [ …"   17 minutes ago   Up 17 minutes (healthy)   0.0.0.0:6007->5000/tcp, [::]:6007->5000/tcp                                            dataprep-redis-server
a552cf4f0dd0   redis/redis-stack:7.2.0-v9                              "/entrypoint.sh"         17 minutes ago   Up 17 minutes (healthy)   0.0.0.0:6379->6379/tcp, :::6379->6379/tcp, 0.0.0.0:8001->8001/tcp, :::8001->8001/tcp   redis-vector-db
6795a52137f7   ghcr.io/huggingface/text-embeddings-inference:cpu-1.5   "text-embeddings-rou…"   17 minutes ago   Up 17 minutes             0.0.0.0:6006->80/tcp, [::]:6006->80/tcp                                                tei-embedding-server
3e55313e714b   opea/llm-textgen:${RELEASE_VERSION}                     "bash entrypoint.sh"     17 minutes ago   Up 17 minutes             0.0.0.0:9000->9000/tcp, :::9000->9000/tcp                                              textgen-service-endpoint-openai
10318f82c943   ghcr.io/huggingface/text-embeddings-inference:cpu-1.5   "text-embeddings-rou…"   17 minutes ago   Up 17 minutes             0.0.0.0:8808->80/tcp, [::]:8808->80/tcp                                                tei-reranking-server
```

If any issues are encountered during deployment, refer to the [troubleshooting](../../../../README_miscellaneous.md##troubleshooting) section.

### Test the Pipeline

Once the ChatQnA services are running, test the pipeline using the following command. This will send a sample query to the ChatQnA service and return a response.

```bash
curl http://${host_ip}:8888/v1/chatqna \
    -H "Content-Type: application/json" \
    -d '{
        "messages": "What is the revenue of Nike in 2023?"
    }'
```

**Note** : Access the ChatQnA UI by web browser through this URL: `http://${host_ip}:8080`. Please confirm the `8080` port is opened in the firewall. To validate each microservice used in the pipeline refer to the [Validate microservices](#validate-microservices) section.

### Cleanup the Deployment

To stop the containers associated with the deployment, execute the following command:

```
docker compose -f compose.yaml down
```

## ChatQnA Docker Compose Files

In the context of deploying a ChatQnA pipeline on an Intel® Xeon® platform, we can pick and choose different vector databases, large language model serving frameworks, and remove pieces of the pipeline such as the reranker. The table below outlines the various configurations that are available as part of the application. These configurations can be used as templates and can be extended to different components available in [GenAIComps](https://github.com/opea-project/GenAIComps.git).

| File                                                           | Description                                                                                                                                                           |
| -------------------------------------------------------------- | --------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| [compose.yaml](./compose.yaml)                                 | Default compose file using vllm as serving framework and redis as vector database                                                                                     |
| [compose_endpoint_openai.yaml](./compose_endpoint_openai.yaml) | Uses OpenAI-compatible endpoint (remote or local) as LLM serving framework with redis as vector database.                                                             |
| [compose_milvus.yaml](./compose_milvus.yaml)                   | Uses Milvus as the vector database. All other configurations remain the same as the default                                                                           |
| [compose_pinecone.yaml](./compose_pinecone.yaml)               | Uses Pinecone as the vector database. All other configurations remain the same as the default. For more details, refer to [README_pinecone.md](./README_pinecone.md). |
| [compose_qdrant.yaml](./compose_qdrant.yaml)                   | Uses Qdrant as the vector database. All other configurations remain the same as the default. For more details, refer to [README_qdrant.md](./README_qdrant.md).       |
| [compose_tgi.yaml](./compose_tgi.yaml)                         | Uses TGI as the LLM serving framework. All other configurations remain the same as the default                                                                        |
| [compose_without_rerank.yaml](./compose_without_rerank.yaml)   | Default configuration without the reranker                                                                                                                            |
| [compose_faqgen.yaml](./compose_faqgen.yaml)                   | Enables FAQ generation using vLLM as the LLM serving framework. For more details, refer to [README_faqgen.md](./README_faqgen.md).                                    |
| [compose_faqgen_tgi.yaml](./compose_faqgen_tgi.yaml)           | Enables FAQ generation using TGI as the LLM serving framework. For more details, refer to [README_faqgen.md](./README_faqgen.md).                                     |
| [compose.telemetry.yaml](./compose.telemetry.yaml)             | Helper file for telemetry features for vllm. Can be used along with any compose files that serves vllm                                                                |
| [compose_tgi.telemetry.yaml](./compose_tgi.telemetry.yaml)     | Helper file for telemetry features for tgi. Can be used along with any compose files that serves tgi                                                                  |
| [compose_mariadb.yaml](./compose_mariadb.yaml)                 | Uses MariaDB Server as the vector database. All other configurations remain the same as the default                                                                   |

## ChatQnA with Conversational UI (Optional)

To access the Conversational UI (react based) frontend, modify the UI service in the `compose` file used to deploy. Replace `chatqna-xeon-ui-server` service with the `chatqna-xeon-conversation-ui-server` service as per the config below:

```yaml
chatqna-xeon-conversation-ui-server:
  image: opea/chatqna-conversation-ui:latest
  container_name: chatqna-xeon-conversation-ui-server
  environment:
    - APP_BACKEND_SERVICE_ENDPOINT=${BACKEND_SERVICE_ENDPOINT}
    - APP_DATA_PREP_SERVICE_URL=${DATAPREP_SERVICE_ENDPOINT}
  ports:
    - "5174:80"
  depends_on:
    - chatqna-xeon-backend-server
  ipc: host
  restart: always
```

Once the services are up, open the following URL in the browser: http://{host_ip}:5174. By default, the UI runs on port 80 internally. If the developer prefers to use a different host port to access the frontend, it can be modified by port mapping in the `compose.yaml` file as shown below:

```yaml
  chatqna-xeon-conversation-ui-server:
    image: opea/chatqna-conversation-ui:latest
    ...
    ports:
      - "80:80"
```

Here is an example of running ChatQnA (default UI):

![project-screenshot](../../../../assets/img/chat_ui_response.png)

Here is an example of running ChatQnA with Conversational UI (React):

![project-screenshot](../../../../assets/img/conversation_ui_response.png)

### Validate Microservices

Note, when verifying the microservices by curl or API from remote client, please make sure the **ports** of the microservices are opened in the firewall of the cloud node.  
Follow the instructions to validate MicroServices.
For details on how to verify the correctness of the response, refer to [how-to-validate_service](../../hpu/gaudi/how_to_validate_service.md).

1. **TEI Embedding Service**
   Send a test request to the TEI Embedding Service to ensure it is running correctly:

   ```bash
   curl http://${host_ip}:6006/embed \
       -X POST \
       -d '{"inputs":"What is Deep Learning?"}' \
       -H 'Content-Type: application/json'
   ```

   If you receive a connection error, ensure that the service is running and the port 6006 is open in the firewall.

2. **Retriever Microservice**

   To consume the retriever microservice, you need to generate a mock embedding vector by Python script. The length of embedding vector
   is determined by the embedding model.
   Here we use the model `EMBEDDING_MODEL_ID="BAAI/bge-base-en-v1.5"`, which vector size is 768.

   Check the vector dimension of your embedding model, set `your_embedding` dimension equal to it.

   ```bash
   export your_embedding=$(python3 -c "import random; embedding = [random.uniform(-1, 1) for _ in range(768)]; print(embedding)")
   curl http://${host_ip}:7000/v1/retrieval \
     -X POST \
     -d "{\"text\":\"test\",\"embedding\":${your_embedding}}" \
     -H 'Content-Type: application/json'
   ```

   If the response indicates an invalid embedding vector, verify that the vector size matches the model's expected dimension.

3. **TEI Reranking Service**

   To test the TEI Reranking Service, use the following `curl` command:

   > Skip for ChatQnA without Rerank pipeline

   ```bash
   curl http://${host_ip}:8808/rerank \
       -X POST \
       -d '{"query":"What is Deep Learning?", "texts": ["Deep Learning is not...", "Deep learning is..."]}' \
       -H 'Content-Type: application/json'
   ```

4. **LLM Backend Service**

   In the first startup, this service will take more time to download, load and warm up the model. After it's finished, the service will be ready.

   Try the command below to check whether the LLM serving is ready.

   ```bash
   docker logs textgen-service-endpoint-openai 2>&1 | grep complete
   # If the service is ready, you will get the response like below.
   INFO:     Application startup complete.
   ```

   Then try the `cURL` command below to validate services.

You may also test your underlying LLM endpoint. E.g., if OpenRouter.ai:

```bash
curl https://openrouter.ai/api/v1/chat/completions \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer $OPENAI_API_KEY" \
  -d '{
  "model": ${LLM_MODEL_ID},
  "messages": [
    {
      "role": "user",
      "content": "What is the meaning of life?"
    }
  ]
}'
```

To test the OPEA service that is based on the above:

```bash
  curl http://${host_ip}:9000/v1/chat/completions \
    -X POST \
    -d '{"model": "${LLM_MODEL_ID}", "messages": [{"role": "user", "content": "What is Deep Learning?"}], "max_tokens":17}' \
    -H 'Content-Type: application/json'
```

5. **MegaService**

   Use the following `curl` command to test the MegaService:

   ```bash
    curl http://${host_ip}:8888/v1/chatqna -H "Content-Type: application/json" -d '{
          "messages": "What is the revenue of Nike in 2023?"
          }'
   ```

6. **Nginx Service**

   Use the following curl command to test the Nginx Service:

   ```bash
   curl http://${host_ip}:${NGINX_PORT}/v1/chatqna \
       -H "Content-Type: application/json" \
       -d '{"messages": "What is the revenue of Nike in 2023?"}'
   ```

7. **Dataprep Microservice(Optional) **

   If you want to update the default knowledge base, you can use the following commands:

   Update Knowledge Base via Local File [nke-10k-2023.pdf](https://github.com/opea-project/GenAIComps/blob/v1.1/comps/retrievers/redis/data/nke-10k-2023.pdf). Or
   click [here](https://raw.githubusercontent.com/opea-project/GenAIComps/v1.1/comps/retrievers/redis/data/nke-10k-2023.pdf) to download the file via any web browser.
   Or run this command to get the file on a terminal.

   ```bash
   wget https://raw.githubusercontent.com/opea-project/GenAIComps/v1.1/comps/retrievers/redis/data/nke-10k-2023.pdf
   ```

   Upload:

   ```bash
   curl -X POST "http://${host_ip}:6007/v1/dataprep/ingest" \
       -H "Content-Type: multipart/form-data" \
       -F "files=@./nke-10k-2023.pdf"
   ```

   This command updates a knowledge base by uploading a local file for processing. Update the file path according to your environment.

   Add Knowledge Base via HTTP Links:

   ```bash
   curl -X POST "http://${host_ip}:6007/v1/dataprep/ingest" \
       -H "Content-Type: multipart/form-data" \
       -F 'link_list=["https://opea.dev"]'
   ```

   This command updates a knowledge base by submitting a list of HTTP links for processing.

   Also, you are able to get the file list that you uploaded:

   ```bash
   curl -X POST "http://${host_ip}:6007/v1/dataprep/get" \
       -H "Content-Type: application/json"
   ```

   Then you will get the response JSON like this. Notice that the returned `name`/`id` of the uploaded link is `https://xxx.txt`.

   ```json
   [
     {
       "name": "nke-10k-2023.pdf",
       "id": "nke-10k-2023.pdf",
       "type": "File",
       "parent": ""
     },
     {
       "name": "https://opea.dev.txt",
       "id": "https://opea.dev.txt",
       "type": "File",
       "parent": ""
     }
   ]
   ```

   To delete the file/link you uploaded:

   The `file_path` here should be the `id` get from `/v1/dataprep/get` API.

   ```bash
   # delete link
   curl -X POST "http://${host_ip}:6007/v1/dataprep/delete" \
       -d '{"file_path": "https://opea.dev.txt"}' \
       -H "Content-Type: application/json"

   # delete file
   curl -X POST "http://${host_ip}:6007/v1/dataprep/delete" \
       -d '{"file_path": "nke-10k-2023.pdf"}' \
       -H "Content-Type: application/json"

   # delete all uploaded files and links
   curl -X POST "http://${host_ip}:6007/v1/dataprep/delete" \
       -d '{"file_path": "all"}' \
       -H "Content-Type: application/json"
   ```

### Profile Microservices

To further analyze MicroService Performance, users could follow the instructions to profile MicroServices.

#### 1. LLM Endpoint Service

Users can profile the performance of the endpoint service using standard HTTP/network profiling tools such as:

- cURL timing statistics
- Browser developer tools
- Network monitoring tools

Example using cURL with timing data:

```bash
curl -w "\nTime Statistics:\n-----------------\n\
DNS Lookup: %{time_namelookup}s\n\
TCP Connect: %{time_connect}s\n\
TLS Handshake: %{time_appconnect}s\n\
First Byte: %{time_starttransfer}s\n\
Total Time: %{time_total}s\n" \
-H "Content-Type: application/json" \
-H "Authorization: Bearer $OPENAI_API_KEY" \
-d '{
  "model": "${LLM_MODEL_ID}",
  "messages": [
    {
      "role": "user",
      "content": "What is machine learning?"
    }
  ]
}' \
${LLM_ENDPOINT}/v1/chat/completions
```

You can also use tools like `ab` (Apache Benchmark) for load testing:

```bash
ab -n 100 -c 10 -p payload.json -T 'application/json' \
  -H "Authorization: Bearer $OPENAI_API_KEY" \
  ${LLM_ENDPOINT}/v1/chat/completions
```

For detailed API latency monitoring, consider using:

- Grafana for visualization
- Prometheus for metrics collection
- OpenTelemetry for distributed tracing

## Conclusion

This guide should enable developer to deploy the default configuration or any of the other compose yaml files for different configurations. It also highlights the configurable parameters that can be set before deployment.
