# ChatQnA Application

Chatbots are the most widely adopted use case for leveraging the powerful chat and reasoning capabilities of large language models (LLM). The retrieval augmented generation (RAG) architecture is quickly becoming the industry standard for developing chatbots because it combines the benefits of a knowledge base (via a vector store) and generative models to reduce hallucinations, maintain up-to-date information, and leverage domain-specific knowledge.

RAG bridges the knowledge gap by dynamically fetching relevant information from external sources, ensuring that responses generated remain factual and current. At the heart of this architecture are vector databases, instrumental in enabling efficient and semantic retrieval of information. These databases store data as vectors, allowing RAG to swiftly access the most pertinent documents or data points based on semantic similarity.

ChatQnA architecture shows below:

![architecture](https://i.imgur.com/lLOnQio.png)

This ChatQnA use case performs RAG using LangChain, Redis vectordb and Text Generation Inference on Intel Gaudi2. The Intel Gaudi2 accelerator supports both training and inference for deep learning models in particular for LLMs. Please visit [Habana AI products](https://habana.ai/products) for more details.

# Solution Overview

Steps to implement the solution are as follows

## In Intel Gaudi2 Platform

1. [Deploy a TGI container with LLM model of your choice](#launch-tgi-gaudi-service) (Solution uses 70B model by default)

## In Intel Xeon Platform

1. [Export TGI endpoint as environment variable](#customize-tgi-gaudi-service)
2. [Deploy a TEI container for Embedding model service and export the endpoint](#enable-tei-for-embedding-model)
3. [Launch a Redis container and Langchain container](#launch-redis-and-langchain-backend-service)
4. [Ingest data into redis](#ingest-data-into-redis), this example provides few example PDF documents
5. [Start the backend service](#start-the-backend-service) to accept queries to Langchain
6. [Start the GUI](#start-the-frontend-service) based chatbot service to experiment with RAG based Chatbot

To use [🤗 text-generation-inference](https://github.com/huggingface/text-generation-inference) on Habana Gaudi/Gaudi2, please follow these steps:

## Prepare TGI Docker

Getting started is straightforward with the official Docker container. Simply pull the image using:

```bash
docker pull ghcr.io/huggingface/tgi-gaudi:1.2.1
```

Alternatively, you can build the Docker image yourself using latest [TGI-Gaudi](https://github.com/huggingface/tgi-gaudi) code with the below command:

```bash
bash ./serving/tgi_gaudi/build_docker.sh
```

## Launch TGI Gaudi Service

### Launch a local server instance on 1 Gaudi card:

```bash
bash ./serving/tgi_gaudi/launch_tgi_service.sh
```

For gated models such as `LLAMA-2`, you will have to pass -e HF_TOKEN=\<token\> to the docker run command above with a valid Hugging Face Hub read token.

Please follow this link [huggingface token](https://huggingface.co/docs/hub/security-tokens) to get the access token and export `HF_TOKEN` environment with the token.

```bash
export HF_TOKEN=<token>
```

### Launch a local server instance on 8 Gaudi cards:

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

### Customize TGI Gaudi Service

The ./serving/tgi_gaudi/launch_tgi_service.sh script accepts three parameters:

- num_cards: The number of Gaudi cards to be utilized, ranging from 1 to 8. The default is set to 1.
- port_number: The port number assigned to the TGI Gaudi endpoint, with the default being 8080.
- model_name: The model name utilized for LLM, with the default set to "Intel/neural-chat-7b-v3-3".

You have the flexibility to customize these parameters according to your specific needs. Additionally, you can set the TGI Gaudi endpoint by exporting the environment variable `TGI_LLM_ENDPOINT`:

```bash
export TGI_LLM_ENDPOINT="http://xxx.xxx.xxx.xxx:8080"
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

## Launch Vector Database and LangChain Backend Service

Update the `HF_TOKEN` environment variable with your huggingface token in the `docker-compose.yml`

By default, Redis is used as the vector store. To use Qdrant, use the `docker-compose-qdrant.yml` file instead.

```bash
cd langchain/docker
docker compose -f docker-compose.yml up -d
# To use Qdrant, run
# docker compose -f docker-compose-qdrant.yml up -d
cd ../../
```

> [!NOTE]
> If you modified any files and want that change introduced in this step, add `--build` to the end of the command to build the container image instead of pulling it from dockerhub.

## Ingest Data Into Vector Database

Each time the vector database container is launched, data should be ingested into the container using the commands:

```bash
docker exec -it qna-rag-redis-server bash
# To use Qdrant, run
# docker exec -it qna-rag-qdrant-server bash
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
docker run -p 8088:80 -v $volume:/data --runtime=habana -e HABANA_VISIBLE_DEVICES=all -e OMPI_MCA_btl_vader_single_copy_mechanism=none --cap-add=sys_nice --ipc=host -e HF_TOKEN=<your HuggingFace token> -e HTTPS_PROXY=$https_proxy -e HTTP_PROXY=$https_proxy tgi_gaudi --model-id $model_id
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

## Prepare Metadata for FP8 Quantization

Enter into the TGI Gaudi docker container, and then run the below commands:

```bash
pip install git+https://github.com/huggingface/optimum-habana.git
git clone https://github.com/huggingface/optimum-habana.git
cd optimum-habana/examples/text-generation
pip install -r requirements_lm_eval.txt
QUANT_CONFIG=./quantization_config/maxabs_measure.json python ../gaudi_spawn.py run_lm_eval.py -o acc_7b_bs1_measure.txt --model_name_or_path Intel/neural-chat-7b-v3-3 --attn_softmax_bf16 --use_hpu_graphs --trim_logits --use_kv_cache --reuse_cache --bf16 --batch_size 1
QUANT_CONFIG=./quantization_config/maxabs_quant.json python ../gaudi_spawn.py run_lm_eval.py -o acc_7b_bs1_quant.txt --model_name_or_path Intel/neural-chat-7b-v3-3 --attn_softmax_bf16 --use_hpu_graphs --trim_logits --use_kv_cache --reuse_cache --bf16 --batch_size 1 --fp8
```

After finishing the above commands, the quantization metadata will be generated. Move the metadata directory ./hqt_output/ and copy the quantization JSON file to the host (under …/data). Please adapt the commands with your Docker ID and directory path.

```bash
docker cp 262e04bbe466:/usr/src/optimum-habana/examples/text-generation/hqt_output data/
docker cp 262e04bbe466:/usr/src/optimum-habana/examples/text-generation/quantization_config/maxabs_quant.json data/
```

Then modify the `dump_stats_path` to "/data/hqt_output/measure" and update `dump_stats_xlsx_path` to /data/hqt_output/measure/fp8stats.xlsx" in maxabs_quant.json file.

## Restart the TGI Gaudi server within all the metadata mapped

```bash
docker run -p 8080:80 -e QUANT_CONFIG=/data/maxabs_quant.json -v $volume:/data --runtime=habana -e HABANA_VISIBLE_DEVICES=all -e OMPI_MCA_btl_vader_single_copy_mechanism=none --cap-add=sys_nice --ipc=host ghcr.io/huggingface/tgi-gaudi:1.2.1 --model-id Intel/neural-chat-7b-v3-3
```

Now the TGI Gaudi will launch the FP8 model by default and you can make requests like below to check the service status:

```bash
curl 127.0.0.1:8080/generate \
  -X POST \
  -d '{"inputs":"What is Deep Learning?","parameters":{"max_new_tokens":32}}' \
  -H 'Content-Type: application/json'
```

#

SCRIPT USAGE NOTICE:  By downloading and using any script file included with the associated software package (such as files with .bat, .cmd, or .JS extensions, Docker files, or any other type of file that, when executed, automatically downloads and/or installs files onto your system) (the “Script File”), it is your obligation to review the Script File to understand what files (e.g.,  other software, AI models, AI Datasets) the Script File will download to your system (“Downloaded Files”). Furthermore, by downloading and using the Downloaded Files, even if they are installed through a silent install, you agree to any and all terms and conditions associated with such files, including but not limited to, license terms, notices, or disclaimers.
