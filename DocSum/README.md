# Document Summarization Application

Large Language Models (LLMs) have revolutionized the way we interact with text. These models can be used to create summaries of news articles, research papers, technical documents, legal documents, multimedia documents, and other types of documents. Suppose you have a set of documents (PDFs, Notion pages, customer questions, multimedia files, etc.) and you want to summarize the content. In this example use case, we utilize LangChain to implement summarization strategies and facilitate LLM inference using Text Generation Inference.

## Table of contents

1. [Architecture](#architecture)
2. [Deployment Options](#deployment-options)

## Architecture

The architecture of the Document Summarization Application is illustrated below:

![Architecture](./assets/img/docsum_architecture.png)

The DocSum example is implemented using the component-level microservices defined in [GenAIComps](https://github.com/opea-project/GenAIComps). The flow chart below shows the information flow between different microservices for this example.

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
    style DocSum-MegaService stroke:#000000



    %% Subgraphs %%
    subgraph DocSum-MegaService["DocSum MegaService "]
        direction LR
        M2T([Multimedia2text MicroService]):::blue
        LLM([LLM MicroService]):::blue
    end
    subgraph UserInterface[" User Interface "]
        direction LR
        a([User Input Query]):::orchid
        UI([UI server<br>]):::orchid
    end


    A2T_SRV{{Audio2Text service<br>}}
    V2A_SRV{{Video2Audio service<br>}}
    WSP_SRV{{whisper service<br>}}
    GW([DocSum GateWay<br>]):::orange


    %% Questions interaction
    direction LR
    a[User Document for Summarization] --> UI
    UI --> GW
    GW <==> DocSum-MegaService
    M2T ==> LLM

    %% Embedding service flow
    direction LR
    M2T .-> V2A_SRV
    M2T <-.-> A2T_SRV <-.-> WSP_SRV
    V2A_SRV .-> A2T_SRV

```

## Deployment Options

The table below lists currently available deployment options. They outline in detail the implementation of this example on selected hardware.

| Category               | Deployment Option      | Description                                                    |
| ---------------------- | ---------------------- | -------------------------------------------------------------- |
| On-premise Deployments | Docker Compose (Xeon)  | [DocSum deployment on Xeon](./docker_compose/intel/cpu/xeon)   |
|                        | Docker Compose (Gaudi) | [DocSum deployment on Gaudi](./docker_compose/intel/hpu/gaudi) |
|                        | Docker Compose (ROCm)  | [DocSum deployment on AMD ROCm](./docker_compose/amd/gpu/rocm) |
