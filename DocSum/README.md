# Document Summarization Application

Large Language Models (LLMs) have revolutionized the way we interact with text. These models can be used to create summaries of news articles, research papers, technical documents, legal documents, multimedia documents, and other types of documents. Suppose you have a set of documents (PDFs, Notion pages, customer questions, multimedia files, etc.) and you want to summarize the content. In this example use case, we utilize LangChain to implement summarization strategies and facilitate LLM inference using Text Generation Inference.

![Architecture](./assets/img/docsum_architecture.png)

## Deploy Document Summarization Service

The Document Summarization service can be effortlessly deployed on either Intel Gaudi2 or Intel Xeon Scalable Processors.
Based on whether you want to use Docker or Kubernetes, follow the instructions below. Currently we support deploying Document Summarization services with docker compose.

### Required Models

Default model is "Intel/neural-chat-7b-v3-3". Change "LLM_MODEL_ID" environment variable in commands below if you want to use another model.

```bash
export LLM_MODEL_ID="Intel/neural-chat-7b-v3-3"
```

When using gated models, you also need to provide [HuggingFace token](https://huggingface.co/docs/hub/security-tokens) to "HUGGINGFACEHUB_API_TOKEN" environment variable.

### Setup Environment Variable

To set up environment variables for deploying Document Summarization services, follow these steps:

1. Set the required environment variables:

   ```bash
   # Example: host_ip="192.168.1.1"
   export host_ip="External_Public_IP"
   # Example: no_proxy="localhost, 127.0.0.1, 192.168.1.1"
   export no_proxy="Your_No_Proxy"
   export HUGGINGFACEHUB_API_TOKEN="Your_Huggingface_API_Token"
   ```

2. If you are in a proxy environment, also set the proxy-related environment variables:

   ```bash
   export http_proxy="Your_HTTP_Proxy"
   export https_proxy="Your_HTTPs_Proxy"
   ```

3. Set up other environment variables:

   ```bash
   source GenAIExamples/DocSum/docker_compose/set_env.sh
   ```

### Deploy using Docker

#### Deploy on Gaudi

Follow the instructions provided in the [Gaudi Guide](./docker_compose/intel/hpu/gaudi/README.md) to build Docker images from source. Once the images are built, run the following command to start the services:

```bash
cd GenAIExamples/DocSum/docker_compose/intel/hpu/gaudi/
docker compose -f compose.yaml up -d
```

Find the corresponding [compose.yaml](./docker_compose/intel/hpu/gaudi/compose.yaml).

> Notice: Currently only the **Habana Driver 1.16.x** is supported for Gaudi.

#### Deploy on Xeon

Follow the instructions provided in the [Xeon Guide](./docker_compose/intel/cpu/xeon/README.md) to build Docker images from source. Once the images are built, run the following command to start the services:

```bash
cd GenAIExamples/DocSum/docker_compose/intel/cpu/xeon/
docker compose -f compose.yaml up -d
```

Find the corresponding [compose.yaml](./docker_compose/intel/cpu/xeon/compose.yaml).

### Deploy DocSum on Kubernetes using Helm Chart

Refer to the [DocSum helm chart](./kubernetes/helm/README.md) for instructions on deploying DocSum on Kubernetes.

### Workflow of the deployed Document Summarization Service

The DocSum example is implemented using the component-level microservices defined in [GenAIComps](https://github.com/opea-project/GenAIComps). The flow chart below shows the information flow between different microservices for this example.

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
    style DocSum-MegaService stroke:#000000



    %% Subgraphs %%
    subgraph DocSum-MegaService["DocSum MegaService "]
        direction LR
        M2T([Multimedia2text MicroService]):::blue
        LLM([LLM MicroService]):::blue
    end
    subgraph UserInterface[" User Interface "]
        direction LR
        a([User Input Query]):::orchid
        UI([UI server<br>]):::orchid
    end


    A2T_SRV{{Audio2Text service<br>}}
    V2A_SRV{{Video2Audio service<br>}}
    WSP_SRV{{whisper service<br>}}
    GW([DocSum GateWay<br>]):::orange


    %% Questions interaction
    direction LR
    a[User Document for Summarization] --> UI
    UI --> GW
    GW <==> DocSum-MegaService
    M2T ==> LLM

    %% Embedding service flow
    direction LR
    M2T .-> V2A_SRV
    M2T <-.-> A2T_SRV <-.-> WSP_SRV
    V2A_SRV .-> A2T_SRV

```

## Consume Document Summarization Service

Two ways of consuming Document Summarization Service:

1. Use cURL command on terminal

   Text:

   ```bash
   curl -X POST http://${host_ip}:8888/v1/docsum \
        -H "Content-Type: application/json" \
        -d '{"type": "text", "messages": "Text Embeddings Inference (TEI) is a toolkit for deploying and serving open source text embeddings and sequence classification models. TEI enables high-performance extraction for the most popular models, including FlagEmbedding, Ember, GTE and E5."}'

   # Use English mode (default).
   curl http://${host_ip}:8888/v1/docsum \
       -H "Content-Type: multipart/form-data" \
       -F "type=text" \
       -F "messages=Text Embeddings Inference (TEI) is a toolkit for deploying and serving open source text embeddings and sequence classification models. TEI enables high-performance extraction for the most popular models, including FlagEmbedding, Ember, GTE and E5." \
       -F "max_tokens=32" \
       -F "language=en" \
       -F "stream=true"

   # Use Chinese mode.
   curl http://${host_ip}:8888/v1/docsum \
       -H "Content-Type: multipart/form-data" \
       -F "type=text" \
       -F "messages=2024年9月26日，北京——今日，英特尔正式发布英特尔® 至强® 6性能核处理器（代号Granite Rapids），为AI、数据分析、科学计算等计算密集型业务提供卓越性能。" \
       -F "max_tokens=32" \
       -F "language=zh" \
       -F "stream=true"

   # Upload file
   curl http://${host_ip}:8888/v1/docsum \
      -H "Content-Type: multipart/form-data" \
      -F "type=text" \
      -F "messages=" \
      -F "files=@/path to your file (.txt, .docx, .pdf)" \
      -F "max_tokens=32" \
      -F "language=en" \
      -F "stream=true"
   ```

   > Audio and Video file uploads are not supported in docsum with curl request, please use the Gradio-UI.

   Audio:

   ```bash
   curl -X POST http://${host_ip}:8888/v1/docsum \
      -H "Content-Type: application/json" \
      -d '{"type": "audio", "messages": "UklGRigAAABXQVZFZm10IBIAAAABAAEARKwAAIhYAQACABAAAABkYXRhAgAAAAEA"}'

   curl http://${host_ip}:8888/v1/docsum \
      -H "Content-Type: multipart/form-data" \
      -F "type=audio" \
      -F "messages=UklGRigAAABXQVZFZm10IBIAAAABAAEARKwAAIhYAQACABAAAABkYXRhAgAAAAEA" \
      -F "max_tokens=32" \
      -F "language=en" \
      -F "stream=true"
   ```

   Video:

   ```bash
   curl -X POST http://${host_ip}:8888/v1/docsum \
      -H "Content-Type: application/json" \
      -d '{"type": "video", "messages": "convert your video to base64 data type"}'

   curl http://${host_ip}:8888/v1/docsum \
      -H "Content-Type: multipart/form-data" \
      -F "type=video" \
      -F "messages=convert your video to base64 data type" \
      -F "max_tokens=32" \
      -F "language=en" \
      -F "stream=true"
   ```

2. Access via frontend

   To access the frontend, open the following URL in your browser: http://{host_ip}:5173.

   By default, the UI runs on port 5173 internally.

## Troubleshooting

1. If you get errors like "Access Denied", [validate micro service](https://github.com/opea-project/GenAIExamples/tree/main/DocSum/docker_compose/intel/cpu/xeon/README.md#validate-microservices) first. A simple example:

   ```bash
   curl http://${host_ip}:8008/generate \
     -X POST \
     -d '{"inputs":"What is Deep Learning?","parameters":{"max_tokens":17, "do_sample": true}}' \
     -H 'Content-Type: application/json'
   ```

2. (Docker only) If all microservices work well, check the port ${host_ip}:8888, the port may be allocated by other users, you can modify the `compose.yaml`.

3. (Docker only) If you get errors like "The container name is in use", change container name in `compose.yaml`.
