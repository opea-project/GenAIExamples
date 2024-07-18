# ChatQnA Application

Chatbots are the most widely adopted use case for leveraging the powerful chat and reasoning capabilities of large language models (LLMs). The retrieval augmented generation (RAG) architecture is quickly becoming the industry standard for chatbots development. It combines the benefits of a knowledge base (via a vector store) and generative models to reduce hallucinations, maintain up-to-date information, and leverage domain-specific knowledge.

RAG bridges the knowledge gap by dynamically fetching relevant information from external sources, ensuring that responses generated remain factual and current. The core of this architecture are vector databases, which are instrumental in enabling efficient and semantic retrieval of information. These databases store data as vectors, allowing RAG to swiftly access the most pertinent documents or data points based on semantic similarity.

ChatQnA architecture shows below:

![architecture](./assets/img/chatqna_architecture.png)

ChatQnA is implemented on top of [GenAIComps](https://github.com/opea-project/GenAIComps), the ChatQnA Flow Chart shows below:

![Flow Chart](./assets/img/chatqna_flow_chart.png)

This ChatQnA use case performs RAG using LangChain, Redis VectorDB and Text Generation Inference on Intel Gaudi2 or Intel XEON Scalable Processors. The Intel Gaudi2 accelerator supports both training and inference for deep learning models in particular for LLMs. Please visit [Habana AI products](https://habana.ai/products) for more details.

# Deploy ChatQnA Service

The ChatQnA service can be effortlessly deployed on either Intel Gaudi2 or Intel XEON Scalable Processors.

Currently we support two ways of deploying ChatQnA services:

1. Start services using the docker image on `docker hub`.

2. Start services using the docker images built `manually`.

## Setup Environment Variable
To set up environment variables for deploying ChatQnA services, follow these steps:

1. Set the required environment variables:

```bash
export host_ip="External_Public_IP"
export no_proxy="Your_No_Proxy"
```

2. If you are in a proxy environment, also set the proxy-related environment variables:
```bash
export http_proxy="Your_HTTP_Proxy"
export https_proxy="Your_HTTPs_Proxy"
export HUGGINGFACEHUB_API_TOKEN="Your_Huggingface_API_Token"
```

3. Set up other environment variables:
```bash
bash ./docker/set_env.sh
```

## Deploy ChatQnA on Gaudi

If your version of `Habana Driver` < 1.16.0 (check with `hl-smi`), run the following command directly to start ChatQnA services.

```bash
cd GenAIExamples/ChatQnA/docker/gaudi/
docker compose -f docker_compose.yaml up -d
```

If your version of `Habana Driver` >= 1.16.0, refer to the [Gaudi Guide](./docker/gaudi/README.md) to build docker images manually.


## Deploy ChatQnA on Xeon

```bash
cd GenAIExamples/ChatQnA/docker/xeon/
docker compose -f docker_compose.yaml up -d
```

Refer to the [Xeon Guide](./docker/xeon/README.md) for more instructions on building docker images manually.

## Deploy ChatQnA on NVIDIA GPU

```bash
cd GenAIExamples/ChatQnA/docker/gpu/
docker compose -f docker_compose.yaml up -d
```

Refer to the [NVIDIA GPU Guide](./docker/gpu/README.md) for more instructions on building docker images manually.

## Deploy ChatQnA into Kubernetes on Xeon & Gaudi

Refer to the [Kubernetes Guide](./kubernetes/manifests/README.md) for instructions on deploying ChatQnA into Kubernetes on Xeon & Gaudi.

## Deploy ChatQnA on AI PC

Refer to the [AI PC Guide](./docker/aipc/README.md) for instructions on deploying ChatQnA on AI PC.

# Consume ChatQnA Service

Two ways of consuming ChatQnA Service:

1. Use cURL command on terminal

```bash
curl http://${host_ip}:8888/v1/chatqna \
    -H "Content-Type: application/json" \
    -d '{
        "messages": "What is the revenue of Nike in 2023?"
    }'
```

2. Access via frontend

To access the frontend, open the following URL in your browser: http://{host_ip}:5173. 

By default, the UI runs on port 5173 internally.