# Document Summarization Application

Large Language Models (LLMs) have revolutionized the way we interact with text. These models can be used to create summaries of news articles, research papers, technical documents, legal documents and other types of text. Suppose you have a set of documents (PDFs, Notion pages, customer questions, etc.) and you want to summarize the content. In this example use case, we utilize LangChain to implement summarization strategies and facilitate LLM inference using Text Generation Inference.

The architecture for document summarization will be illustrated/described below:

![Architecture](./assets/img/docsum_architecture.png)

![Workflow](./assets/img/docsum_workflow.png)

## Deploy Document Summarization Service

The Document Summarization service can be effortlessly deployed on either Intel Gaudi2 or Intel XEON Scalable Processors.
Based on whether you want to use Docker or Kubernetes, follow the instructions below.

Currently we support two ways of deploying Document Summarization services with docker compose:

1. Start services using the docker image on `docker hub`:

   ```bash
   docker pull opea/docsum:latest
   ```

2. Start services using the docker images `built from source`: [Guide](./docker)

### Required Models

We set default model as "Intel/neural-chat-7b-v3-3", change "LLM_MODEL_ID" in "set_env.sh" if you want to use other models.

```
export LLM_MODEL_ID="Intel/neural-chat-7b-v3-3"
```

If use gated models, you also need to provide [huggingface token](https://huggingface.co/docs/hub/security-tokens) to "HUGGINGFACEHUB_API_TOKEN" environment variable.

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
   source ./docker/set_env.sh
   ```

### Deploy using Docker

#### Deploy on Gaudi

Find the corresponding [compose.yaml](./docker/gaudi/compose.yaml).

```bash
cd GenAIExamples/DocSum/docker/gaudi/
docker compose -f compose.yaml up -d
```

> Notice: Currently only the **Habana Driver 1.16.x** is supported for Gaudi.

Refer to the [Gaudi Guide](./docker/gaudi/README.md) to build docker images from source.

#### Deploy on Xeon

Find the corresponding [compose.yaml](./docker/xeon/compose.yaml).

```bash
cd GenAIExamples/DocSum/docker/xeon/
docker compose up -d
```

Refer to the [Xeon Guide](./docker/xeon/README.md) for more instructions on building docker images from source.

### Deploy using Kubernetes with GMC

Refer to [Kubernetes deployment](./kubernetes/README.md)

### Deploy using Kubernetes without GMC

Refer to [Kubernetes deployment](./kubernetes/manifests/README.md)

### Deploy DocSum into Kubernetes using Helm Chart

Install Helm (version >= 3.15) first. Refer to the [Helm Installation Guide](https://helm.sh/docs/intro/install/) for more information.

Refer to the [DocSum helm chart](https://github.com/opea-project/GenAIInfra/tree/main/helm-charts/docsum) for instructions on deploying DocSum into Kubernetes on Xeon & Gaudi.

### Workflow of the deployed Document Summarization Service

The workflow of the Document Summarization Service, from user's input query to the application's output response, is as follows:

```mermaid
flowchart LR
    subgraph DocSum
        direction LR
        A[User] <--> |Input query| B[DocSum Gateway]
        B <--> |Post| Megaservice
        subgraph Megaservice["Megaservice"]
            direction TB
            C([ Microservice : llm-docsum-tgi <br>9000]) -. Post .-> D{{TGI Service<br>8008}}
        end
        Megaservice --> |Output| E[Response]
    end
    subgraph Legend
        X([Micsrservice])
        Y{{Service from industry peers}}
        Z[Gateway]
    end
```

## Consume Document Summarization Service

Two ways of consuming Document Summarization Service:

1. Use cURL command on terminal

   ```bash
   curl http://${host_ip}:8888/v1/docsum \
       -H "Content-Type: application/json" \
       -d '{"messages": "Text Embeddings Inference (TEI) is a toolkit for deploying and serving open source text embeddings and sequence classification models. TEI enables high-performance extraction for the most popular models, including FlagEmbedding, Ember, GTE and E5."}'
   ```

2. Access via frontend

   To access the frontend, open the following URL in your browser: http://{host_ip}:5173.

   By default, the UI runs on port 5173 internally.

## Troubleshooting

1. If you get errors like "Access Denied", [validate micro service](https://github.com/opea-project/GenAIExamples/tree/main/DocSum/docker/xeon#validate-microservices) first. A simple example:

   ```bash
   http_proxy=""
   curl http://${your_ip}:8008/generate \
     -X POST \
     -d '{"inputs":"What is Deep Learning?","parameters":{"max_new_tokens":17, "do_sample": true}}' \
     -H 'Content-Type: application/json'
   ```

2. (Docker only) If all microservices work well, check the port ${host_ip}:8888, the port may be allocated by other users, you can modify the `compose.yaml`.

3. (Docker only) If you get errors like "The container name is in use", change container name in `compose.yaml`.
