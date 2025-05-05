# Translation Application

The Translation example demonstrates the implementation of language translation using OPEA component-level microservices.

## Table of contents

1. [Architecture](#architecture)
2. [Deployment Options](#deployment-options)

## Architecture

The architecture of the Translation Application is illustrated below:

![architecture](./assets/img/translation_architecture.png)

The Translation example is implemented using the component-level microservices defined in [GenAIComps](https://github.com/opea-project/GenAIComps). The flow chart below shows the information flow between different microservices for this example.

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
    style Translation-MegaService stroke:#000000

    %% Subgraphs %%
    subgraph Translation-MegaService["Translation MegaService "]
        direction LR
        LLM([LLM MicroService]):::blue
    end
    subgraph UserInterface[" User Interface "]
        direction LR
        a([User Input Query]):::orchid
        UI([UI server<br>]):::orchid
    end


    LLM_gen{{LLM Service <br>}}
    GW([Translation GateWay<br>]):::orange
    NG([Nginx MicroService]):::blue


    %% Questions interaction
    direction LR
    a[User Input Query] --> UI
    a[User Input Query] --> |Need Proxy Server|NG
    NG --> UI
    UI --> GW
    GW <==> Translation-MegaService


    %% Embedding service flow
    direction LR
    LLM <-.-> LLM_gen

```

This Translation use case performs Language Translation Inference across multiple platforms. Currently, we provide the example for [Intel Gaudi2](https://www.intel.com/content/www/us/en/products/details/processors/ai-accelerators/gaudi-overview.html) and [Intel Xeon Scalable Processors](https://www.intel.com/content/www/us/en/products/details/processors/xeon.html), and we invite contributions from other hardware vendors to expand OPEA ecosystem.

## Deployment Options

The table below lists the available deployment options and their implementation details for different hardware platforms.

| Platform     | Deployment Method | Link                                                              |
| ------------ | ----------------- | ----------------------------------------------------------------- |
| Intel Xeon   | Docker compose    | [Deployment on Xeon](./docker_compose/intel/cpu/xeon/README.md)   |
| Intel Gaudi2 | Docker compose    | [Deployment on Gaudi](./docker_compose/intel/hpu/gaudi/README.md) |
| AMD ROCm     | Docker compose    | [Deployment on AMD Rocm](./docker_compose/amd/gpu/rocm/README.md) |
