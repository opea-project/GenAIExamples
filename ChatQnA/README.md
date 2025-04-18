# ChatQnA Application

Chatbots are the most widely adopted use case for leveraging the powerful chat and reasoning capabilities of large language models (LLMs). The retrieval augmented generation (RAG) architecture is quickly becoming the industry standard for chatbot development. It combines the benefits of a knowledge base (via a vector store) and generative models to reduce hallucinations, maintain up-to-date information, and leverage domain-specific knowledge.

RAG bridges the knowledge gap by dynamically fetching relevant information from external sources, ensuring that the response generated remains factual and current. Vector databases are at the core of this architecture, enabling efficient retrieval of semantically relevant information. These databases store data as vectors, allowing RAG to swiftly access the most pertinent documents or data points based on semantic similarity.

## Table of contents

1. [Architecture](#architecture)
2. [Deployment Options](#deployment-options)
3. [Monitoring and Tracing](#monitor-and-tracing)

## Architecture

The ChatQnA application is a customizable end-to-end workflow that leverages the capabilities of LLMs and RAG efficiently. ChatQnA architecture is shown below:

![architecture](./assets/img/chatqna_architecture.png)

This application is modular as it leverages each component as a microservice(as defined in [GenAIComps](https://github.com/opea-project/GenAIComps)) that can scale independently. It comprises data preparation, embedding, retrieval, reranker(optional) and LLM microservices. All these microservices are stitched together by the ChatQnA megaservice that orchestrates the data through these microservices. The flow chart below shows the information flow between different microservices for this example.

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

## Deployment Options

The table below lists currently available deployment options. They outline in detail the implementation of this example on selected hardware.

| Category                | Deployment Option            | Description                                                                                                                                                                                                                                                                          |
| ----------------------- | ---------------------------- | ------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------ |
| On-premise Deployments  | Docker compose               | [ChatQnA deployment on Xeon](./docker_compose/intel/cpu/xeon)                                                                                                                                                                                                                        |
|                         |                              | [ChatQnA deployment on AI PC](./docker_compose/intel/cpu/aipc)                                                                                                                                                                                                                       |
|                         |                              | [ChatQnA deployment on Gaudi](./docker_compose/intel/hpu/gaudi)                                                                                                                                                                                                                      |
|                         |                              | [ChatQnA deployment on Nvidia GPU](./docker_compose/nvidia/gpu)                                                                                                                                                                                                                      |
|                         |                              | [ChatQnA deployment on AMD ROCm](./docker_compose/amd/gpu/rocm)                                                                                                                                                                                                                      |
|                         | Kubernetes                   | [Helm Charts](./kubernetes/helm)                                                                                                                                                                                                                                                     |
| Cloud Service Providers | AWS                          | [Terraform deployment on 4th Gen Intel Xeon with Intel AMX using meta-llama/Meta-Llama-3-8B-Instruct ](https://github.com/intel/terraform-intel-aws-vm/tree/main/examples/gen-ai-xeon-opea-chatqna)                                                                                  |
|                         |                              | [Terraform deployment on 4th Gen Intel Xeon with Intel AMX using TII Falcon2-11B](https://github.com/intel/terraform-intel-aws-vm/tree/main/examples/gen-ai-xeon-opea-chatqna-falcon11B)                                                                                             |
|                         | GCP                          | [Terraform deployment on 5th Gen Intel Xeon with Intel AMX(support Confidential AI by using Intel® TDX](https://github.com/intel/terraform-intel-gcp-vm/tree/main/examples/gen-ai-xeon-opea-chatqna)                                                                                |
|                         | Azure                        | [Terraform deployment on 4th/5th Gen Intel Xeon with Intel AMX & Intel TDX](https://github.com/intel/terraform-intel-azure-linux-vm/tree/main/examples/azure-gen-ai-xeon-opea-chatqna-tdx)                                                                                           |
|                         | Intel Tiber AI Cloud         | Coming Soon                                                                                                                                                                                                                                                                          |
|                         | Any Xeon based Ubuntu system | [ChatQnA Ansible Module for Ubuntu 20.04](https://github.com/intel/optimized-cloud-recipes/tree/main/recipes/ai-opea-chatqna-xeon) .Use this if you are not using Terraform and have provisioned your system either manually or with another tool, including directly on bare metal. |

## Monitor and Tracing

Follow [OpenTelemetry OPEA Guide](https://opea-project.github.io/latest/tutorial/OpenTelemetry/OpenTelemetry_OPEA_Guide.html) to understand how to use OpenTelemetry tracing and metrics in OPEA.  
For ChatQnA specific tracing and metrics monitoring, follow [OpenTelemetry on ChatQnA](https://opea-project.github.io/latest/tutorial/OpenTelemetry/deploy/ChatQnA.html) section.

## FAQ Generation Application

FAQ Generation Application leverages the power of large language models (LLMs) to revolutionize the way you interact with and comprehend complex textual data. By harnessing cutting-edge natural language processing techniques, our application can automatically generate comprehensive and natural-sounding frequently asked questions (FAQs) from your documents, legal texts, customer queries, and other sources. We merged the FaqGen into the ChatQnA example, which utilize LangChain to implement FAQ Generation and facilitate LLM inference using Text Generation Inference on Intel Xeon and Gaudi2 processors.
