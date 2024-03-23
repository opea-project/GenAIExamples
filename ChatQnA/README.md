This ChatQnA use case performs RAG using LangChain, Redis vectordb and Text Generation Inference on Intel Gaudi2. The Intel Gaudi2 accelerator supports both training and inference for deep learning models in particular for LLMs. Please visit [Habana AI products](https://habana.ai/products) for more details.

# Environment Setup
To use [🤗 text-generation-inference](https://github.com/huggingface/text-generation-inference) on Habana Gaudi/Gaudi2, please follow these steps:

## Prepare Docker

Getting started is straightforward with the official Docker container. Simply pull the image using:

```bash
docker pull ghcr.io/huggingface/tgi-gaudi:1.2.1
```

Alternatively, you can build the Docker image yourself with:

```bash
bash ./serving/tgi_gaudi/build_docker.sh
```

## Launch TGI Gaudi Service

### Launch a local server instance on 1 Gaudi card:
```bash
bash ./serving/tgi_gaudi/launch_tgi_service.sh
```

For gated models such as `LLAMA-2`, you will have to pass -e HUGGING_FACE_HUB_TOKEN=\<token\> to the docker run command above with a valid Hugging Face Hub read token.

Please follow this link [huggingface token](https://huggingface.co/docs/hub/security-tokens) to get the access token ans export `HUGGINGFACEHUB_API_TOKEN` environment with the token.

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

## Enable TGI Gaudi FP8 for higher throughput
The TGI Gaudi utilizes BFLOAT16 optimization as the default setting. If you aim to achieve higher throughput, you can enable FP8 quantization on the TGI Gaudi. According to our test results, FP8 quantization yields approximately a 1.8x performance gain compared to BFLOAT16. Please follow the below steps to enable FP8 quantization.

### Prepare Metadata for FP8 Quantization

Enter into the TGI Gaudi docker container, and then run the below commands:

```bash
git clone https://github.com/huggingface/optimum-habana.git
cd optimum-habana/examples/text-generation
pip install -r requirements_lm_eval.txt
QUANT_CONFIG=./quantization_config/maxabs_measure.json python ../gaudi_spawn.py run_lm_eval.py -o acc_7b_bs1_measure.txt --
model_name_or_path meta-llama/Llama-2-7b-hf --attn_softmax_bf16 --use_hpu_graphs --trim_logits --use_kv_cache --reuse_cache --bf16 --batch_size 1
QUANT_CONFIG=./quantization_config/maxabs_quant.json python ../gaudi_spawn.py run_lm_eval.py -o acc_7b_bs1_quant.txt --model_name_or_path
meta-llama/Llama-2-7b-hf --attn_softmax_bf16 --use_hpu_graphs --trim_logits --use_kv_cache --reuse_cache --bf16 --batch_size 1 --fp8
```

After finishing the above commands, the quantization metadata will be generated. Move the metadata directory ./hqt_output/ and copy the quantization JSON file to the host (under …/data). Please adapt the commands with your Docker ID and directory path.

```bash
docker cp 262e04bbe466:/usr/src/optimum-habana/examples/text-generation/hqt_output data/
docker cp 262e04bbe466:/usr/src/optimum-habana/examples/text-generation/quantization_config/maxabs_quant.json data/
```

### Restart the TGI Gaudi server within all the metadata mapped

```bash
docker run -d -p 8080:80 -e QUANT_CONFIG=/data/maxabs_quant.json -e HUGGING_FACE_HUB_TOKEN=<your HuggingFace token> -v $volume:/data --
runtime=habana -e HABANA_VISIBLE_DEVICES="4,5,6" -e OMPI_MCA_btl_vader_single_copy_mechanism=none --cap-add=sys_nice --ipc=host tgi_gaudi --
model-id meta-llama/Llama-2-7b-hf
```

Now the TGI Gaudi will launch the FP8 model by default. Please note that currently only Llama2 and Mistral models support FP8 quantization.


## Launch Redis
```bash
docker pull redis/redis-stack:latest
docker compose -f langchain/docker/docker-compose-redis.yml up -d
```

## Launch LangChain Docker

### Build LangChain Docker Image

```bash
cd langchain/docker/
bash ./build_docker.sh
```

### Lanuch LangChain Docker

Update the `HUGGINGFACEHUB_API_TOKEN` environment variable with your huggingface token in the `docker-compose-langchain.yml`

```bash
docker compose -f docker-compose-langchain.yml up -d
cd ../../
```

## Ingest data into redis

After every time of redis container is launched, data should be ingested in the container ingestion steps:

```bash
docker exec -it qna-rag-redis-server bash
cd /ws
python ingest.py
```

Note: `ingest.py` will download the embedding model, please set the proxy if necessary.

# Start LangChain Server

## Start the Backend Service
Make sure TGI-Gaudi service is running and also make sure data is populated into Redis. Launch the backend service:

```bash
docker exec -it qna-rag-redis-server bash
nohup python app/server.py &
```

## Start the Frontend Service

Navigate to the "ui" folder and execute the following commands to start the fronend GUI:
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
