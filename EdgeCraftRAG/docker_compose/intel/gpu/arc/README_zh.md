# 在 Intel® Arc® 平台上部署 Edge Craft 检索增强生成（EC-RAG）示例

[English](README.md)

本文档介绍了在 Intel® Arc® 平台上部署 Edge Craft 检索增强生成服务的流程。该示例包含以下部分：

- [EdgeCraftRAG 快速开始部署](#edgecraftrag-快速开始部署)：演示如何在 Intel® Arc® 平台上快速部署 Edge Craft 检索增强生成服务/流水线。
- [EdgeCraftRAG Docker Compose 文件](#edgecraftrag-docker-compose-文件)：说明一些示例部署及其 docker compose 文件。
- [EdgeCraftRAG 服务配置](#edgecraftrag-服务配置)：说明服务以及可进行的配置变更。

## EdgeCraftRAG 快速开始部署

本节介绍如何在 Intel® Arc® 平台上手动快速部署并测试 EdgeCraftRAG 服务。基本步骤如下：

1. [前置条件](#1-前置条件)
2. [获取代码](#2-获取代码)
3. [准备模型](#3-准备模型)
4. [准备环境变量和配置](#4-准备环境变量和配置)
5. [使用 Docker Compose 在 Arc GPU 上部署服务](#5-使用-docker-compose-在-intel-gpu-上部署服务)
6. [访问 UI](#6-访问-ui)
7. [清理部署](#7-清理部署)

### 1. 前置条件

EC-RAG 支持 vLLM 部署（默认方式）以及面向 Intel Arc GPU 和 Core Ultra 平台的本地 OpenVINO 部署。前置条件如下：

#### Core Ultra
**操作系统**：Ubuntu 24.04 或更高版本  
**驱动与库**：请参考 [Installing Client GPUs on Ubuntu Desktop](https://dgpu-docs.intel.com/driver/client/overview.html#installing-client-gpus-on-ubuntu-desktop)  
**可用推理框架**：openVINO

#### Intel Arc B60
**操作系统**：Ubuntu 25.04 Desktop（适用于 Core Ultra 和 Xeon-W），Ubuntu 25.04 Server（适用于 Xeon-SP）。  
**驱动与库**：详细安装请参考 [Install Bare Metal Environment](https://github.com/intel/llm-scaler/tree/main/vllm#11-install-bare-metal-environment)  
**可用推理框架**：openVINO、vLLM

#### Intel Arc A770
**操作系统**：Ubuntu Server 22.04.1 或更高版本（至少 6.2 LTS 内核）  
**驱动与库**：详细驱动与库安装请参考 [Installing GPUs Drivers](https://dgpu-docs.intel.com/driver/installation-rolling.html#installing-gpu-drivers)  
**可用推理框架**：openVINO、vLLM

### 2. 获取代码

克隆 GenAIExample 仓库，并进入 EdgeCraftRAG 在 Intel® Arc® 平台上的 Docker Compose 文件与配套脚本目录：

```
git clone https://github.com/opea-project/GenAIExamples.git
cd GenAIExamples/EdgeCraftRAG
```

> **注意**：如果你想切换到某个发布版本，例如 v1.5：
>
>```
>git checkout v1.5
>```

### 3. 准备模型

需要准备 3 个模型：**Embedding**、**Reranking**、**LLM**。  
你需要为这些模型选择推理框架。

#### Embedding 和 Reranking

Embedding 和 reranking 通常由本地 OpenVINO 推理提供服务。准备这 2 个模型：

```bash
# 准备 embedding、reranking 模型：
export MODEL_PATH="${PWD}/models" # embedding、reranking、LLM 模型路径
mkdir -p $MODEL_PATH
pip install --upgrade --upgrade-strategy eager "optimum[openvino]"
optimum-cli export openvino -m BAAI/bge-small-en-v1.5 ${MODEL_PATH}/BAAI/bge-small-en-v1.5 --task sentence-similarity
optimum-cli export openvino -m BAAI/bge-reranker-large ${MODEL_PATH}/BAAI/bge-reranker-large --task text-classification
```

#### LLM

##### openVINO
如果你只有 Core Ultra 平台，请准备 openVINO 模型：
你也可以在独立 GPU 上运行 openVINO 模型。

```bash
# 准备 openVINO 的 LLM 模型
optimum-cli export openvino --model Qwen/Qwen3-8B ${MODEL_PATH}/Qwen/Qwen3-8B/INT4_compressed_weights --task text-generation-with-past --weight-format int4 --group-size 128 --ratio 0.8
```

##### vLLM
另外，如果你有独立显卡，可以为 vLLM 准备模型：

```bash
# 准备 vLLM 的 LLM 模型
export LLM_MODEL="Qwen/Qwen3-8B" # 你的模型 id
pip install modelscope
modelscope download --model $LLM_MODEL --local_dir "${MODEL_PATH}/${LLM_MODEL}"
# 可选：你也可以用 huggingface 下载模型：
# pip install -U huggingface_hub
# huggingface-cli download $LLM_MODEL --local-dir "${MODEL_PATH}/${LLM_MODEL}"
```

### 4. 准备环境变量和配置

#### 为部署准备环境变量

```bash
ip_address=$(hostname -I | awk '{print $1}')
# 使用 `ip a` 查看当前活动 ip
export HOST_IP=$ip_address # 主机 ip

# 查看 video 与 render 的 group id
export VIDEOGROUPID=$(getent group video | cut -d: -f3)
export RENDERGROUPID=$(getent group render | cut -d: -f3)

# 若已配置代理，执行以下命令
export no_proxy=${no_proxy},${HOST_IP},edgecraftrag,edgecraftrag-server
export NO_PROXY=${NO_PROXY},${HOST_IP},edgecraftrag,edgecraftrag-server
# 如果配置了 HF 镜像，会传入容器
# export HF_ENDPOINT=https://hf-mirror.com # 你的 HF 镜像地址"

# 确保以下 3 个文件夹权限为 1000:1000，否则
export DOC_PATH=${PWD}/tests
export TMPFILE_PATH=${PWD}/tests
chown 1000:1000 ${MODEL_PATH} ${DOC_PATH} ${TMPFILE_PATH}
# 此外还要确保 .cache 文件夹权限为 1000:1000，否则
chown 1000:1000 -R $HOME/.cache
```

如需更高级的环境变量和配置，请参考 [Prepare env variables for vLLM deployment](../../../../docs/Advanced_Setup.md#prepare-env-variables-for-vllm-deployment)

为推理设置 Milvus 数据库与聊天历史轮数：

```bash
# EC-RAG 支持 Milvus 持久化数据库，默认关闭；可设置 MILVUS_ENABLED=1 开启
export MILVUS_ENABLED=0
# 如果启用 Milvus，默认存储路径为 PWD，如需修改请取消注释：
# export DOCKER_VOLUME_DIRECTORY= # 按需修改

# EC-RAG 支持聊天历史轮数设置，默认关闭；可通过 CHAT_HISTORY_ROUND 控制
# export CHAT_HISTORY_ROUND= # 按需修改
```

### 5. 使用 Docker Compose 在 Intel GPU 上部署服务

#### Option a. 为 Core Ultra、Arc B60、Arc A770 部署基于 openVINO LLM 的 EC-RAG

请确保已准备好 [openVINO 模型](#openvino)

```bash
docker compose -f docker_compose/intel/gpu/arc/compose.yaml up -d
```

#### Option b.1. 为 Arc B60 部署基于 vLLM 的 EC-RAG

请确保已准备好 [vLLM 模型](#vllm)

```bash
docker compose --profile b60 -f docker_compose/intel/gpu/arc/compose.yaml up -d
```

#### Option b.2. 为 Arc A770 部署基于 vLLM 的 EC-RAG

请确保已准备好 [vLLM 模型](#vllm)

```bash
docker compose --profile a770 -f docker_compose/intel/gpu/arc/compose.yaml up -d
```

### 6. 访问 UI

打开浏览器访问 http://${HOST_IP}:8082

> 浏览器应运行在与控制台相同的主机上；否则你需要使用主机域名而不是 ${HOST_IP} 来访问 UI。

下图为 UI 首页。有关 UI 操作和 EC-RAG 设置的详细说明，请参考 [Explore_Edge_Craft_RAG](../../../../docs/Explore_Edge_Craft_RAG.md)
![front_page](../../../../assets/img/front_page.png)

### 7. 清理部署

若要停止与本次部署关联的容器，请执行以下命令：

```
docker compose -f docker_compose/intel/gpu/arc/compose.yaml down
```

执行完 `down` 命令后，所有 EdgeCraftRAG 容器都会停止并被移除。

## EdgeCraftRAG Docker Compose 文件

`compose.yaml` 是默认的 compose 文件，使用 tgi 作为服务框架。

| 服务名称            | 镜像名称                                 |
| ------------------- | ---------------------------------------- |
| etcd                | quay.io/coreos/etcd:v3.5.5               |
| minio               | minio/minio:RELEASE.2023-03-20T20-16-18Z |
| milvus-standalone   | milvusdb/milvus:v2.4.6                   |
| edgecraftrag-server | opea/edgecraftrag-server:latest          |
| edgecraftrag-ui     | opea/edgecraftrag-ui:latest              |
| ecrag               | opea/edgecraftrag:latest                 |

## EdgeCraftRAG 服务配置

下表全面概述了示例 Docker Compose 文件中各类部署所使用的 EdgeCraftRAG 服务。表中每一行代表一个独立服务，详细说明了可用镜像及其在部署架构中的功能描述。

| 服务名称            | 可选镜像名称                             | 可选 | 描述                                                                                             |
| ------------------- | ---------------------------------------- | ---- | ------------------------------------------------------------------------------------------------ |
| etcd                | quay.io/coreos/etcd:v3.5.5               | 否   | 提供分布式键值存储，用于服务发现和配置管理。                                                     |
| minio               | minio/minio:RELEASE.2023-03-20T20-16-18Z | 否   | 提供对象存储服务，用于存储文档和模型文件。                                                       |
| milvus-standalone   | milvusdb/milvus:v2.4.6                   | 否   | 提供向量数据库能力，用于管理 embedding 和相似度检索。                                            |
| edgecraftrag-server | opea/edgecraftrag-server:latest          | 否   | 作为 EdgeCraftRAG 服务后端，具体形态随部署方式不同而变化。                                       |
| edgecraftrag-ui     | opea/edgecraftrag-ui:latest              | 否   | 提供 EdgeCraftRAG 服务的用户界面。                                                               |
| ecrag               | opea/edgecraftrag:latest                 | 否   | 作为反向代理，管理 UI 与后端服务之间的流量。                                                     |
