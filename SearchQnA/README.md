# SearchQnA Application

Search Question and Answering (SearchQnA) harnesses the synergy between search engines, like Google Search, and large language models (LLMs) to enhance QA quality. While LLMs excel at general knowledge, they face limitations in accessing real-time or specific details due to their reliance on prior training data. By integrating a search engine, SearchQnA bridges this gap.

Operating within the LangChain framework, the Google Search QnA chatbot mimics human behavior by iteratively searching, selecting, and synthesizing information. Here's how it works:

- Diverse Search Queries: The system employs an LLM to generate multiple search queries from a single prompt, ensuring a wide range of query terms essential for comprehensive results.

- Parallel Search Execution: Queries are executed simultaneously, accelerating data collection. This concurrent approach enables the bot to 'read' multiple pages concurrently, a unique advantage of AI.

- Top Link Prioritization: Algorithms identify top K links for each query, and the bot scrapes full page content in parallel. This prioritization ensures the extraction of the most relevant information.

- Efficient Data Indexing: Extracted data is meticulously indexed into a dedicated vector store (Chroma DB), optimizing retrieval and comparison in subsequent steps.

- Contextual Result Matching: The bot matches original search queries with relevant documents stored in the vector store, presenting users with accurate and contextually appropriate results.

By integrating search capabilities with LLMs within the LangChain framework, this Google Search QnA chatbot delivers comprehensive and precise answers, akin to human search behavior.

The workflow falls into the following architecture:

![architecture](./assets/img/searchqna.png)

The SearchQnA example is implemented using the component-level microservices defined in [GenAIComps](https://github.com/opea-project/GenAIComps). The flow chart below shows the information flow between different microservices for this example.

```mermaid
%% SearchQnA Architecture Diagram
%% Horizontal layout with LLM Service below MegaService
%% Hugging Face services shown as yellow circles

flowchart LR
    %% Colors and Shapes %%
    classDef blue fill:#ADD8E6,stroke:#ADD8E6,stroke-width:2px,fill-opacity:0.5
    classDef yellow fill:#FBAA60,stroke:#FBAA60,stroke-width:2px,fill-opacity:0.5,width:200,height:200
    classDef orchid fill:#C26DBC,stroke:#C26DBC,stroke-width:2px,fill-opacity:0.5

    %% Main Flow %%
    subgraph UserInterface["User Interface"]
        a["User Input Query"]:::orchid
        UI["UI server<br/>(docker: searchqna-xeon-ui-server)"]:::orchid
    end

    GW["SearchQnA GateWay<br/>(docker: searchqna-xeon-backend-server)"]

    subgraph SearchQnA-MegaService["SearchQnA MegaService"]
        EM["Embedding MicroService<br/>(docker: embedding-server)"]:::blue
        RET["Web Retrieval MicroService<br/>(docker: web-retriever-server)"]:::blue
        RER["Rerank MicroService<br/>(docker: reranking-tei-xeon-server)"]:::blue
        LLM["LLM MicroService<br/>(docker: llm-textgen-server)"]:::blue
    end

    %% OPEA wrapped microservices services e.g. Hugging Face, Google/Langchain (yellow circles) %%
    TEI_EM(("TEI Embedding<br/>(docker: tei-embedding-server)")):::yellow
    R_RET(("Web Retriever<br/>(docker: web-retriever-server)")):::yellow
    TEI_RER(("TEI Reranking<br/>(docker: tei-reranking-server)")):::yellow
    
    %% LLM Service positioned below MegaService %%
    LLM_gen(("LLM Service<br/>(docker: tgi-service)")):::yellow
    
    %% Vertical positioning %%
    subgraph vertical[" "]
        direction TB
        SearchQnA-MegaService --> LLM_gen
    end

    %% Connections %%
    a --> UI --> GW
    GW <==> SearchQnA-MegaService
    EM ==> RET ==> RER ==> LLM
    EM <-.-> TEI_EM
    RET <-.-> R_RET
    RER <-.-> TEI_RER
    LLM <-.-> LLM_gen
```


## Deploy SearchQnA Service

The SearchQnA service can be effortlessly deployed on either Intel Gaudi2 or Intel Xeon Scalable Processors.

Currently we support two ways of deploying SearchQnA services with docker compose:

1. Start services using the docker image on `docker hub`:

   ```bash
   docker pull opea/searchqna:latest
   ```

2. Start services using the docker images `built from source`: [Guide](https://github.com/opea-project/GenAIExamples/tree/main/SearchQnA/docker_compose/)

### Setup Environment Variable

To set up environment variables for deploying SearchQnA services, follow these steps:

1. Set the required environment variables:

   ```bash
   # Example: host_ip="192.168.1.1"
   export host_ip="External_Public_IP"
   # Example: no_proxy="localhost, 127.0.0.1, 192.168.1.1"
   export no_proxy="Your_No_Proxy"
   export GOOGLE_CSE_ID="Your_CSE_ID"
   export GOOGLE_API_KEY="Your_Google_API_Key"
   export HUGGINGFACEHUB_API_TOKEN="Your_Huggingface_API_Token"
   ```

2. If you are in a proxy environment, also set the proxy-related environment variables:

   ```bash
   export http_proxy="Your_HTTP_Proxy"
   export https_proxy="Your_HTTPs_Proxy"
   ```

3. Set up other environment variables:

   ```bash
   source ./docker_compose/set_env.sh
   ```

### Deploy SearchQnA on Gaudi

If your version of `Habana Driver` < 1.16.0 (check with `hl-smi`), run the following command directly to start SearchQnA services. Find the corresponding [compose.yaml](./docker_compose/intel/hpu/gaudi/compose.yaml).

```bash
cd GenAIExamples/SearchQnA/docker_compose/intel/hpu/gaudi/
docker compose up -d
```

Refer to the [Gaudi Guide](./docker_compose/intel/hpu/gaudi/README.md) to build docker images from source.

### Deploy SearchQnA on Xeon

Find the corresponding [compose.yaml](./docker_compose/intel/cpu/xeon/compose.yaml).

```bash
cd GenAIExamples/SearchQnA/docker_compose/intel/cpu/xeon/
docker compose up -d
```

Refer to the [Xeon Guide](./docker_compose/intel/cpu/xeon/README.md) for more instructions on building docker images from source.

## Consume SearchQnA Service

Two ways of consuming SearchQnA Service:

1. Use cURL command on terminal

   ```bash
   curl http://${host_ip}:3008/v1/searchqna \
       -H "Content-Type: application/json" \
       -d '{
           "messages": "What is the latest news? Give me also the source link.",
           "stream": "True"
       }'
   ```

2. Access via frontend

   To access the frontend, open the following URL in your browser: http://{host_ip}:5173.

   By default, the UI runs on port 5173 internally.

## Troubleshooting

1. If you get errors like "Access Denied", [validate micro service](https://github.com/opea-project/GenAIExamples/tree/main/ChatQnA/docker_compose/intel/cpu/xeon/README.md#validate-microservices) first. A simple example:

   ```bash
   http_proxy=""
   curl http://${host_ip}:3001/embed \
       -X POST \
       -d '{"inputs":"What is Deep Learning?"}' \
       -H 'Content-Type: application/json'
   ```

2. (Docker only) If all microservices work well, check the port ${host_ip}:3008, the port may be allocated by other users, you can modify the `compose.yaml`.

3. (Docker only) If you get errors like "The container name is in use", change container name in `compose.yaml`.
