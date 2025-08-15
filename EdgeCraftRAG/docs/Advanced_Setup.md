# Edge Craft Retrieval-Augmented Generation Advanced Setup

## Query Search

Query Search features allow EC-RAG to do query pre-process before retrieval and reranking. To enable query search, vllm inference is required. Chinese version is available in [Query Search Zh](Query_Search_Zh.md)

### 1. Sub-question file(s) example

Sub-question files need to end with `.json` and follow json file format: main question as json key, sub-questions as json value. See below example:

```json
{
  "Issue1": "Sub-question1.1? Sub-question1.2?",
  "Issue2": "Sub-question2.1? Sub-question2.2? Sub-question2.3?"
}
```

> Note: 1. At lease one sub-question file is required. 2. Increasing main question amount would increase query time for EC-RAG.

### 2. Sub-question file(s) location

All sub-question files need to be placed under `${TMPFILE_PATH}/configs/search_dir`.

### 3. Config file example

Configure file includes variables such as prompts, temperature, etc.

`instruction`, `input_template`, `output_template` would affect final prompt for query search.
`json_key` and `json_levels` are related to each other. For example, if `json_key` is set to "similarity", `json_levels` need list options for "similarity", such as "Low, Medium, High".

One example for DeesSeep-R1-Distill-Qwen-32B configs is listed below:

```yaml
query_matcher:
  instructions: "Decide similarity of two queries. For exactly the same, mark as High, for totally different, mark as Low.\n"
  input_template: "<query> {} </query>\n<query> {} </query>\n"
  output_template: "output from {json_levels}.\n"
  json_key: "similarity"
  json_levels: ["Low", "Medium", "High"]
  temperature: 3.7
```

### 4. Config file location

Config file needs to be placed under `${TMPFILE_PATH}/configs` and named as `search_config.yaml`, which gives final path as `${TMPFILE_PATH}/configs/search_config.yaml`.

## OpenVINO Local Inference

EC-RAG support using local OpenVINO models to do inference, please follow below steps to run local inference:

### 1. (Optional) Build Docker Images for Mega Service, Server and UI by your own

**All the docker images can be automatically‌ pulled**, If you want to build the images by your own, please follow the steps:

```bash
git clone https://github.com/opea-project/GenAIExamples.git
cd GenAIExamples/EdgeCraftRAG
docker build --build-arg http_proxy=$http_proxy --build-arg https_proxy=$https_proxy --build-arg no_proxy="$no_proxy" -t opea/edgecraftrag:latest -f Dockerfile .
docker build --build-arg http_proxy=$http_proxy --build-arg https_proxy=$https_proxy --build-arg no_proxy="$no_proxy" -t opea/edgecraftrag-server:latest -f Dockerfile.server .
docker build --build-arg http_proxy=$http_proxy --build-arg https_proxy=$https_proxy --build-arg no_proxy="$no_proxy" -t opea/edgecraftrag-ui:latest -f ui/docker/Dockerfile.ui .
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

export DOC_PATH=${PWD} # Your doc path for uploading a dir of files
export TMPFILE_PATH=${PWD} # Your UI cache path for transferring files

# Check group id of video and render
export VIDEOGROUPID=$(getent group video | cut -d: -f3)
export RENDERGROUPID=$(getent group render | cut -d: -f3)

# If you have a proxy configured, uncomment below line
# export no_proxy=${no_proxy},${HOST_IP},edgecraftrag,edgecraftrag-server
# export NO_PROXY=${NO_PROXY},${HOST_IP},edgecraftrag,edgecraftrag-server
# If you have a HF mirror configured, it will be imported to the container
# export HF_ENDPOINT=https://hf-mirror.com # your HF mirror endpoint"

# By default, the ports of the containers are set, uncomment if you want to change
# export MEGA_SERVICE_PORT=16011
# export PIPELINE_SERVICE_PORT=16010
# export UI_SERVICE_PORT="8082"

# Make sure all 3 folders have 1000:1000 permission, otherwise
# chown 1000:1000 ${MODEL_PATH} ${DOC_PATH} ${TMPFILE_PATH}
# In addition, also make sure the .cache folder has 1000:1000 permission, otherwise
# chown 1000:1000 -R $HOME/.cache
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

# Launch EC-RAG service with compose
docker compose -f docker_compose/intel/gpu/arc/compose.yaml up -d
```

## Multi-ARC Setup

