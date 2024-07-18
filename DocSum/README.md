# Document Summarization Application

In a world where data, information, and legal complexities are prevalent, the volume of legal documents is growing rapidly. Law firms, legal professionals, and businesses are dealing with an ever-increasing number of legal texts, including contracts, court rulings, statutes, and regulations. These documents contain important insights, but understanding them can be overwhelming. This is where the demand for legal document summarization comes in.

Large Language Models (LLMs) have revolutionized the way we interact with text. These models can be used to create summaries of news articles, research papers, technical documents, and other types of text. Suppose you have a set of documents (PDFs, Notion pages, customer questions, etc.) and you want to summarize the content. In this example use case, we utilize LangChain to implement summarization strategies and facilitate LLM inference using Text Generation Inference on Intel Xeon and Gaudi2 processors.

The architecture for document summarization will be illustrated/described below:

![Architecture](./assets/img/docsum_architecture.png)

![Workflow](./assets/img/docsum_workflow.png)

# Deploy Document Summarization Service

The Document Summarization service can be effortlessly deployed on either Intel Gaudi2 or Intel XEON Scalable Processors.
Based on whether you want to use Docker or Kubernetes, please follow the instructions below.

Currently we support two ways of deploying Document Summarization services with docker compose:

1. Start services using the docker image on `docker hub`:

```bash
docker pull opea/docsum:latest
```

2. Start services using the docker images `built from source`: [Guide](./docker)

## Setup Environment Variable

To set up environment variables for deploying Document Summarization services, follow these steps:

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

## Deploy using Docker

### Deploy on Gaudi

If your version of `Habana Driver` < 1.16.0 (check with `hl-smi`), run the following command directly to start DocSum services. Please find corresponding [docker_compose.yaml](./docker/gaudi/docker_compose.yaml).

```bash
cd GenAIExamples/DocSum/docker/gaudi/
docker compose -f docker_compose.yaml up -d
```

If your version of `Habana Driver` >= 1.16.0, refer to the [Gaudi Guide](./docker/gaudi/README.md) to build docker images from source.

### Deploy on Xeon

Please find corresponding [docker_compose.yaml](./docker/xeon/docker_compose.yaml).

```bash
cd GenAIExamples/DocSum/docker/xeon/
docker compose -f docker_compose.yaml up -d
```

Refer to the [Xeon Guide](./docker/xeon/README.md) for more instructions on building docker images from source.

## Deploy using Kubernetes

Please refer to [Kubernetes deployment](./kubernetes/README.md)

# Consume Document Summarization Service

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

# Troubleshooting

1. If you get errors like "Access Denied", please [validate micro service](https://github.com/opea-project/GenAIExamples/tree/main/DocSum/docker/xeon#validate-microservices) first. A simple example:

```bash
http_proxy=""
curl http://${your_ip}:8008/generate \
  -X POST \
  -d '{"inputs":"What is Deep Learning?","parameters":{"max_new_tokens":17, "do_sample": true}}' \
  -H 'Content-Type: application/json'
```

2. (Docker only) If all microservices work well, please check the port ${host_ip}:8888, the port may be allocated by other users, you can modify the `docker_compose.yaml`.

3. (Docker only) If you get errors like "The container name is in use", please change container name in `docker_compose.yaml`.
