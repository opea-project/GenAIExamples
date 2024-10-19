# AvatarChatbot Application

The AvatarChatbot service can be effortlessly deployed on either Intel Gaudi2 or Intel XEON Scalable Processors.

## AI Avatar Workflow

The AI Avatar example is implemented using both megaservices and the component-level microservices defined in [GenAIComps](https://github.com/opea-project/GenAIComps). The flow chart below shows the information flow between different megaservices and microservices for this example.

```mermaid
---
config:
  flowchart:
    nodeSpacing: 100
    rankSpacing: 100
    curve: linear
  themeVariables:
    fontSize: 42px
---
flowchart LR
    classDef blue fill:#ADD8E6,stroke:#ADD8E6,stroke-width:2px,fill-opacity:0.5
    classDef thistle fill:#D8BFD8,stroke:#ADD8E6,stroke-width:2px,fill-opacity:0.5
    classDef orange fill:#FBAA60,stroke:#ADD8E6,stroke-width:2px,fill-opacity:0.5
    classDef orchid fill:#C26DBC,stroke:#ADD8E6,stroke-width:2px,fill-opacity:0.5
    classDef invisible fill:transparent,stroke:transparent;
    style AvatarChatbot-Megaservice stroke:#000000

    subgraph AvatarChatbot-Megaservice["AvatarChatbot Megaservice"]
        direction LR
        ASR([ASR Microservice]):::blue
        LLM([LLM Microservice]):::blue
        TTS([TTS Microservice]):::blue
        animation([Animation Microservice]):::blue
    end
    subgraph UserInterface["User Interface"]
        direction LR
        invis1[ ]:::invisible
        USER1([User Audio Query]):::orchid
        USER2([User Image/Video Query]):::orchid
        UI([UI server<br>]):::orchid
    end
    GW([AvatarChatbot GateWay<br>]):::orange
    subgraph  
        direction LR
        X([OPEA Microservice]):::blue
        Y{{Open Source Service}}:::thistle
        Z([OPEA Gateway]):::orange
        Z1([UI]):::orchid
    end

    WHISPER{{Whisper service}}:::thistle
    TGI{{LLM service}}:::thistle
    T5{{Speecht5 service}}:::thistle
    WAV2LIP{{Wav2Lip service}}:::thistle

    %% Connections %%
    direction LR
    USER1 -->|1| UI
    UI -->|2| GW
    GW <==>|3| AvatarChatbot-Megaservice
    ASR ==>|4| LLM ==>|5| TTS ==>|6| animation

    direction TB
    ASR <-.->|3'| WHISPER
    LLM <-.->|4'| TGI
    TTS <-.->|5'| T5
    animation <-.->|6'| WAV2LIP

    USER2 -->|1| UI
    UI <-.->|6'| WAV2LIP
```
