# ChatQnA Application

Chatbots are the most widely adopted use case for leveraging the powerful chat and reasoning capabilities of large language models (LLM). The retrieval augmented generation (RAG) architecture is quickly becoming the industry standard for developing chatbots because it combines the benefits of a knowledge base (via a vector store) and generative models to reduce hallucinations, maintain up-to-date information, and leverage domain-specific knowledge.

RAG bridges the knowledge gap by dynamically fetching relevant information from external sources, ensuring that responses generated remain factual and current. At the heart of this architecture are vector databases, instrumental in enabling efficient and semantic retrieval of information. These databases store data as vectors, allowing RAG to swiftly access the most pertinent documents or data points based on semantic similarity.

ChatQnA architecture shows below:

![architecture](https://i.imgur.com/lLOnQio.png)

This ChatQnA use case performs RAG using LangChain, Redis vectordb, Text Generation Inference and vLLM on Intel Gaudi2 or Intel XEON Scalable Processors. The Intel XEON Scalable Processors and Gaudi2 accelerator support both training and inference for deep learning models in particular for LLMs. Please visit [Intel products](https://www.intel.com/content/www/us/en/products/overview.html) and [Habana AI products](https://habana.ai/products) for more details.

# Solution Overview

Steps to implement the solution are as follows

## In Intel Gaudi2 Platform

1. [Deploy a TGI container with LLM model of your choice](#launch-tgi-gaudi-service) (Solution uses 70B model by default)

## In Intel Xeon Platform

**Using TGI Endpoint Service**

1. [Export TGI endpoint as environment variable](#customize-tgi-gaudi-service)

or **Using vLLM Endpoint Service**

1. [Export vLLM endpoint as environment variable](#customize-vllm-cpu-service)

2. [Deploy a TEI container for Embedding model service and export the endpoint](#enable-tei-for-embedding-model)
3. [Launch a Redis container and Langchain container](#launch-redis-and-langchain-backend-service)
4. [Ingest data into redis](#ingest-data-into-redis), this example provides few example PDF documents
5. [Start the backend service](#start-the-backend-service) to accept queries to Langchain
6. [Start the GUI](#start-the-frontend-service) based chatbot service to experiment with RAG based Chatbot

To use [🤗 text-generation-inference](https://github.com/huggingface/text-generation-inference) on Habana Gaudi/Gaudi2, please follow these steps:

## Prepare LLM Endpoint Service

### Prepare TGI Docker

Getting started is straightforward with the official Docker container. Simply pull the image using:

```bash
docker pull ghcr.io/huggingface/tgi-gaudi:1.2.1
```

Alternatively, you can build the Docker image yourself using latest [TGI-Gaudi](https://github.com/huggingface/tgi-gaudi) code with the below command:

```bash
bash ./serving/tgi_gaudi/build_docker.sh
```

### Launch TGI Gaudi Service

#### Launch a local server instance on 1 Gaudi card:

```bash
bash ./serving/tgi_gaudi/launch_tgi_service.sh
```

For gated models such as `LLAMA-2`, you will have to pass -e HUGGING_FACE_HUB_TOKEN=\<token\> to the docker run command above with a valid Hugging Face Hub read token.

Please follow this link [huggingface token](https://huggingface.co/docs/hub/security-tokens) to get the access token and export `HUGGINGFACEHUB_API_TOKEN` environment with the token.

```bash
export HUGGINGFACEHUB_API_TOKEN=<token>
```

#### Launch a local server instance on 8 Gaudi cards:

```bash
bash ./serving/tgi_gaudi/launch_tgi_service.sh 8
```

And then you can make requests like below to check the service status:

```bash
curl 127.0.0.1:8080/generate \
  -X POST \
  -d '{"inputs":"What is Deep Learning?","parameters":{"max_new_tokens":32}}' \
  -H 'Content-Type: application/json'
```

#### Customize TGI Gaudi Service

The ./serving/tgi_gaudi/launch_tgi_service.sh script accepts three parameters:

- num_cards: The number of Gaudi cards to be utilized, ranging from 1 to 8. The default is set to 1.
- port_number: The port number assigned to the TGI Gaudi endpoint, with the default being 8080.
- model_name: The model name utilized for LLM, with the default set to "Intel/neural-chat-7b-v3-3".

You have the flexibility to customize these parameters according to your specific needs. Additionally, you can set the TGI Gaudi endpoint by exporting the environment variable `TGI_LLM_ENDPOINT`:

```bash
export TGI_LLM_ENDPOINT="http://xxx.xxx.xxx.xxx:8080"
```

### Prepare vLLM Docker

Getting started is straightforward with the official Docker container. You can build the Docker image yourself using latest [vLLM-CPU](https://github.com/vllm-project/vllm) code with the below command:

```bash
bash ./serving/vllm/build_docker_cpu.sh
```

### Launch vLLM CPU Service

#### Launch a local server instance:

```bash
bash ./serving/vllm/launch_vllm_service.sh
```

For gated models such as `LLAMA-2`, you will have to pass -e HUGGING_FACE_HUB_TOKEN=\<token\> to the docker run command above with a valid Hugging Face Hub read token.

Please follow this link [huggingface token](https://huggingface.co/docs/hub/security-tokens) to get the access token and export `HUGGINGFACEHUB_API_TOKEN` environment with the token.

```bash
export HUGGINGFACEHUB_API_TOKEN=<token>
```

And then you can make requests like below to check the service status:

```bash
curl http://127.0.0.1::8080/v1/completions \
  -H "Content-Type: application/json" \
  -d '{
  "model": <model_name>,
  "prompt": "What is Deep Learning?",
  "max_tokens": 32,
  "temperature": 0
  }'
```

#### Customize vLLM CPU Service

The ./serving/vllm/launch_vllm_service.sh script accepts two parameters:

- port_number: The port number assigned to the vLLM CPU endpoint, with the default being 8080.
- model_name: The model name utilized for LLM, with the default set to "mistralai/Mistral-7B-v0.1".

You have the flexibility to customize twp parameters according to your specific needs. Additionally, you can set the vLLM CPU endpoint by exporting the environment variable `vLLM_LLM_ENDPOINT`:

```bash
export vLLM_LLM_ENDPOINT="http://xxx.xxx.xxx.xxx:8080"
export LLM_MODEL=<model_name> # example: export LLM_MODEL="mistralai/Mistral-7B-v0.1"
```

## Enable TEI for embedding model

Text Embeddings Inference (TEI) is a toolkit designed for deploying and serving open-source text embeddings and sequence classification models efficiently. With TEI, users can extract high-performance features using various popular models. It supports token-based dynamic batching for enhanced performance.

To launch the TEI service, you can use the following commands:

```bash
model=BAAI/bge-large-en-v1.5
revision=refs/pr/5
volume=$PWD/data # share a volume with the Docker container to avoid downloading weights every run
docker run -p 9090:80 -v $volume:/data -e http_proxy=$http_proxy -e https_proxy=$https_proxy --pull always ghcr.io/huggingface/text-embeddings-inference:cpu-1.2 --model-id $model --revision $revision
export TEI_ENDPOINT="http://xxx.xxx.xxx.xxx:9090"
```

And then you can make requests like below to check the service status:

```bash
curl 127.0.0.1:9090/embed \
    -X POST \
    -d '{"inputs":"What is Deep Learning?"}' \
    -H 'Content-Type: application/json'
```

Note: If you want to integrate the TEI service into the LangChain application, you'll need to restart the LangChain backend service after launching the TEI service.

## Launch Redis and LangChain Backend Service

Update the `HUGGINGFACEHUB_API_TOKEN` environment variable with your huggingface token in the `docker-compose.yml`

```bash
cd langchain/docker
docker compose -f docker-compose.yml up -d
cd ../../
```

> [!NOTE]
> If you modified any files and want that change introduced in this step, add `--build` to the end of the command to build the container image instead of pulling it from dockerhub.

## Ingest data into Redis

Each time the Redis container is launched, data should be ingested into the container using the commands:

```bash
docker exec -it qna-rag-redis-server bash
cd /ws
python ingest.py
```

Note: `ingest.py` will download the embedding model. Please set the proxy if necessary.

# Start LangChain Server

## Enable GuardRails using Meta's Llama Guard model (Optional)

We offer content moderation support utilizing Meta's [Llama Guard](https://huggingface.co/meta-llama/LlamaGuard-7b) model. To activate GuardRails, kindly follow the instructions below to deploy the Llama Guard model on TGI Gaudi.

```bash
volume=$PWD/data
model_id="meta-llama/LlamaGuard-7b"
docker run -p 8088:80 -v $volume:/data --runtime=habana -e HABANA_VISIBLE_DEVICES=all -e OMPI_MCA_btl_vader_single_copy_mechanism=none --cap-add=sys_nice --ipc=host -e HUGGING_FACE_HUB_TOKEN=<your HuggingFace token> -e HTTPS_PROXY=$https_proxy -e HTTP_PROXY=$https_proxy tgi_gaudi --model-id $model_id
export SAFETY_GUARD_ENDPOINT="http://xxx.xxx.xxx.xxx:8088"
```

And then you can make requests like below to check the service status:

```bash
curl 127.0.0.1:8088/generate \
  -X POST \
  -d '{"inputs":"How do you buy a tiger in the US?","parameters":{"max_new_tokens":32}}' \
  -H 'Content-Type: application/json'
```

## Start the Backend Service

Make sure TGI-Gaudi service is running and also make sure data is populated into Redis. Launch the backend service:

```bash
docker exec -it qna-rag-redis-server bash
# export TGI_LLM_ENDPOINT="http://xxx.xxx.xxx.xxx:8080" - can be omitted if set before in docker-compose.yml
# export TEI_ENDPOINT="http://xxx.xxx.xxx.xxx:9090" - Needs to be added only if TEI to be used and can be omitted if set before in docker-compose.yml
nohup python app/server.py &
```

The LangChain backend service listens to port 8000, you can customize it by changing the code in `docker/qna-app/app/server.py`.

And then you can make requests like below to check the LangChain backend service status:

```bash
# non-streaming endpoint
curl 127.0.0.1:8000/v1/rag/chat \
  -X POST \
  -d '{"query":"What is the total revenue of Nike in 2023?"}' \
  -H 'Content-Type: application/json'
```

```bash
# streaming endpoint
curl 127.0.0.1:8000/v1/rag/chat_stream \
  -X POST \
  -d '{"query":"What is the total revenue of Nike in 2023?"}' \
  -H 'Content-Type: application/json'
```

## Start the Frontend Service

Navigate to the "ui" folder and execute the following commands to start the frontend GUI:

```bash
cd ui
sudo apt-get install npm && \
    npm install -g n && \
    n stable && \
    hash -r && \
    npm install -g npm@latest
```

For CentOS, please use the following commands instead:

```bash
curl -sL https://rpm.nodesource.com/setup_20.x | sudo bash -
sudo yum install -y nodejs
```

Update the `DOC_BASE_URL` environment variable in the `.env` file by replacing the IP address '127.0.0.1' with the actual IP address.

Run the following command to install the required dependencies:

```bash
npm install
```

Start the development server by executing the following command:

```bash
nohup npm run dev &
```

This will initiate the frontend service and launch the application.

# Enable TGI Gaudi FP8 for higher throughput (Optional)

The TGI Gaudi utilizes BFLOAT16 optimization as the default setting. If you aim to achieve higher throughput, you can enable FP8 quantization on the TGI Gaudi. Note that currently only Llama2 series and Mistral series models support FP8 quantization. Please follow the below steps to enable FP8 quantization.

## Deploy ChatQnA on Xeon

Refer to the [Xeon Guide](./microservice/xeon/README.md) for instructions on deploying ChatQnA on Xeon.
