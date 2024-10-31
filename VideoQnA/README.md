# VideoQnA Application

VideoQnA is a framework that retrieves video based on provided user prompt. It uses only the video embeddings to perform vector similarity search in Intel's VDMS vector database and performs all operations on Intel Xeon CPU. The pipeline supports long form videos and time-based search.

VideoQnA is implemented on top of [GenAIComps](https://github.com/opea-project/GenAIComps), with the architecture flow chart shows below:

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
    style VideoQnA-MegaService stroke:#000000
    %% Subgraphs %%
    subgraph VideoQnA-MegaService["VideoQnA-MegaService"]
        direction LR
        EM([Embedding MicroService]):::blue
        RET([Retrieval MicroService]):::blue
        RER([Rerank MicroService]):::blue
        LVM([LVM MicroService]):::blue
    end
    subgraph User Interface
        direction LR
        a([User Input Query]):::orchid
        UI([UI server<br>]):::orchid
        Ingest([Ingest<br>]):::orchid
    end

    LOCAL_RER{{Reranking service<br>}}
    CLIP_EM{{Embedding service <br>}}
    VDB{{Vector DB<br><br>}}
    V_RET{{Retriever service <br>}}
    Ingest{{Ingest data <br>}}
    DP([Data Preparation<br>]):::blue
    LVM_gen{{LVM Service <br>}}
    GW([VideoQnA GateWay<br>]):::orange

    %% Data Preparation flow
    %% Ingest data flow
    direction LR
    Ingest[Ingest data] --> UI
    UI --> DP
    DP <-.-> CLIP_EM

    %% Questions interaction
    direction LR
    a[User Input Query] --> UI
    UI --> GW
    GW <==> VideoQnA-MegaService
    EM ==> RET
    RET ==> RER
    RER ==> LVM


    %% Embedding service flow
    direction LR
    EM <-.-> CLIP_EM
    RET <-.-> V_RET
    RER <-.-> LOCAL_RER
    LVM <-.-> LVM_gen

    direction TB
    %% Vector DB interaction
    V_RET <-.->VDB
    DP <-.->VDB
```

- This project implements a Retrieval-Augmented Generation (RAG) workflow using LangChain, Intel VDMS VectorDB, and Text Generation Inference, optimized for Intel Xeon Scalable Processors.
- Video Processing: Videos are converted into feature vectors using mean aggregation and stored in the VDMS vector store.
- Query Handling: When a user submits a query, the system performs a similarity search in the vector store to retrieve the best-matching videos.
- Contextual Inference: The retrieved videos are then sent to the Large Vision Model (LVM) for inference, providing supplemental context for the query.

## Deploy VideoQnA Service

The VideoQnA service can be effortlessly deployed on Intel Xeon Scalable Processors.

### Required Models

By default, the embedding and LVM models are set to a default value as listed below:

| Service   | Model                        |
| --------- | ---------------------------- |
| Embedding | openai/clip-vit-base-patch32 |
| LVM       | DAMO-NLP-SG/Video-LLaMA      |

### Deploy VideoQnA on Xeon

For full instruction of deployment, please check [Guide](docker_compose/intel/cpu/xeon/README.md)

Currently we support deploying VideoQnA services with docker compose, using the docker images `built from source`. Find the corresponding [compose.yaml](docker_compose/intel/cpu/xeon/compose.yaml).
