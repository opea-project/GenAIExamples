# AudioQnA Application

AudioQnA is an example that demonstrates the integration of Generative AI (GenAI) models for performing question-answering (QnA) on audio files, with the added functionality of Text-to-Speech (TTS) for generating spoken responses. The example showcases how to convert audio input to text using Automatic Speech Recognition (ASR), generate answers to user queries using a language model, and then convert those answers back to speech using Text-to-Speech (TTS).

The AudioQnA example is implemented using the component-level microservices defined in [GenAIComps](https://github.com/opea-project/GenAIComps). The flow chart below shows the information flow between different microservices for this example.

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
    style AudioQnA-MegaService stroke:#000000

    %% Subgraphs %%
    subgraph AudioQnA-MegaService["AudioQnA MegaService "]
        direction LR
        ASR([ASR MicroService]):::blue
        LLM([LLM MicroService]):::blue
        TTS([TTS MicroService]):::blue
    end
    subgraph UserInterface[" User Interface "]
        direction LR
        a([User Input Query]):::orchid
        UI([UI server<br>]):::orchid
    end



    WSP_SRV{{whisper service<br>}}
    SPC_SRV{{speecht5 service <br>}}
    LLM_gen{{LLM Service <br>}}
    GW([AudioQnA GateWay<br>]):::orange


    %% Questions interaction
    direction LR
    a[User Audio Query] --> UI
    UI --> GW
    GW <==> AudioQnA-MegaService
    ASR ==> LLM
    LLM ==> TTS

    %% Embedding service flow
    direction LR
    ASR <-.-> WSP_SRV
    LLM <-.-> LLM_gen
    TTS <-.-> SPC_SRV

```

## Deploy AudioQnA Service

The AudioQnA service can be deployed on either Intel Gaudi2 or Intel Xeon Scalable Processor.

### Deploy AudioQnA on Gaudi

Refer to the [Gaudi Guide](./docker_compose/intel/hpu/gaudi/README.md) for instructions on deploying AudioQnA on Gaudi.

### Deploy AudioQnA on Xeon

Refer to the [Xeon Guide](./docker_compose/intel/cpu/xeon/README.md) for instructions on deploying AudioQnA on Xeon.

## Deploy using Helm Chart

Refer to the [AudioQnA helm chart](./kubernetes/helm/README.md) for instructions on deploying AudioQnA on Kubernetes.

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
