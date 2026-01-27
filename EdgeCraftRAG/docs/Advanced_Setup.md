# Edge Craft Retrieval-Augmented Generation Advanced Setup

## OpenVINO Local Inference

EC-RAG support using local OpenVINO models to do inference, please follow below steps to run local inference:

### 1. (Optional) Build Docker Images for Mega Service, Server and UI by your own

**All the docker images can be automatically‌ pulled**, If you want to build the images by your own, please follow the steps:

```bash
git clone https://github.com/opea-project/GenAIExamples.git
cd GenAIExamples/EdgeCraftRAG
docker build --no-cache --pull --build-arg http_proxy=$http_proxy --build-arg https_proxy=$https_proxy --build-arg no_proxy="$no_proxy" -t opea/edgecraftrag:latest -f Dockerfile .
docker build --no-cache --pull --build-arg http_proxy=$http_proxy --build-arg https_proxy=$https_proxy --build-arg no_proxy="$no_proxy" -t opea/edgecraftrag-server:latest -f Dockerfile.server .
docker build --no-cache --pull --build-arg http_proxy=$http_proxy --build-arg https_proxy=$https_proxy --build-arg no_proxy="$no_proxy" -t opea/edgecraftrag-ui:latest -f ui/docker/Dockerfile.ui .
```

### 2. Prepare models

```bash
# Prepare models for embedding, reranking and generation, you can also choose other OpenVINO optimized models
export MODEL_PATH="${PWD}/ov_models" # Your model path for embedding, reranking and LLM models
mkdir -p $MODEL_PATH
pip install --upgrade --upgrade-strategy eager "optimum[openvino]"
optimum-cli export openvino -m BAAI/bge-small-en-v1.5 ${MODEL_PATH}/BAAI/bge-small-en-v1.5 --task sentence-similarity
optimum-cli export openvino -m BAAI/bge-reranker-large ${MODEL_PATH}/BAAI/bge-reranker-large --task text-classification
optimum-cli export openvino --model Qwen/Qwen3-8B ${MODEL_PATH}/Qwen/Qwen3-8B/INT4_compressed_weights --task text-generation-with-past --weight-format int4 --group-size 128 --ratio 0.8
```

### 3. Prepare env variables and configurations

```bash
ip_address=$(hostname -I | awk '{print $1}')
# Use `ip a` to check your active ip
export HOST_IP=$ip_address # Your host ip

# Check group id of video and render
export VIDEOGROUPID=$(getent group video | cut -d: -f3)
export RENDERGROUPID=$(getent group render | cut -d: -f3)

# If you have a proxy configured, execute below line
export no_proxy=${no_proxy},${HOST_IP},edgecraftrag,edgecraftrag-server
export NO_PROXY=${NO_PROXY},${HOST_IP},edgecraftrag,edgecraftrag-server
# If you have a HF mirror configured, it will be imported to the container
# export HF_ENDPOINT=https://hf-mirror.com # your HF mirror endpoint"

# Make sure all 3 folders have 1000:1000 permission, otherwise
export DOC_PATH=${PWD}/tests
export TMPFILE_PATH=${PWD}/tests
chown 1000:1000 -R ${MODEL_PATH} ${DOC_PATH} ${TMPFILE_PATH}
# In addition, also make sure the .cache folder has 1000:1000 permission, otherwise
chown 1000:1000 -R $HOME/.cache
```

### 4. Start Edge Craft RAG Services with Docker Compose

```bash
# EC-RAG support Milvus as persistent database, by default milvus is disabled, you can choose to set MILVUS_ENABLED=1 to enable it
export MILVUS_ENABLED=0
# If you enable Milvus, the default storage path is PWD, uncomment if you want to change:
# export DOCKER_VOLUME_DIRECTORY= # change to your preference

# EC-RAG support chat history round setting, by default chat history is disabled, you can set CHAT_HISTORY_ROUND to control it
# export CHAT_HISTORY_ROUND= # change to your preference

# EC-RAG support pipeline performance benchmark, use ENABLE_BENCHMARK=true/false to turn on/off benchmark
# export ENABLE_BENCHMARK= # change to your preference

export MAX_MODEL_LEN=5000
# Launch EC-RAG service with compose
docker compose -f docker_compose/intel/gpu/arc/compose.yaml up -d
```

## EC-RAG with Kbadmin

EC-RAG support kbadmin as a knowledge base manager  
Please make sure all the kbadmin services have been launched
EC-RAG Docker Images preparation is the same as local inference section, please refer to [Build Docker Images](#1-optional-build-docker-images-for-mega-service-server-and-ui-by-your-own)
Model preparation is the same as vLLM inference section, please refer to [Prepare models](../docker_compose/intel/gpu/arc/README.md#2-prepare-models)

### 1. Start Edge Craft RAG Services with Docker Compose

This section is the same as default vLLM inference section, please refer to [Prepare env variables and configurations](../docker_compose/intel/gpu/arc/README.md#prepare-env-variables-and-configurations) and [Start Edge Craft RAG Services with Docker Compose](../docker_compose/intel/gpu/arc/README.md#deploy-the-service-on-arc-a770-using-docker-compose)

### 2. Access Kbadmin UI

please refer to [ChatQnA with Kbadmin in UI](./Explore_Edge_Craft_RAG.md#chatqna-with-kbadmin-in-ui)

## Deploy EC-RAG on multi GPUs

In this sample, we will use Qwen3-30B-A3B deployment on 4 Arc B60 GPUs as an example.
Before started, please prepare models into MODEL_PATH and prepare docker images

### Prepare env variables and configurations

```bash
export MODEL_PATH="${PWD}/models" # Your model path
export LLM_MODEL="Qwen/Qwen3-30B-A3B"
ip_address=$(hostname -I | awk '{print $1}')
# Use `ip a` to check your active ip
export HOST_IP=$ip_address # Your host ip

# Check group id of video and render
export VIDEOGROUPID=$(getent group video | cut -d: -f3)
export RENDERGROUPID=$(getent group render | cut -d: -f3)

# If you have a proxy configured, execute below line
export no_proxy=${no_proxy},${HOST_IP},edgecraftrag,edgecraftrag-server
export NO_PROXY=${NO_PROXY},${HOST_IP},edgecraftrag,edgecraftrag-server
# If you have a HF mirror configured, it will be imported to the container
# export HF_ENDPOINT=https://hf-mirror.com # your HF mirror endpoint"

# Make sure all 3 folders have 1000:1000 permission, otherwise
export DOC_PATH=${PWD}/tests
export TMPFILE_PATH=${PWD}/tests
chown 1000:1000 ${MODEL_PATH} ${DOC_PATH} ${TMPFILE_PATH}
# In addition, also make sure the .cache folder has 1000:1000 permission, otherwise
chown 1000:1000 -R $HOME/.cache
```

### Deploy the Service on Arc B60 Using Docker Compose

```bash
# vLLM envs
export TP=4 # for multi GPU, you can change TP value
export ZE_AFFINITY_MASK=0,1,2,3 # for multi GPU, you can export ZE_AFFINITY_MASK=0,1,2...
docker compose --profile b60 -f docker_compose/intel/gpu/arc/compose.yaml up -d
```
