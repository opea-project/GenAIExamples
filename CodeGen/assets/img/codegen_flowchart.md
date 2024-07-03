flowchart TB
subgraph A[ ]
direction LR
CodeGen
Legend
end

    subgraph CodeGen
        A1[User] --> |Input query| B[CodeGen Gateway]
        B --> |Invoke| C([LLM])
        C --> |Depend on| D([Text Generation Inference])
        D --> |Post| E{{HuggingFace Endpoint}}
        E --> |Get| D
        C --> |Output| F[Response]

        subgraph Megaservice["Megaservice"]
            direction TB
            C
            D
            E
        end
    end

    subgraph Legend
        direction TB
        G([Microservice])
        H{{Server API}}
    end

```

```
