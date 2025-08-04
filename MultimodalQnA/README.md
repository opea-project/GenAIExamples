# MultimodalQnA Application

Multimodal question answering is the process of extracting insights from documents that contain a mix of text, images, videos, audio, and PDFs. It involves reasoning over both textual and non-textual content to answer user queries.

The MultimodalQnA framework enables this by leveraging the BridgeTower model, which encodes visual and textual data into a shared semantic space. During ingestion, it processes content and stores embeddings in a vector database. At query time, relevant multimodal segments are retrieved and passed to a vision-language model to generate responses in text or audio form.

## Table of Contents

1. [Architecture](#architecture)
2. [Deployment Options](#deployment-options)
3. [Monitoring and Tracing](./README_miscellaneous.md)

## Architecture

The MultimodalQnA application is an end-to-end workflow designed for multimodal question answering across video, image, audio, and PDF inputs. The architecture is illustrated below:

![architecture](./assets/img/MultimodalQnA.png)

The MultimodalQnA example is implemented using the component-level microservices defined in [GenAIComps](https://github.com/opea-project/GenAIComps), the MultimodalQnA Flow Chart shows below:

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
    style MultimodalQnA-MegaService stroke:#000000
    %% Subgraphs %%
    subgraph MultimodalQnA-MegaService["MultimodalQnA-MegaService"]
        direction LR
        EM([Embedding <br>]):::blue
        RET([Retrieval <br>]):::blue
        LVM([LVM <br>]):::blue
    end
    subgraph UserInterface[" User Interface "]
        direction LR
        a([User Input Query]):::orchid
        Ingest([Ingest data]):::orchid
        UI([UI server<br>]):::orchid
    end

    ASR{{Whisper service <br>}}
    TEI_EM{{Embedding service <br>}}
    VDB{{Vector DB<br><br>}}
    R_RET{{Retriever service <br>}}
    DP([Data Preparation<br>]):::blue
    LVM_gen{{LVM Service <br>}}
    GW([MultimodalQnA GateWay<br>]):::orange
    TTS{{SpeechT5 service <br>}}

    %% Data Preparation flow
    %% Ingest data flow
    direction LR
    Ingest[Ingest data] --> UI
    UI -->DP
    DP <-.-> TEI_EM

    %% Questions interaction
    direction LR
    a[User Input Query] --> UI
    UI --> GW
    GW <==> MultimodalQnA-MegaService
    EM ==> RET
    RET ==> LVM

    %% Embedding service flow
    direction LR
    EM <-.-> TEI_EM
    RET <-.-> R_RET
    LVM <-.-> LVM_gen

    direction TB
    %% Vector DB interaction
    R_RET <-.->VDB
    DP <-.->VDB

    %% Audio speech recognition used for translating audio queries to text
    GW <-.-> ASR

    %% Generate spoken responses with text-to-speech using the SpeechT5 model
    GW <-.-> TTS

```

This MultimodalQnA use case performs Multimodal-RAG using LangChain, Redis VectorDB and Text Generation Inference on [Intel Gaudi2](https://www.intel.com/content/www/us/en/products/details/processors/ai-accelerators/gaudi.html), [Intel Xeon Scalable Processors](https://www.intel.com/content/www/us/en/products/details/processors/xeon.html) and [AMD EPYC™ Processors](https://www.amd.com/en/products/processors/server/epyc.html), and we invite contributions from other hardware vendors to expand the example.

## Deployment Options

The table below lists currently available deployment options. They outline in detail the implementation of this example on selected hardware.

![MultimodalQnA-pdf-query-example-screenshot](./assets/img/vector-store.png)

## Validated Configurations

| **Deploy Method** | **LLM Engine** | **LLM Model**                     | **Database**  | **Hardware** |
| ----------------- | -------------- | --------------------------------- | ------------- | ------------ |
| Docker Compose    | LLAVA          | llava-hf/llava-1.5-7b-hf          | Milvus, Redis | Intel Xeon   |
| Docker Compose    | LLAVA          | llava-hf/llava-v1.6-vicuna-13b-hf | Redis         | Intel Gaudi  |
| Docker Compose    | LLAVA          | llava-hf/llava-1.5-7b-hf          | Milvus, Redis | AMD EPYC     |
| Docker Compose    | TGI, vLLM      | Xkev/Llama-3.2V-11B-cot           | Redis         | AMD ROCm     |

## Validated Configurations

| **Deploy Method** | **LLM Engine** | **LLM Model**                     | **Database**  | **Hardware** |
| ----------------- | -------------- | --------------------------------- | ------------- | ------------ |
| Docker Compose    | LLAVA          | llava-hf/llava-1.5-7b-hf          | Milvus, Redis | Intel Xeon   |
| Docker Compose    | LLAVA          | llava-hf/llava-v1.6-vicuna-13b-hf | Redis         | Intel Gaudi  |
| Docker Compose    | LLAVA          | llava-hf/llava-1.5-7b-hf          | Milvus, Redis | AMD EPYC     |
| Docker Compose    | TGI, vLLM      | Xkev/Llama-3.2V-11B-cot           | Redis         | AMD ROCm     |
