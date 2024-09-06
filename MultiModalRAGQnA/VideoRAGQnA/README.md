# VideoRAGQnA Application

Video RAG QnA is a framework that retrieves video based on provided user prompt. It uses only the video embeddings to perform vector similarity search in Intel's VDMS vector database and performs all operations on Intel Xeon CPU. The pipeline supports long form videos and time-based search.

VideoRAGQnA is implemented on top of [GenAIComps](https://github.com/opea-project/GenAIComps), with the architecture flow chart shows below:

```mermaid
---
config:
  flowchart:
    nodeSpacing: 100
    rankSpacing: 100
    curve: linear
  theme: base
  themeVariables:
    fontSize: 42px
---
flowchart LR
    %% Colors %%
    classDef blue fill:#ADD8E6,stroke:#ADD8E6,stroke-width:2px,fill-opacity:0.5
    classDef orange fill:#FBAA60,stroke:#ADD8E6,stroke-width:2px,fill-opacity:0.5
    classDef orchid fill:#C26DBC,stroke:#ADD8E6,stroke-width:2px,fill-opacity:0.5
    classDef invisible fill:transparent,stroke:transparent;
    style VideoRAGQnA-MegaService stroke:#000000
    %% Subgraphs %%
    subgraph VideoRAGQnA-MegaService["VideoRAGQnA-MegaService"]
        direction LR
        EM([Embedding <br>]):::blue
        RET([Retrieval <br>]):::blue
        RER([Rerank <br>]):::blue
        LLM([LLM <br>]):::blue
    end
    subgraph User Interface
        direction TB
        a([User Input Query]):::orchid
        UI([UI server<br>]):::orchid
        Ingest([Ingest<br>]):::orchid
    end
    subgraph VideoRAGQnA GateWay
        direction LR
        invisible1[ ]:::invisible
        GW([VideoRAGQnA GateWay<br>]):::orange
    end
    subgraph .
        X([OPEA Micsrservice]):::blue
        Y{{Open Source Service}}
        Z([OPEA Gateway]):::orange
        Z1([UI]):::orchid
    end

    LOCAL_RER{{Reranking service<br>}}
    CLIP_EM{{Embedding service <br>}}
    VDB{{Vector DB<br><br>}}
    V_RET{{Retriever service <br>}}
    Ingest{{Ingest data <br>}}
    DP([Data Preparation<br>]):::blue
    LVM_gen{{LLM Service <br>}}

    %% Data Preparation flow
    %% Ingest data flow
    direction LR
    Ingest[Ingest data] -->|a| DP
    DP <-.->|b| CLIP_EM

    %% Questions interaction
    direction LR
    a[User Input Query] -->|1| UI
    UI -->|2| GW
    GW <==>|3| VideoRAGQnA-MegaService
    EM ==>|4| RET
    RET ==>|5| RER
    RER ==>|6| LLM


    %% Embedding service flow
    direction TB
    EM <-.->|3'| CLIP_EM
    RET <-.->|4'| V_RET
    RER <-.->|5'| LOCAL_RER
    LLM <-.->|6'| LVM_gen

    direction TB
    %% Vector DB interaction
    V_RET <-.->|d|VDB
    DP <-.->|d|VDB
```

This VideoRAGQnA use case performs RAG using LangChain, Intel VDMS VectorDB and Text Generation Inference on Intel XEON Scalable Processors.

## Deploy VideoRAGQnA Service

The VideoRAGQnA service can be effortlessly deployed on Intel XEON Scalable Processors.

### Required Models

By default, the embedding and LVM models are set to a default value as listed below:

| Service   | Model                        |
| --------- | ---------------------------- |
| Embedding | openai/clip-vit-base-patch32 |
| LVM       | DAMO-NLP-SG/Video-LLaMA      |

### Deploy VideoRAGQnA on Xeon

For full instruction of deployment, please check [Guide](docker/xeon/README.md)

Currently we support deploying VideoRAGQnA services with docker compose, using the docker images `built from source`. Find the corresponding [compose.yaml](./docker/xeon/compose.yaml).