EC-RAG support run inference with multi-ARC in multiple isolated containers
Docker Images preparation is the same as local inference section, please refer to [Build Docker Images](#1-optional-build-docker-images-for-mega-service-server-and-ui-by-your-own)
Model preparation is the same as vLLM inference section, please refer to [Prepare models](../docker_compose/intel/gpu/arc/README.md#2-prepare-models)
After docker images preparation and model preparation, please follow below steps to run multi-ARC Setup(Below steps show 2 vLLM container(2 DP) with multi Intel Arc GPUs):

### 1. Prepare env variables and configurations

#### Prepare env variables for vLLM deployment

```bash
ip_address=$(hostname -I | awk '{print $1}')
# Use `ip a` to check your active ip
export HOST_IP=$ip_address # Your host ip

# The default LLM_MODEL_PATH is "${MODEL_PATH}/${LLM_MODEL}", you can change to your model path
# export LLM_MODEL_PATH= # change to your model path
export DOC_PATH=${PWD} # Your doc path for uploading a dir of files
export TMPFILE_PATH=${PWD} # Your UI cache path for transferring files

# Check group id of video and render
export VIDEOGROUPID=$(getent group video | cut -d: -f3)
export RENDERGROUPID=$(getent group render | cut -d: -f3)

# If you have a proxy configured, uncomment below line
# export no_proxy=${no_proxy},${HOST_IP},edgecraftrag,edgecraftrag-server
# export NO_PROXY=${NO_PROXY},${HOST_IP},edgecraftrag,edgecraftrag-server
# If you have a HF mirror configured, it will be imported to the container
# export HF_ENDPOINT=https://hf-mirror.com # your HF mirror endpoint"

# By default, the ports of the containers are set, uncomment if you want to change
# export MEGA_SERVICE_PORT=16011
# export PIPELINE_SERVICE_PORT=16010
# export UI_SERVICE_PORT="8082"

# Make sure all 3 folders have 1000:1000 permission, otherwise
# chown 1000:1000 ${MODEL_PATH} ${DOC_PATH} ${TMPFILE_PATH}
# In addition, also make sure the .cache folder has 1000:1000 permission, otherwise
# chown 1000:1000 -R $HOME/.cache

export NGINX_PORT=8086 # Set port for nginx
export vLLM_ENDPOINT="http://${HOST_IP}:${NGINX_PORT}"
export DP_NUM=2 # How many containers you want to start to run inference
export VLLM_SERVICE_PORT_0=8100 # You can set your own vllm service port
export VLLM_SERVICE_PORT_1=8200 # You can set your own vllm service port
export TENSOR_PARALLEL_SIZE=1 # Your Intel Arc GPU number to do TP inference
export SELECTED_XPU_0=0 # Which GPU to select to run for container 0
export SELECTED_XPU_1=1 # Which GPU to select to run for container 1

# Below are the extra env you can set for vllm
export MAX_NUM_SEQS=64 # MAX_NUM_SEQS value
export MAX_NUM_BATCHED_TOKENS=5000 # MAX_NUM_BATCHED_TOKENS value
export MAX_MODEL_LEN=5000 # MAX_MODEL_LEN value
export LOAD_IN_LOW_BIT=fp8 # the weight type value, expected: sym_int4, asym_int4, sym_int5, asym_int5 or sym_int8
export CCL_DG2_USM="" # Need to set to 1 on Core to enable USM (Shared Memory GPUDirect). Xeon supports P2P and doesn't need this.
```

### 2. Generate nginx config file and compose yaml file

```bash
# Generate your nginx config file
# nginx-conf-generator.sh requires 2 parameters: DP_NUM and output filepath
bash nginx/nginx-conf-generator.sh $DP_NUM nginx/nginx.conf # You can change TEMP_FILE_PATH to your reference
# set NGINX_CONFIG_PATH
export NGINX_CONFIG_PATH="${PWD}/nginx/nginx.conf"

# Generate compose_vllm.yaml file
# multi-arc-yaml-generator.sh requires 2 parameters: DP_NUM and output filepath
bash docker_compose/intel/gpu/arc/multi-arc-yaml-generator.sh $DP_NUM docker_compose/intel/gpu/arc/compose_vllm.yaml
```

### 3. Start Edge Craft RAG Services with Docker Compose

This section is the same as default vLLM inference section, please refer to [Start Edge Craft RAG Services with Docker Compose](../docker_compose/intel/gpu/arc/README.md#deploy-the-service-using-docker-compose)
