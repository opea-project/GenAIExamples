# HybridRAG Application

Enterprise AI systems require solutions that handle both structured data (databases, transactions, CSVs, JSON) and unstructured data (documents, images, audio). While traditional VectorRAG excels at semantic search across documents, it struggles with complex queries requiring global context or relationship-aware reasoning. HybridRAG application addresses these gaps by combining GraphRAG (knowledge graph-based retrieval) and VectorRAG (vector database retrieval) for enhanced accuracy and contextual relevance.

## Table of contents

1. [Architecture](#architecture)
2. [Deployment](#deployment)

## Architecture

The HybridRAG application is a customizable end-to-end workflow that leverages the capabilities of LLMs and RAG efficiently. HybridRAG architecture is shown below:

![architecture](./assets/img/hybridrag_retriever_architecture.png)

This application is modular as it leverages each component as a microservice(as defined in [GenAIComps](https://github.com/opea-project/GenAIComps)) that can scale independently. It comprises data preparation, embedding, retrieval, reranker(optional) and LLM microservices. All these microservices are stitched together by the HybridRAG megaservice that orchestrates the data through these microservices. The flow chart below shows the information flow between different microservices for this example.

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
    style HybridRAG-MegaService stroke:#000000

    %% Subgraphs %%
    subgraph HybridRAG-MegaService["HybridRAG MegaService "]
        direction LR
        EM([Embedding MicroService]):::blue
        RET([Retrieval MicroService]):::blue
        RER([Rerank MicroService]):::blue
        LLM([LLM MicroService]):::blue
        direction LR
        T2C([Text2Cypher MicroService]):::blue
        LLM([LLM MicroService]):::blue
    end
    subgraph UserInterface[" User Interface "]
        direction LR
        a([User Input Query]):::orchid
        UI([UI server<br>]):::orchid
    end



    TEI_RER{{Reranking service<br>}}
    TEI_EM{{Embedding service <br>}}
    VDB{{Vector DB<br><br>}}
    GDB{{Graph DB<br><br>}}
    R_RET{{Retriever service <br>}}
    DP([Data Preparation MicroService]):::blue
    S2G([Struct2Graph MicroService]):::blue
    LLM_gen{{LLM Service <br>}}
    GW([HybridRAG GateWay<br>]):::orange

    %% Questions interaction
    direction LR
    a[User Input Query] --> UI
    UI --> GW
    GW <==> HybridRAG-MegaService
    EM ==> RET
    RET ==> RER
    RER ==> LLM
    direction LR
    T2C ==> LLM


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

    direction TB
    %% Graph DB interaction
    T2C <-.->|d|GDB
    S2G <-.->|d|GDB

```

## Deployment

[HybridRAG deployment on Intel Gaudi](./docker_compose/intel/hpu/gaudi/README.md)

## Validated Configurations

| **Deploy Method** | **LLM Engine** | **LLM Model**                       | **Hardware** |
| ----------------- | -------------- | ----------------------------------- | ------------ |
| Docker Compose    | vLLM           | meta-llama/Meta-Llama-3-8B-Instruct | Intel Gaudi  |
