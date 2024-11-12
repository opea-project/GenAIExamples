# ChatQnA Application

Chatbots are the most widely adopted use case for leveraging the powerful chat and reasoning capabilities of large language models (LLMs). The retrieval augmented generation (RAG) architecture is quickly becoming the industry standard for chatbots development. It combines the benefits of a knowledge base (via a vector store) and generative models to reduce hallucinations, maintain up-to-date information, and leverage domain-specific knowledge.

RAG bridges the knowledge gap by dynamically fetching relevant information from external sources, ensuring that responses generated remain factual and current. The core of this architecture are vector databases, which are instrumental in enabling efficient and semantic retrieval of information. These databases store data as vectors, allowing RAG to swiftly access the most pertinent documents or data points based on semantic similarity.

## Deploy ChatQnA Service

The ChatQnA service can be effortlessly deployed on Intel Gaudi2, Intel Xeon Scalable Processors and Nvidia GPU.

Two types of ChatQnA pipeline are supported now: `ChatQnA with/without Rerank`. And the `ChatQnA without Rerank` pipeline (including Embedding, Retrieval, and LLM) is offered for Xeon customers who can not run rerank service on HPU yet require high performance and accuracy.

Quick Start Deployment Steps:

1. Set up the environment variables.
2. Run Docker Compose.
3. Consume the ChatQnA Service.

Note: If you do not have docker installed you can run this script to install docker : `bash docker_compose/install_docker.sh`

### Quick Start: 1.Setup Environment Variable

To set up environment variables for deploying ChatQnA services, follow these steps:

1. Set the required environment variables:

   ```bash
   # Example: host_ip="192.168.1.1"
   export host_ip="External_Public_IP"
   # Example: no_proxy="localhost, 127.0.0.1, 192.168.1.1"
   export no_proxy="Your_No_Proxy"
   export HUGGINGFACEHUB_API_TOKEN="Your_Huggingface_API_Token"
   ```

2. If you are in a proxy environment, also set the proxy-related environment variables:

   ```bash
   export http_proxy="Your_HTTP_Proxy"
   export https_proxy="Your_HTTPs_Proxy"
   ```

3. Set up other environment variables:

   > Notice that you can only choose **one** command below to set up envs according to your hardware. Other that the port numbers may be set incorrectly.

   ```bash
   # on Gaudi
   source ./docker_compose/intel/hpu/gaudi/set_env.sh
   # on Xeon
   source ./docker_compose/intel/cpu/xeon/set_env.sh
   # on Nvidia GPU
   source ./docker_compose/nvidia/gpu/set_env.sh
   ```

### Quick Start: 2.Run Docker Compose

Select the compose.yaml file that matches your hardware.

CPU example:

```bash
cd GenAIExamples/ChatQnA/docker_compose/intel/cpu/xeon/
# cd GenAIExamples/ChatQnA/docker_compose/intel/hpu/gaudi/
# cd GenAIExamples/ChatQnA/docker_compose/nvidia/gpu/
docker compose up -d
```

It will automatically download the docker image on `docker hub`:

```bash
docker pull opea/chatqna:latest
docker pull opea/chatqna-ui:latest
```

In following cases, you could build docker image from source by yourself.

- Failed to download the docker image.

- If you want to use a specific version of Docker image.

Please refer to the 'Build Docker Images' in [Guide](docker_compose/intel/cpu/xeon/README.md).

### QuickStart: 3.Consume the ChatQnA Service

```bash
curl http://${host_ip}:8888/v1/chatqna \
    -H "Content-Type: application/json" \
    -d '{
        "messages": "What is the revenue of Nike in 2023?"
    }'
```

## Architecture and Deploy details

ChatQnA architecture shows below:
![architecture](./assets/img/chatqna_architecture.png)

