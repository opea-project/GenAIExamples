# ManufacturingAgentSuite Flow

```mermaid
flowchart LR
    Evidence["Plant-floor evidence"] --> Gateway["Gateway"]
    Gateway --> Mega["Manufacturing Megaservice"]
    Mega --> Registry["Route registry"]
    Registry --> Maintenance["maintenance"]
    Registry --> IQC["iqc"]
    Registry --> Changeover["changeover"]
    Registry --> WI["wi"]
    Registry --> Hazard["hazard"]
    Maintenance --> Eval["Evaluator"]
    IQC --> Eval
    Changeover --> Eval
    WI --> Eval
    Hazard --> Eval
    Eval --> Guardrails["Guardrails"]
    Guardrails --> Action["Bounded action card"]
```

OPEA component mapping:

| OPEA concept  | ManufacturingAgentSuite role                                     |
| ------------- | ---------------------------------------------------------------- |
| Gateway       | Plant evidence/API entry point                                   |
| Megaservice   | Route orchestration                                              |
| Dataprep      | Route-specific manuals, quality plans, policies, and checklists  |
| Retriever/RAG | Source-grounded evidence retrieval in the full reference package |
| Vector DB     | Qdrant profile in the full reference package                     |
| LLM service   | Pluggable LLM adapter; deterministic path for CI                 |
| Guardrails    | Blocked claims and human-confirmation gates                      |
| Evaluation    | Route scorecard                                                  |
