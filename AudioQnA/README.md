# AudioQnA Application

AudioQnA is an example that demonstrates the integration of Generative AI (GenAI) models for performing question-answering (QnA) on audio files, with the added functionality of Text-to-Speech (TTS) for generating spoken responses. The example showcases how to convert audio input to text using Automatic Speech Recognition (ASR), generate answers to user queries using a language model, and then convert those answers back to speech using Text-to-Speech (TTS).

## Table of Contents

1. [Architecture](#architecture)
2. [Deployment Options](#deployment-options)

## Architecture

The AudioQnA example is implemented using the component-level microservices defined in [GenAIComps](https://github.com/opea-project/GenAIComps). The flow chart below shows the information flow between different microservices for this example.

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
    style AudioQnA-MegaService stroke:#000000

    %% Subgraphs %%
    subgraph AudioQnA-MegaService["AudioQnA MegaService "]
        direction LR
        ASR([ASR MicroService]):::blue
        LLM([LLM MicroService]):::blue
        TTS([TTS MicroService]):::blue
    end
    subgraph UserInterface[" User Interface "]
        direction LR
        a([User Input Query]):::orchid
        UI([UI server<br>]):::orchid
    end



    WSP_SRV{{whisper service<br>}}
    SPC_SRV{{speecht5 service <br>}}
    LLM_gen{{LLM Service <br>}}
    GW([AudioQnA GateWay<br>]):::orange


    %% Questions interaction
    direction LR
    a[User Audio Query] --> UI
    UI --> GW
    GW <==> AudioQnA-MegaService
    ASR ==> LLM
    LLM ==> TTS

    %% Embedding service flow
    direction LR
    ASR <-.-> WSP_SRV
    LLM <-.-> LLM_gen
    TTS <-.-> SPC_SRV

```

## Deployment Options

The table below lists currently available deployment options. They outline in detail the implementation of this example on selected hardware.

| Category               | Deployment Option | Description                                                      |
| ---------------------- | ----------------- | ---------------------------------------------------------------- |
| On-premise Deployments | Docker compose    | [AudioQnA deployment on Xeon](./docker_compose/intel/cpu/xeon)   |
|                        |                   | [AudioQnA deployment on Gaudi](./docker_compose/intel/hpu/gaudi) |
|                        |                   | [AudioQnA deployment on AMD ROCm](./docker_compose/amd/gpu/rocm) |
|                        | Kubernetes        | [Helm Charts](./kubernetes/helm)                                 |
