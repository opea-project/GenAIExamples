# SearchQnA Application

Search Question and Answering (SearchQnA) harnesses the synergy between search engines, like Google Search, and large language models (LLMs) to enhance QA quality. While LLMs excel at general knowledge, they face limitations in accessing real-time or specific details due to their reliance on prior training data. By integrating a search engine, SearchQnA bridges this gap.

Operating within the LangChain framework, the Google Search QnA chatbot mimics human behavior by iteratively searching, selecting, and synthesizing information. Here's how it works:

- Diverse Search Queries: The system employs an LLM to generate multiple search queries from a single prompt, ensuring a wide range of query terms essential for comprehensive results.

- Parallel Search Execution: Queries are executed simultaneously, accelerating data collection. This concurrent approach enables the bot to 'read' multiple pages concurrently, a unique advantage of AI.

- Top Link Prioritization: Algorithms identify top K links for each query, and the bot scrapes full page content in parallel. This prioritization ensures the extraction of the most relevant information.

- Efficient Data Indexing: Extracted data is meticulously indexed into a dedicated vector store (Chroma DB), optimizing retrieval and comparison in subsequent steps.

- Contextual Result Matching: The bot matches original search queries with relevant documents stored in the vector store, presenting users with accurate and contextually appropriate results.

By integrating search capabilities with LLMs within the LangChain framework, this Google Search QnA chatbot delivers comprehensive and precise answers, akin to human search behavior.

## Table of contents

1. [Architecture](#architecture)
2. [Deployment Options](#deployment-options)

## Architecture

The architecture of the SearchQnA Application is illustrated below:

![architecture](./assets/img/searchqna.png)

The SearchQnA example is implemented using the component-level microservices defined in [GenAIComps](https://github.com/opea-project/GenAIComps). The flow chart below shows the information flow between different microservices for this example.

```mermaid
%% Orange are microservices from third parties that are 'wrapped' as OPEA components.
flowchart LR
    User["User"] --> Nginx["Nginx<br>searchqna-nginx-server"]
    Nginx --> UI["UI<br>searchqna-ui-server"] & Gateway & User
    UI --> Nginx
    Gateway --> Nginx & Embedding
    Embedding --> Retriever
    Retriever --> Reranker
    Reranker --> LLM
    LLM --> Gateway
    LLM <-.-> TGI_Service["LLM<br>tgi-service"]
    Embedding <-.-> TEI_Embedding["TEI Embedding<br>tei-embedding-server"]
    Reranker <-.-> TEI_Reranker["TEI Reranker<br>tei-reranking-server"]

     TEI_Embedding:::ext
     TEI_Reranker:::ext
     TGI_Service:::ext

 subgraph MegaService["MegaService"]
        LLM["LLM<br>llm-textgen-server"]
        Reranker["Reranker<br>reranking-tei-server"]
        Retriever["Retriever<br>web-retriever-server"]
        Embedding["Embedding<br>embedding-server"]
  end
 subgraph Backend["searchqna-backend-server"]
    direction TB
        MegaService
        Gateway["Backend Endpoint"]
 end
    classDef default fill:#fff,stroke:#000,color:#000
    classDef ext fill:#f9cb9c,stroke:#000,color:#000
    style MegaService margin-top:20px,margin-bottom:20px
```

This SearchQnA use case performs Search-augmented Question Answering across multiple platforms. Currently, we provide the example for Intel® Gaudi® 2, Intel® Xeon® Scalable Processors and AMD EPYC™ Processors, and we invite contributions from other hardware vendors to expand OPEA ecosystem.

## Deployment Options

The table below lists the available deployment options and their implementation details for different hardware platforms.

| Category               | Deployment Option      | Description                                                                 |
| ---------------------- | ---------------------- | --------------------------------------------------------------------------- |
| On-premise Deployments | Docker Compose (Xeon)  | [SearchQnA deployment on Xeon](./docker_compose/intel/cpu/xeon/README.md)   |
|                        | Docker Compose (Gaudi) | [SearchQnA deployment on Gaudi](./docker_compose/intel/hpu/gaudi/README.md) |
|                        | Docker Compose (EPYC)  | [SearchQnA deployment on AMD EPYC](./docker_compose/amd/cpu/epyc/README.md) |
|                        | Docker Compose (ROCm)  | [SearchQnA deployment on AMD ROCm](./docker_compose/amd/gpu/rocm/README.md) |

## Validated Configurations

| **Deploy Method** | **LLM Engine** | **LLM Model**             | **Hardware** |
| ----------------- | -------------- | ------------------------- | ------------ |
| Docker Compose    | vLLM, TGI      | Intel/neural-chat-7b-v3-3 | Intel Gaudi  |
| Docker Compose    | vLLM, TGI      | Intel/neural-chat-7b-v3-3 | Intel Xeon   |
| Docker Compose    | vLLM, TGI      | Intel/neural-chat-7b-v3-3 | AMD EPYC     |
| Docker Compose    | vLLM, TGI      | Intel/neural-chat-7b-v3-3 | AMD ROCm     |
| Helm Charts       | vLLM, TGI      | Intel/neural-chat-7b-v3-3 | Intel Gaudi  |
| Helm Charts       | vLLM, TGI      | Intel/neural-chat-7b-v3-3 | Intel Xeon   |
