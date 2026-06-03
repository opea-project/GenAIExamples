# Edge Craft Retrieval-Augmented Generation Application

Edge Craft RAG (EC-RAG) is a customizable, tunable and production-ready
Retrieval-Augmented Generation system for edge solutions. It is designed to
curate the RAG pipeline to meet hardware requirements at edge with guaranteed
quality and performance.

## What's New

1. Support Agent component and enable deep_search agent
2. Optimize pipeline execution performance with asynchronous api
3. Support session list display in UI
4. Support vllm-based embedding service

## Table of contents

1. [Architecture](#architecture)
2. [Deployment Options](#deployment-options)

## Architecture

The architecture of the Edge Craft Retrieval-Augmented Generation Application is illustrated below:

```mermaid
flowchart TD
    EC_RAG_UI[EC-RAG UI]
    EC_RAG_Gateway[EC-RAG Gateway]
    Vector_DB[(Vector DB)]
    LLM[[LLM]]

    %% Mega Service 组
    subgraph MegaService["Mega Service"]
        subgraph EC_RAG_Pipeline["EC-RAG Pipeline"]
            %% Indexing 线
            subgraph Indexing["Indexing"]
                Preprocessor[Preprocessor]
                Node_Parser[Node Parser]
                Indexer[Indexer]
            end

            %% Inference 线
            subgraph Inference["Inference"]
                Retriever[Retriever]
                Postprocessor[Postprocessor]
                Generator[Generator]
            end

            Knowledge_Base[(Knowledge Base)]
            Benchmark_Hook[Benchmark Hook]
        end
    end

    %% UI <-> Gateway
    EC_RAG_UI <--> EC_RAG_Gateway

    %% UI -> Pipeline (Configure/Indexing)
    EC_RAG_UI -. Configure .-> EC_RAG_Pipeline
    EC_RAG_UI -->|Indexing| EC_RAG_Pipeline

    %% Gateway -> Pipeline (Inference)
    EC_RAG_Gateway -->|Inference| MegaService

    Preprocessor --> Node_Parser
    Node_Parser --> Indexer
    Indexer --> Knowledge_Base

    Retriever --> Postprocessor
    Postprocessor --> Generator

    Knowledge_Base --> Vector_DB
    Indexer --> Vector_DB

    Generator -->|Inference| LLM
    Retriever -. Configure .-> LLM
    Postprocessor -. Configure .-> LLM

    %% Benchmark Hook
    Benchmark_Hook -.-> Generator

    classDef external fill:#f9f,stroke:#333
    classDef storage fill:#bbf,stroke:#66c
    classDef process fill:#dfd,stroke:#090
    classDef config stroke-dasharray: 5 5

    class EC_RAG_UI,EC_RAG_Gateway,LLM external
    class Vector_DB,Knowledge_Base storage
    class Preprocessor,Node_Parser,Indexer,Retriever,Postprocessor,Generator,Benchmark_Hook process
    class Configure,config config
```

## Deployment Options

The table below lists the available deployment options and their implementation details for different hardware platforms.

| Platform  | Deployment Method | Link                                                          |
| --------- | ----------------- | ------------------------------------------------------------- |
| Intel Arc | Docker compose    | [Deployment on Arc](./docker_compose/intel/gpu/arc/README.md) |

## Validated Configurations

| **Deploy Method** | **LLM Engine** | **LLM Model** | **Hardware** |
| ----------------- | -------------- | ------------- | ------------ |
| Docker Compose    | vLLM           | Qwen3-8B      | Intel Arc    |
