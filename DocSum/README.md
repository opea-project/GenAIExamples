# Document Summarization

In a world where data, information, and legal complexities is prevalent, the volume of legal documents is growing rapidly. Law firms, legal professionals, and businesses are dealing with an ever-increasing number of legal texts, including contracts, court rulings, statutes, and regulations.
These documents contain important insights, but understanding them can be overwhelming. This is where the demand for legal document summarization comes in.

Large Language Models (LLMs) have revolutionized the way we interact with text, LLMs can be used to create summaries of news articles, research papers, technical documents, and other types of text. Suppose you have a set of documents (PDFs, Notion pages, customer questions, etc.) and you want to summarize the content. In this example use case, we use LangChain to apply some summarization strategies and run LLM inference using Text Generation Inference on Intel Xeon and Gaudi2.

The document summarization architecture shows below:

![Architecture](https://i.imgur.com/XT0YUhu.png)

![Workflow](https://i.imgur.com/m9Ac9wy.png)

# Environment Setup

To use [🤗 text-generation-inference](https://github.com/huggingface/text-generation-inference) on Habana Gaudi/Gaudi2, please follow these steps:

## Build TGI Gaudi Docker Image

```bash
bash ./serving/tgi_gaudi/build_docker.sh
```

## Launch TGI Gaudi Service

### Launch a local server instance on 1 Gaudi card:

```bash
bash ./serving/tgi_gaudi/launch_tgi_service.sh
```

For gated models such as `LLAMA-2`, you will have to pass -e HUGGING_FACE_HUB_TOKEN=\<token\> to the docker run command above with a valid Hugging Face Hub read token.

Please follow this link [huggingface token](https://huggingface.co/docs/hub/security-tokens) to get the access token and export `HUGGINGFACEHUB_API_TOKEN` environment with the token.

```bash
export HUGGINGFACEHUB_API_TOKEN=<token>
```

### Launch a local server instance on 8 Gaudi cards:

```bash
bash ./serving/tgi_gaudi/launch_tgi_service.sh 8
```

### Customize TGI Gaudi Service

The ./serving/tgi_gaudi/launch_tgi_service.sh script accepts three parameters:

- num_cards: The number of Gaudi cards to be utilized, ranging from 1 to 8. The default is set to 1.
- port_number: The port number assigned to the TGI Gaudi endpoint, with the default being 8080.
- model_name: The model name utilized for LLM, with the default set to "Intel/neural-chat-7b-v3-3".

You have the flexibility to customize these parameters according to your specific needs. Additionally, you can set the TGI Gaudi endpoint by exporting the environment variable `TGI_ENDPOINT`:

```bash
export TGI_ENDPOINT="http://xxx.xxx.xxx.xxx:8080"
```

## Launch Document Summary Docker

### Build Document Summary Docker Image (Optional)

```bash
cd langchain/docker/
bash ./build_docker.sh
cd ../../
```

### Launch Document Summary Docker

```bash
docker run -it --net=host --ipc=host -e http_proxy=${http_proxy} -e https_proxy=${https_proxy} -v /var/run/docker.sock:/var/run/docker.sock intel/gen-ai-examples:document-summarize bash
```

# Start Document Summary Server

## Start the Backend Service

Make sure TGI-Gaudi service is running. Launch the backend service:

```bash
export HUGGINGFACEHUB_API_TOKEN=<token>
nohup python app/server.py &
```

Then you can make requests like below to check the DocSum backend service status:

```bash
curl http://127.0.0.1:8000/v1/text_summarize \
    -X POST \
    -H 'Content-Type: application/json' \
    -d '{"text":"Text Embeddings Inference (TEI) is a toolkit for deploying and serving open source text embeddings and sequence classification models. TEI enables high-performance extraction for the most popular models, including FlagEmbedding, Ember, GTE and E5."}'
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

Update the `BASIC_URL` environment variable in the `.env` file by replacing the IP address '127.0.0.1' with the actual IP address.

Run the following command to install the required dependencies:

```bash
npm install
```

Start the development server by executing the following command:

```bash
nohup npm run dev &
```

This will initiate the frontend service and launch the application.