The ChatQnA example is implemented using the component-level microservices defined in [GenAIComps](https://github.com/opea-project/GenAIComps). The flow chart below shows the information flow between different microservices for this example.

```mermaid
---
config:
  flowchart:
    nodeSpacing: 400
    rankSpacing: 100
    curve: linear
  themeVariables:
    fontSize: 50px
---
flowchart LR
    %% Colors %%
    classDef blue fill:#ADD8E6,stroke:#ADD8E6,stroke-width:2px,fill-opacity:0.5
    classDef orange fill:#FBAA60,stroke:#ADD8E6,stroke-width:2px,fill-opacity:0.5
    classDef orchid fill:#C26DBC,stroke:#ADD8E6,stroke-width:2px,fill-opacity:0.5
    classDef invisible fill:transparent,stroke:transparent;
    style ChatQnA-MegaService stroke:#000000

    %% Subgraphs %%
    subgraph ChatQnA-MegaService["ChatQnA MegaService "]
        direction LR
        EM([Embedding MicroService]):::blue
        RET([Retrieval MicroService]):::blue
        RER([Rerank MicroService]):::blue
        LLM([LLM MicroService]):::blue
    end
    subgraph UserInterface[" User Interface "]
        direction LR
        a([User Input Query]):::orchid
        Ingest([Ingest data]):::orchid
        UI([UI server<br>]):::orchid
    end



    TEI_RER{{Reranking service<br>}}
    TEI_EM{{Embedding service <br>}}
    VDB{{Vector DB<br><br>}}
    R_RET{{Retriever service <br>}}
    DP([Data Preparation MicroService]):::blue
    LLM_gen{{LLM Service <br>}}
    GW([ChatQnA GateWay<br>]):::orange

    %% Data Preparation flow
    %% Ingest data flow
    direction LR
    Ingest[Ingest data] --> UI
    UI --> DP
    DP <-.-> TEI_EM

    %% Questions interaction
    direction LR
    a[User Input Query] --> UI
    UI --> GW
    GW <==> ChatQnA-MegaService
    EM ==> RET
    RET ==> RER
    RER ==> LLM


    %% Embedding service flow
    direction LR
    EM <-.-> TEI_EM
    RET <-.-> R_RET
    RER <-.-> TEI_RER
    LLM <-.-> LLM_gen

    direction TB
    %% Vector DB interaction
    R_RET <-.->|d|VDB
    DP <-.->|d|VDB

```

This ChatQnA use case performs RAG using LangChain, Redis VectorDB and Text Generation Inference on [Intel Gaudi2](https://www.intel.com/content/www/us/en/products/details/processors/ai-accelerators/gaudi-overview.html) or [Intel Xeon Scalable Processors](https://www.intel.com/content/www/us/en/products/details/processors/xeon.html).
In the below, we provide a table that describes for each microservice component in the ChatQnA architecture, the default configuration of the open source project, hardware, port, and endpoint.

Gaudi default compose.yaml
| MicroService | Open Source Project | HW | Port | Endpoint |
| ------------ | ------------------- | ----- | ---- | -------------------- |
| Embedding | Langchain | Xeon | 6000 | /v1/embaddings |
| Retriever | Langchain, Redis | Xeon | 7000 | /v1/retrieval |
| Reranking | Langchain, TEI | Gaudi | 8000 | /v1/reranking |
| LLM | Langchain, TGI | Gaudi | 9000 | /v1/chat/completions |
| Dataprep | Redis, Langchain | Xeon | 6007 | /v1/dataprep |

### Required Models

By default, the embedding, reranking and LLM models are set to a default value as listed below:

| Service   | Model                     |
| --------- | ------------------------- |
| Embedding | BAAI/bge-base-en-v1.5     |
| Reranking | BAAI/bge-reranker-base    |
| LLM       | Intel/neural-chat-7b-v3-3 |

Change the `xxx_MODEL_ID` in `docker_compose/xxx/set_env.sh` for your needs.

For customers with proxy issues, the models from [ModelScope](https://www.modelscope.cn/models) are also supported in ChatQnA. Refer to [this readme](docker_compose/intel/cpu/xeon/README.md) for details.

### Deploy ChatQnA on Gaudi

Find the corresponding [compose.yaml](./docker_compose/intel/hpu/gaudi/compose.yaml).

```bash
cd GenAIExamples/ChatQnA/docker_compose/intel/hpu/gaudi/
docker compose up -d
```

Refer to the [Gaudi Guide](./docker_compose/intel/hpu/gaudi/README.md) to build docker images from source.

### Deploy ChatQnA on Xeon

Find the corresponding [compose.yaml](./docker_compose/intel/cpu/xeon/compose.yaml).

```bash
cd GenAIExamples/ChatQnA/docker_compose/intel/cpu/xeon/
docker compose up -d
```

Refer to the [Xeon Guide](./docker_compose/intel/cpu/xeon/README.md) for more instructions on building docker images from source.

### Deploy ChatQnA on NVIDIA GPU

```bash
cd GenAIExamples/ChatQnA/docker_compose/nvidia/gpu/
docker compose up -d
```

Refer to the [NVIDIA GPU Guide](./docker_compose/nvidia/gpu/README.md) for more instructions on building docker images from source.

### Deploy ChatQnA into Kubernetes on Xeon & Gaudi with GMC

Refer to the [Kubernetes Guide](./kubernetes/intel/README_gmc.md) for instructions on deploying ChatQnA into Kubernetes on Xeon & Gaudi with GMC.

### Deploy ChatQnA into Kubernetes on Xeon & Gaudi without GMC

Refer to the [Kubernetes Guide](./kubernetes/intel/README.md) for instructions on deploying ChatQnA into Kubernetes on Xeon & Gaudi without GMC.

### Deploy ChatQnA into Kubernetes using Helm Chart

Install Helm (version >= 3.15) first. Refer to the [Helm Installation Guide](https://helm.sh/docs/intro/install/) for more information.

Refer to the [ChatQnA helm chart](https://github.com/opea-project/GenAIInfra/tree/main/helm-charts/chatqna/README.md) for instructions on deploying ChatQnA into Kubernetes on Xeon & Gaudi.

### Deploy ChatQnA on AI PC

Refer to the [AI PC Guide](./docker_compose/intel/cpu/aipc/README.md) for instructions on deploying ChatQnA on AI PC.

### Deploy ChatQnA on Red Hat OpenShift Container Platform (RHOCP)

Refer to the [Intel Technology enabling for Openshift readme](https://github.com/intel/intel-technology-enabling-for-openshift/blob/main/workloads/opea/chatqna/README.md) for instructions to deploy ChatQnA prototype on RHOCP with [Red Hat OpenShift AI (RHOAI)](https://www.redhat.com/en/technologies/cloud-computing/openshift/openshift-ai).

## Consume ChatQnA Service with RAG

### Check Service Status

Before consuming ChatQnA Service, make sure the TGI/vLLM service is ready (which takes up to 2 minutes to start).

```bash
# TGI example
docker logs tgi-service | grep Connected
```

Consume ChatQnA service until you get the TGI response like below.

```log
2024-09-03T02:47:53.402023Z  INFO text_generation_router::server: router/src/server.rs:2311: Connected
```

### Upload RAG Files (Optional)

To chat with retrieved information, you need to upload a file using `Dataprep` service.

Here is an example of `Nike 2023` pdf.

```bash
# download pdf file
wget https://raw.githubusercontent.com/opea-project/GenAIComps/main/comps/retrievers/redis/data/nke-10k-2023.pdf
# upload pdf file with dataprep
curl -X POST "http://${host_ip}:6007/v1/dataprep" \
    -H "Content-Type: multipart/form-data" \
    -F "files=@./nke-10k-2023.pdf"
```

### Consume Chat Service

Two ways of consuming ChatQnA Service:

1. Use cURL command on terminal

   ```bash
   curl http://${host_ip}:8888/v1/chatqna \
       -H "Content-Type: application/json" \
       -d '{
           "messages": "What is the revenue of Nike in 2023?"
       }'
   ```

2. Access via frontend

   To access the frontend, open the following URL in your browser: `http://{host_ip}:5173`

   By default, the UI runs on port 5173 internally.

   If you choose conversational UI, use this URL: `http://{host_ip}:5174`

## Troubleshooting

1. If you get errors like "Access Denied", [validate micro service](https://github.com/opea-project/GenAIExamples/tree/main/ChatQnA/docker_compose/intel/cpu/xeon/README.md#validate-microservices) first. A simple example:

   ```bash
   http_proxy="" curl ${host_ip}:6006/embed -X POST  -d '{"inputs":"What is Deep Learning?"}' -H 'Content-Type: application/json'
   ```

2. (Docker only) If all microservices work well, check the port ${host_ip}:8888, the port may be allocated by other users, you can modify the `compose.yaml`.

3. (Docker only) If you get errors like "The container name is in use", change container name in `compose.yaml`.

## Monitoring OPEA Service with Prometheus and Grafana dashboard

OPEA microservice deployment can easily be monitored through Grafana dashboards in conjunction with Prometheus data collection. Follow the [README](https://github.com/opea-project/GenAIEval/blob/main/evals/benchmark/grafana/README.md) to setup Prometheus and Grafana servers and import dashboards to monitor the OPEA service.

![chatqna dashboards](./assets/img/chatqna_dashboards.png)
![tgi dashboard](./assets/img/tgi_dashboard.png)
