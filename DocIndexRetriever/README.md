# DocRetriever Application

DocRetriever is the most widely adopted use case for leveraging the different methodologies to match user query against a set of free-text records. DocRetriever is essential to RAG system, which bridges the knowledge gap by dynamically fetching relevant information from external sources, ensuring that responses generated remain factual and current. The core of this architecture are vector databases, which are instrumental in enabling efficient and semantic retrieval of information. These databases store data as vectors, allowing RAG to swiftly access the most pertinent documents or data points based on semantic similarity.

The DocIndexRetriever example is implemented using the component-level microservices defined in [GenAIComps](https://github.com/opea-project/GenAIComps). The flow chart below shows the information flow between different microservices for this example.

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
    style DocIndexRetriever-MegaService stroke:#000000

    %% Subgraphs %%
    subgraph DocIndexRetriever-MegaService["DocIndexRetriever MegaService "]
        direction LR
        EM([Embedding MicroService]):::blue
        RET([Retrieval MicroService]):::blue
        RER([Rerank MicroService]):::blue
    end
    subgraph UserInput[" User Input "]
        direction LR
        a([User Input Query]):::orchid
        Ingest([Ingest data]):::orchid
    end

    DP([Data Preparation MicroService]):::blue
    TEI_RER{{Reranking service<br>}}
    TEI_EM{{Embedding service <br>}}
    VDB{{Vector DB<br><br>}}
    R_RET{{Retriever service <br>}}
    GW([DocIndexRetriever GateWay<br>]):::orange

    %% Data Preparation flow
    %% Ingest data flow
    direction LR
    Ingest[Ingest data] --> DP
    DP <-.-> TEI_EM

    %% Questions interaction
    direction LR
    a[User Input Query] --> GW
    GW <==> DocIndexRetriever-MegaService
    EM ==> RET
    RET ==> RER

    %% Embedding service flow
    direction LR
    EM <-.-> TEI_EM
    RET <-.-> R_RET
    RER <-.-> TEI_RER

    direction TB
    %% Vector DB interaction
    R_RET <-.-> VDB
    DP <-.-> VDB

```

## We provided DocRetriever with different deployment infra

- [docker xeon version](docker_compose/intel/cpu/xeon/README.md) => minimum endpoints, easy to setup
- [docker gaudi version](docker_compose/intel/hpu/gaudi/README.md) => with extra tei_gaudi endpoint, faster

## We allow users to set retriever/reranker hyperparams via requests

Example usage:

```python
url = "http://{host_ip}:{port}/v1/retrievaltool".format(host_ip=host_ip, port=port)
payload = {
    "messages": query,
    "k": 5,  # retriever top k
    "top_n": 2,  # reranker top n
}
response = requests.post(url, json=payload)
```
