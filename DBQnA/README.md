# DBQnA Application

Experience a revolutionary way to interact with your database using our DBQnA app! Harnessing the power of OPEA microservices, our application seamlessly translates natural language queries into SQL and delivers real-time database results, all designed to optimize workflows and enhance productivity for modern enterprises.

---

```mermaid
flowchart LR
    %% Colors %%
    classDef blue fill:#ADD8E6,stroke:#ADD8E6,stroke-width:2px,fill-opacity:0.7
    classDef orange fill:#FBAA60,stroke:#ADD8E6,stroke-width:2px,fill-opacity:0.7
    classDef orchid fill:#DA70D6,stroke:#1E90FF,stroke-width:2px,fill-opacity:0.7
    classDef invisible fill:transparent,stroke:transparent;
    style Text2SQL-MegaService stroke:#000000

    %% Subgraphs %%
    subgraph Text2SQL-MegaService["Text-to-SQL MegaService "]
        direction LR
        LLM([LLM MicroService]):::invisible
    end
    subgraph UserInterface[" User Interface "]
        direction LR
        a([User Input Query]):::orchid
        UI([UI server<br>]):::orchid
    end

    LLM_gen{{LLM Service <br>}}
    POSTGRES_DB{{POSGRES DATABASE <br>}}
    GW([Text-to-SQL GateWay<br>]):::orange


    %% Questions interaction
    direction LR
    a[User Input Query] --> UI
    UI --> GW
    GW <==> Text2SQL-MegaService


    %% Text-to-SQL service flow
    direction TB
    LLM <-.-> POSTGRES_DB
    direction LR
    LLM <-.-> LLM_gen

```

---

## 🛠️ Key Features

### 💬 SQL Query Generation

The key feature of DBQnA app is that it converts a user's natural language query into an SQL query and automatically executes the generated SQL query on the database to return the relevant results. BAsically ask questions to database, receive corresponding SQL query and real-time query execution output, all without needing any SQL knowledge.

---

## 📚 Setup Guide

- **[Xeon Guide](./docker_compose/intel/cpu/xeon/README.md)**: Instructions to build Docker images from source and run the application via Docker Compose.
