# 快速启动指南

## 1. 环境准备

EC-RAG支持通过vllm或本地OpenVINO在Intel Arc GPU上进行部署，其中vllm为系统默认方法。

具体环境和系统需求如下：

硬件环境：Intel Arc A770

操作系统：Ubuntu server 22.04.1或更新的版本（至少需要6.2LTS kernel）

驱动和库依赖：请参考[如何为client GPU安装驱动](https://dgpu-docs.intel.com/driver/client/overview.html)

以下步骤均基于使用vllm作为推理引擎，如果您选择使用OpenVINO，可以参考[OpenVINO本地部署指南](Advanced_Setup.md#openvino-local-inference)

## 2. 准备模型

您可以使用如下命令下载和准备所需的模型：

```bash
git clone https://github.com/opea-project/GenAIExamples.git
cd GenAIExamples/EdgeCraftRAG
# 准备embedding和reranking的模型：
export MODEL_PATH="${PWD}/models" # 用于存储模型的路径
mkdir -p $MODEL_PATH
pip install --upgrade --upgrade-strategy eager "optimum[openvino]"
optimum-cli export openvino -m BAAI/bge-small-en-v1.5 ${MODEL_PATH}/BAAI/bge-small-en-v1.5 --task sentence-similarity
optimum-cli export openvino -m BAAI/bge-reranker-large ${MODEL_PATH}/BAAI/bge-reranker-large --task text-classification

# 准备LLM模型
export LLM_MODEL="Qwen/Qwen3-8B" # 所需的模型ID
pip install modelscope
modelscope download --model $LLM_MODEL --local_dir "${MODEL_PATH}/${LLM_MODEL}"
# 或者，您也可以通过huggingface下载模型：
# pip install -U huggingface_hub
# huggingface-cli download $LLM_MODEL --local-dir "${MODEL_PATH}/${LLM_MODEL}"
```

## 3. 准备环境变量和配置文件

下面的步骤默认使用单一Intel Arc GPU进行推理，如果您需要使用多GPU，请参考[多GPU搭建指南](Advanced_Setup.md#multi-arc-setup)

### 为vllm部署准备环境变量

```bash
ip_address=$(hostname -I | awk '{print $1}')
# 使用`ip a`命令来查看ip
export HOST_IP=$ip_address

# 查看并设定video和render的id
export VIDEOGROUPID=$(getent group video | cut -d: -f3)
export RENDERGROUPID=$(getent group render | cut -d: -f3)

# 您可以使用如下命令配置代理：
# export no_proxy=${no_proxy},${HOST_IP},edgecraftrag,edgecraftrag-server
# export NO_PROXY=${NO_PROXY},${HOST_IP},edgecraftrag,edgecraftrag-server

# 您可以使用如下命令配置HF镜像：
# export HF_ENDPOINT=https://hf-mirror.com # your HF mirror endpoint"

# 请使用chown 1000:1000 ${MODEL_PATH} ${PWD}来确保三个文件都有1000:1000权限
# 请使用chown 1000:1000 -R $HOME/.cache命令来确保.cache有1000:1000权限
```

如果您希望对环境变量进行更高阶的配置，可以参考[vllm环境变量准备指南](Advanced_Setup.md#prepare-env-variables-for-vllm-deployment)

### 生成nginx配置文件

```bash
export VLLM_SERVICE_PORT_0=8100 # vllm服务端口，可以自定义设置

# 生成nginx配置文件
# nginx-conf-generator.sh脚本需要两个参数: DP_NUM 和 output filepath
bash nginx/nginx-conf-generator.sh 1 nginx/nginx.conf
# 设置 NGINX_CONFIG_PATH
export NGINX_CONFIG_PATH="${PWD}/nginx/nginx.conf"
```

## 4. 通过docker compose启动EC-RAG服务

```bash
# # EC-RAG 支持 Milvus 作为持久化数据库，可以通过设置START_MILVUS=1来打开，默认为关闭状态
export MILVUS_ENABLED=0
# 如果您启用了Milvus，默认的存储路径为PWD，可以使用下面的命令进行更改
# export DOCKER_VOLUME_DIRECTORY= # change to your preference

# 通过compose命令启动EC-RAG
docker compose -f docker_compose/intel/gpu/arc/compose_vllm.yaml up -d
```

## 5. 访问UI

打开浏览器，访问http://${HOST_IP}:8082

> 注意：浏览器应该运行在和控制台同样的主机上，否则请用域名而不是${HOST_IP}访问UI。

如下为UI首界面，您可以通过[更多关于EC-RAG的信息](Explore_Edge_Craft_RAG.md)来查看更多关于UI和EC-RAG配置的操作方法。

![front_page](../assets/img/front_page.png)

| **Deploy Method** | **LLM Engine** | **LLM Model** | **Hardware** |
| ----------------- | -------------- | ------------- | ------------ |
| Docker Compose    | vLLM           | Qwen3-8B      | Intel Arc    |
