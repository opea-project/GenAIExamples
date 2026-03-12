# Edge Craft Retrieval-Augmented Generation Advanced Setup

[中文版](Advanced_Setup_zh.md)

## Build Docker Images for Mega Service, Server and UI by your own

**All the docker images can be automatically‌ pulled**, if you want to build the images by your own, please use helper script:

```bash
# Build all images
./tools/build_images.sh

# Build a single image
./tools/build_images.sh mega
./tools/build_images.sh server
./tools/build_images.sh ui

# Build multiple selected images
./tools/build_images.sh mega server
```

## Manual deployment details for Arc platform

### Prepare models

There are 3 models need to be prepared: **Embedding**, **Reranking**, **LLM**  
You'll need to decide the inferencing framework for these models.

#### Embedding and Reranking

Embedding and reranking are usually servered by local OpenVINO inferencing, to prepare these 2 models:

```bash
# Prepare models for embedding, reranking:
export MODEL_PATH="${PWD}/models" # Your model path for embedding, reranking and LLM models
mkdir -p $MODEL_PATH
pip install --upgrade --upgrade-strategy eager "optimum[openvino]"
optimum-cli export openvino -m BAAI/bge-small-en-v1.5 ${MODEL_PATH}/BAAI/bge-small-en-v1.5 --task sentence-similarity
optimum-cli export openvino -m BAAI/bge-reranker-large ${MODEL_PATH}/BAAI/bge-reranker-large --task text-classification
```

#### LLM

##### openVINO

If you have Core Ultra platform only, please prepare openVINO models:  
You can also run openVINO models on discrete GPU.

```bash
# Prepare LLM model for openVINO
optimum-cli export openvino --model Qwen/Qwen3-8B ${MODEL_PATH}/Qwen/Qwen3-8B/INT4_compressed_weights --task text-generation-with-past --weight-format int4 --group-size 128 --ratio 0.8
```

##### vLLM

Alternatively, if you have discrete GPU and want to use vLLM, please prepare models for vLLM:

```bash
# Prepare LLM model for vLLM
export LLM_MODEL="Qwen/Qwen3-8B" # Your model id
pip install modelscope
modelscope download --model $LLM_MODEL --local_dir "${MODEL_PATH}/${LLM_MODEL}"
# Optionally, you can also download models with huggingface:
# pip install -U huggingface_hub
# huggingface-cli download $LLM_MODEL --local-dir "${MODEL_PATH}/${LLM_MODEL}"
```

### Prepare env variables and configurations

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
chown 1000:1000 ${MODEL_PATH} ${DOC_PATH} ${TMPFILE_PATH}
# In addition, also make sure the .cache folder has 1000:1000 permission, otherwise
chown 1000:1000 -R $HOME/.cache
```

Set Milvus DB and chat history round for inference:

```bash
# EC-RAG support Milvus as persistent database, by default milvus is disabled, you can choose to set MILVUS_ENABLED=1 to enable it
export MILVUS_ENABLED=0
# If you enable Milvus, the default storage path is PWD, uncomment if you want to change:
# export DOCKER_VOLUME_DIRECTORY= # change to your preference

# EC-RAG support chat history round setting, by default chat history is disabled, you can set CHAT_HISTORY_ROUND to control it
# export CHAT_HISTORY_ROUND= # change to your preference
```

### Deploy the Service on Intel GPU Using Docker Compose

#### Option a. Deploy openVINO LLM based EC-RAG for Core Ultra, Arc B60, Arc A770

```bash
docker compose -f docker_compose/intel/gpu/arc/compose.yaml up -d
```

#### Option b.1. Deploy vLLM based EC-RAG for Arc B60

```bash
docker compose --profile b60 -f docker_compose/intel/gpu/arc/compose.yaml up -d
```

#### Option b.2. Deploy vLLM based EC-RAG for Arc A770

```bash
docker compose --profile a770 -f docker_compose/intel/gpu/arc/compose.yaml up -d
```

### 6. Cleanup the Deployment (Manual)

To stop the containers associated with the deployment, execute the following command:

```bash
docker compose -f docker_compose/intel/gpu/arc/compose.yaml down
```

All the EdgeCraftRAG containers will be stopped and then removed on completion of the `down` command.

## EC-RAG with Kbadmin

EC-RAG support kbadmin as a knowledge base manager  
Please make sure all the kbadmin services have been launched
EC-RAG Docker Images preparation is the same as local inference section, please refer to [Build Docker Images](#build-docker-images-for-mega-service-server-and-ui-by-your-own)
Model preparation is the same as Arc manual deployment section, please refer to [Prepare models](#prepare-models)

### 1. Start Edge Craft RAG Services with Docker Compose

This section is the same as Arc manual deployment section, please refer to [Prepare env variables and configurations](#prepare-env-variables-and-configurations) and [Deploy the Service on Intel GPU Using Docker Compose](#deploy-the-service-on-intel-gpu-using-docker-compose)

### 2. Access Kbadmin UI

please refer to [ChatQnA with Kbadmin in UI](./Explore_Edge_Craft_RAG.md#chatqna-with-kbadmin-in-ui)

## Deploy EC-RAG on multi GPUs

In this sample, we will use Qwen3-30B-A3B deployment on 4 Arc B60 GPUs as an example.
Before started, please prepare models into MODEL_PATH and prepare docker images

```bash
export MODEL_PATH="${PWD}/models" # Your model path
export LLM_MODEL="Qwen/Qwen3-30B-A3B"
pip install modelscope
modelscope download --model $LLM_MODEL --local_dir "${MODEL_PATH}/${LLM_MODEL}"

# vLLM envs
export TP=4 # for multi GPU, you can change TP value
export ZE_AFFINITY_MASK=0,1,2,3 # for multi GPU, you can export ZE_AFFINITY_MASK=0,1,2...
docker compose --profile b60 -f docker_compose/intel/gpu/arc/compose.yaml up -d
```
