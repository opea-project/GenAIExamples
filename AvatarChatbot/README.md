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
    subgraph .
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

## Deploy AvatarChatbot Service

The AvatarChatbot service can be deployed on either Intel Gaudi2 AI Accelerator or Intel Xeon Scalable Processor.

### Deploy AvatarChatbot on Gaudi

Refer to the [Gaudi Guide](./docker_compose/intel/hpu/gaudi/README.md) for instructions on deploying AvatarChatbot on Gaudi, and on setting up an UI for the application.

### Deploy AvatarChatbot on Xeon

Refer to the [Xeon Guide](./docker_compose/intel/cpu/xeon/README.md) for instructions on deploying AvatarChatbot on Xeon.

## Supported Models

### ASR

The default model is [openai/whisper-small](https://huggingface.co/openai/whisper-small). It also supports all models in the Whisper family, such as `openai/whisper-large-v3`, `openai/whisper-medium`, `openai/whisper-base`, `openai/whisper-tiny`, etc.

To replace the model, please edit the `compose.yaml` and add the `command` line to pass the name of the model you want to use:

```yaml
services:
  whisper-service:
    ...
    command: --model_name_or_path openai/whisper-tiny
```

### TTS

The default model is [microsoft/SpeechT5](https://huggingface.co/microsoft/speecht5_tts). We currently do not support replacing the model. More models under the commercial license will be added in the future.

### Animation

The default model is [Rudrabha/Wav2Lip](https://github.com/Rudrabha/Wav2Lip) and [TencentARC/GFPGAN](https://github.com/TencentARC/GFPGAN). We currently do not support replacing the model. More models under the commercial license such as [OpenTalker/SadTalker](https://github.com/OpenTalker/SadTalker) will be added in the future.
