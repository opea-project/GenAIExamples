# Edge Craft Retrieval-Augmented Generation

Edge Craft RAG (EC-RAG) is a customizable, tunable and production-ready
Retrieval-Augmented Generation system for edge solutions. It is designed to
curate the RAG pipeline to meet hardware requirements at edge with guaranteed
quality and performance.

## What's New in this release?

- Add MilvusDB to support persistent storage
- Support EC-RAG service recovery after restart
- Add query search in EC-RAG pipeline to improve RAG quality
- Support Qwen3-8B as the default LLM for EC-RAG
- Enable chat history round setting for Users

## Quick Start Guide

### 1. Prerequisites

EC-RAG supports vLLM deployment(default method) and local OpenVINO deployment for Intel Arc GPU. Prerequisites are shown as below:  
Hardware: Intel Arc A770  
OS: Ubuntu Server 22.04.1 or newer (at least 6.2 LTS kernel)  
Driver & libraries: please to [Installing Client GPUs](https://dgpu-docs.intel.com/driver/client/overview.html) for detailed driver & libraries setup

Below steps are based on **vLLM** as inference engine, if you want to choose **OpenVINO**, please refer to [OpenVINO Local Inference](docs/Advanced_Setup.md#openvino-local-inference)

### 2. Prepare models

```bash
git clone https://github.com/opea-project/GenAIExamples.git
cd GenAIExamples/EdgeCraftRAG
# Prepare models for embedding, reranking:
export MODEL_PATH="${PWD}/models" # Your model path for embedding, reranking and LLM models
mkdir -p $MODEL_PATH
pip install --upgrade --upgrade-strategy eager "optimum[openvino]"
optimum-cli export openvino -m BAAI/bge-small-en-v1.5 ${MODEL_PATH}/BAAI/bge-small-en-v1.5 --task sentence-similarity
optimum-cli export openvino -m BAAI/bge-reranker-large ${MODEL_PATH}/BAAI/bge-reranker-large --task text-classification

# Prepare LLM model
export LLM_MODEL="Qwen/Qwen3-8B" # Your model id
pip install modelscope
modelscope download --model $LLM_MODEL --local_dir "${MODEL_PATH}/${LLM_MODEL}"
# Optionally, you can also download models with huggingface:
# pip install -U huggingface_hub
# huggingface-cli download $LLM_MODEL --local-dir "${MODEL_PATH}/${LLM_MODEL}"
```

### 3. Prepare env variables and configurations

Below steps are for single Intel Arc GPU inference, if you want to setup multi Intel Arc GPUs inference, please refer to [Multi-ARC Setup](docs/Advanced_Setup.md#multi-arc-setup)

#### Prepare env variables for vLLM deployment

```bash
ip_address=$(hostname -I | awk '{print $1}')
# Use `ip a` to check your active ip
export HOST_IP=$ip_address # Your host ip

# Check group id of video and render
export VIDEOGROUPID=$(getent group video | cut -d: -f3)
export RENDERGROUPID=$(getent group render | cut -d: -f3)

# If you have a proxy configured, uncomment below line
# export no_proxy=${no_proxy},${HOST_IP},edgecraftrag,edgecraftrag-server
# export NO_PROXY=${NO_PROXY},${HOST_IP},edgecraftrag,edgecraftrag-server
# If you have a HF mirror configured, it will be imported to the container
# export HF_ENDPOINT=https://hf-mirror.com # your HF mirror endpoint"

# Make sure all 3 folders have 1000:1000 permission, otherwise
# chown 1000:1000 ${MODEL_PATH} ${PWD} # the default value of DOC_PATH and TMPFILE_PATH is PWD ,so here we give permission to ${PWD}
# In addition, also make sure the .cache folder has 1000:1000 permission, otherwise
# chown 1000:1000 -R $HOME/.cache
```

For more advanced env variables and configurations, please refer to [Prepare env variables for vLLM deployment](docs/Advanced_Setup.md#prepare-env-variables-for-vllm-deployment)

#### Generate nginx config file

```bash
export VLLM_SERVICE_PORT_0=8100 # You can set your own port for vllm service
# Generate your nginx config file
# nginx-conf-generator.sh requires 2 parameters: DP_NUM and output filepath
bash nginx/nginx-conf-generator.sh 1 nginx/nginx.conf
# set NGINX_CONFIG_PATH
export NGINX_CONFIG_PATH="${PWD}/nginx/nginx.conf"
```

### 4. Start Edge Craft RAG Services with Docker Compose

```bash
# EC-RAG support Milvus as persistent database, by default milvus is disabled, you can choose to set MILVUS_ENABLED=1 to enable it
export MILVUS_ENABLED=0
# If you enable Milvus, the default storage path is PWD, uncomment if you want to change:
# export DOCKER_VOLUME_DIRECTORY= # change to your preference

# Launch EC-RAG service with compose
docker compose -f docker_compose/intel/gpu/arc/compose_vllm.yaml up -d
```

### 5. Access UI

Open your browser, access http://${HOST_IP}:8082

> Your browser should be running on the same host of your console, otherwise you will need to access UI with your host domain name instead of ${HOST_IP}.

Below is the UI front page, for detailed operations on UI and EC-RAG settings, please refer to [Explore_Edge_Craft_RAG](docs/Explore_Edge_Craft_RAG.md)
![front_page](assets/img/front_page.png)

| **Deploy Method** | **LLM Engine** | **LLM Model** | **Hardware** |
| ----------------- | -------------- | ------------- | ------------ |
| Docker Compose    | vLLM           | Qwen3-8B      | Intel Arc    |
