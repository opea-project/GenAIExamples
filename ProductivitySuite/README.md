# Productivity Suite Application

Productivity Suite, a tool designed to streamline your workflow and boost productivity! Our application leverages the power of OPEA microservices to deliver a comprehensive suite of features tailored to meet the diverse needs of modern enterprises.

The ProductivitySuite example is implemented using both megaservices and the component-level microservices defined in [GenAIComps](https://github.com/opea-project/GenAIComps). The flow chart below shows the information flow between different megaservices and microservices for this example. Prompt Registry and Chat History microservices save prompt and chat history from the ChatQnA MegaService only into the database.

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
    subgraph DocSum-MegaService["DocSum MegaService "]
        direction LR
        LLM_D([LLM MicroService]):::blue
    end
    subgraph CodeGen-MegaService["CodeGen MegaService "]
        direction LR
        LLM_CG([LLM MicroService]):::blue
    end
    subgraph FaqGen-MegaService["FaqGen MegaService "]
        direction LR
        LLM_F([LLM MicroService]):::blue
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
    LLM_gen_C{{LLM Service <br>}}
    GW_C([ChatQnA GateWay<br>]):::orange
    LLM_gen_D{{LLM Service <br>}}
    GW_D([DocSum GateWay<br>]):::orange
    LLM_gen_CG{{LLM Service <br>}}
    GW_CG([CodeGen GateWay<br>]):::orange
    LLM_gen_F{{LLM Service <br>}}
    GW_F([FaqGen GateWay<br>]):::orange
    PR([Prompt Registry MicroService]):::blue
    CH([Chat History MicroService]):::blue
    MDB{{Mongo DB<br><br>}}


    %% Data Preparation flow
    %% Ingest data flow
    direction LR
    Ingest[Ingest data] --> UI
    UI --> DP
    DP <-.-> TEI_EM

    %% Questions interaction
    direction LR
    a[User Input Query] --> UI
    UI <--> GW_C
    GW_C <==> ChatQnA-MegaService
    EM ==> RET
    RET ==> RER
    RER ==> LLM


    %% Embedding service flow
    direction LR
    EM <-.-> TEI_EM
    RET <-.-> R_RET
    RER <-.-> TEI_RER
    LLM <-.-> LLM_gen_C

    direction LR
    %% Vector DB interaction
    R_RET <-.-> VDB
    DP <-.-> VDB

    %% Questions interaction
    direction LR
    UI --> GW_D
    GW_D <==> DocSum-MegaService


    %% Embedding service flow
    direction LR
    LLM_D <-.-> LLM_gen_D

    %% Questions interaction
    direction LR
    UI --> GW_CG
    GW_CG <==> CodeGen-MegaService


    %% Embedding service flow
    direction LR
    LLM_CG <-.-> LLM_gen_CG

    %% Questions interaction
    direction LR
    UI --> GW_F
    GW_F <==> FaqGen-MegaService


    %% Embedding service flow
    direction LR
    LLM_F <-.-> LLM_gen_F

    %% Questions interaction
    direction LR
    UI --> PR

    %% Embedding service flow
    direction LR
    PR <-.-> MDB

    %% Questions interaction
    direction LR
    UI --> CH

    %% Embedding service flow
    direction LR
    CH <-.-> MDB

```

---

## 🛠️ Key Features

### 💬 Chat with Documents

Engage in intelligent conversations with your documents using our advanced **Retrieval-Augmented Generation (RAG)** capabilities. Ask questions, receive relevant information, and gain insights from your documents in real-time!

### 📄 Content Summarization

Summarize lengthy documents or articles, enabling you to grasp key takeaways quickly. Save time and effort with our intelligent summarization feature!

### ❓ FAQ Generation

Effortlessly create comprehensive FAQs based on your documents. Ensure your users have access to the information they need with minimal effort!

### 💻 Code Generation

Boost your coding productivity by providing a description of the functionality you require. Our application generates corresponding code snippets, saving you valuable time and effort!

### 🎛️ User Context Management

Maintain a seamless workflow by managing your user's context within the application. Our context management system keeps track of documents and chat history for a personalized experience.

### 🔐 Identity and Access Management

Utilizes the open-source platform **Keycloak** for single sign-on identity and access management. This ensures secure and convenient access to your productivity tools.

---

## 📚 Setup Guide

- **[Keycloak Configuration Guide](./docker_compose/intel/cpu/xeon/keycloak_setup_guide.md)**: Instructions to set up Keycloak for identity and access management.
- **[Xeon Guide](./docker_compose/intel/cpu/xeon/README.md)**: Instructions to build Docker images from source and run the application via Docker Compose.
