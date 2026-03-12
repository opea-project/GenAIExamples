# Edge Craft 检索增强生成（EC-RAG）高级部署说明

[English](Advanced_Setup.md)

## 自行构建 Mega Service、Server 和 UI 镜像

**所有 Docker 镜像都可以自动拉取**。如果你希望自行构建镜像，请使用辅助脚本：

```bash
# 构建全部镜像
./tools/build_images.sh

# 单独构建某个镜像
./tools/build_images.sh mega
./tools/build_images.sh server
./tools/build_images.sh ui

# 组合构建多个镜像
./tools/build_images.sh mega server
```

## Arc 平台手动部署详细说明

### 准备模型

需要准备 3 类模型：**Embedding**、**Reranking**、**LLM**。  
你需要根据场景选择对应推理框架。

#### Embedding 与 Reranking

Embedding 与 Reranking 通常由本地 OpenVINO 推理提供，可按如下方式准备：

```bash
# 准备 embedding、reranking 模型：
export MODEL_PATH="${PWD}/models" # embedding、reranking、LLM 模型目录
mkdir -p $MODEL_PATH
pip install --upgrade --upgrade-strategy eager "optimum[openvino]"
optimum-cli export openvino -m BAAI/bge-small-en-v1.5 ${MODEL_PATH}/BAAI/bge-small-en-v1.5 --task sentence-similarity
optimum-cli export openvino -m BAAI/bge-reranker-large ${MODEL_PATH}/BAAI/bge-reranker-large --task text-classification
```

#### LLM

##### openVINO

如果仅使用 Core Ultra 平台，请准备 openVINO 模型：  
你也可以在独立 GPU 上运行 openVINO 模型。

```bash
# 准备 openVINO 的 LLM 模型
optimum-cli export openvino --model Qwen/Qwen3-8B ${MODEL_PATH}/Qwen/Qwen3-8B/INT4_compressed_weights --task text-generation-with-past --weight-format int4 --group-size 128 --ratio 0.8
```

##### vLLM

如果你有独立 GPU 并希望使用 vLLM，可按如下方式准备模型：

```bash
# 准备 vLLM 的 LLM 模型
export LLM_MODEL="Qwen/Qwen3-8B" # 模型 ID
pip install modelscope
modelscope download --model $LLM_MODEL --local_dir "${MODEL_PATH}/${LLM_MODEL}"
# 可选：也可以使用 huggingface 下载模型：
# pip install -U huggingface_hub
# huggingface-cli download $LLM_MODEL --local-dir "${MODEL_PATH}/${LLM_MODEL}"
```

### 准备环境变量与配置

```bash
ip_address=$(hostname -I | awk '{print $1}')
# 可使用 `ip a` 查看当前活动 ip
export HOST_IP=$ip_address # 主机 IP

# 获取 video / render 组 ID
export VIDEOGROUPID=$(getent group video | cut -d: -f3)
export RENDERGROUPID=$(getent group render | cut -d: -f3)

# 如果你配置了代理，请执行以下命令
export no_proxy=${no_proxy},${HOST_IP},edgecraftrag,edgecraftrag-server
export NO_PROXY=${NO_PROXY},${HOST_IP},edgecraftrag,edgecraftrag-server
# 如果你配置了 HF 镜像，会被注入容器
# export HF_ENDPOINT=https://hf-mirror.com # 你的 HF 镜像地址

# 确保以下 3 个目录权限为 1000:1000
export DOC_PATH=${PWD}/tests
export TMPFILE_PATH=${PWD}/tests
chown 1000:1000 ${MODEL_PATH} ${DOC_PATH} ${TMPFILE_PATH}
# 同时确保 .cache 目录权限为 1000:1000
chown 1000:1000 -R $HOME/.cache
```

设置 Milvus 和聊天历史轮数：

```bash
# EC-RAG 支持 Milvus 持久化数据库，默认关闭；设置 MILVUS_ENABLED=1 可开启
export MILVUS_ENABLED=0
# 启用 Milvus 时，默认存储路径为 PWD，如需修改请取消注释：
# export DOCKER_VOLUME_DIRECTORY= # 按需修改

# EC-RAG 支持聊天历史轮数，默认关闭；可通过 CHAT_HISTORY_ROUND 控制
# export CHAT_HISTORY_ROUND= # 按需修改
```

### 使用 Docker Compose 在 Intel GPU 上部署服务

#### 选项 a：为 Core Ultra / Arc B60 / Arc A770 部署基于 openVINO LLM 的 EC-RAG

```bash
docker compose -f docker_compose/intel/gpu/arc/compose.yaml up -d
```

#### 选项 b.1：为 Arc B60 部署基于 vLLM 的 EC-RAG

```bash
docker compose --profile b60 -f docker_compose/intel/gpu/arc/compose.yaml up -d
```

#### 选项 b.2：为 Arc A770 部署基于 vLLM 的 EC-RAG

```bash
docker compose --profile a770 -f docker_compose/intel/gpu/arc/compose.yaml up -d
```

### 6. 清理部署（手动）

若要停止本次部署相关容器，请执行：

```bash
docker compose -f docker_compose/intel/gpu/arc/compose.yaml down
```

执行 `down` 后，EdgeCraftRAG 相关容器将停止并移除。

## EC-RAG 与 Kbadmin

EC-RAG 支持 kbadmin 作为知识库管理器。  
请先确保所有 kbadmin 服务已启动。  
EC-RAG 镜像准备与本地推理章节一致，请参考 [自行构建镜像](#自行构建-mega-serviceserver-和-ui-镜像)。  
模型准备与 Arc 手动部署章节一致，请参考 [准备模型](#准备模型)。

### 1. 使用 Docker Compose 启动 Edge Craft RAG 服务

此部分与 Arc 手动部署一致，请参考 [准备环境变量与配置](#准备环境变量与配置) 和 [使用 Docker Compose 在 Intel GPU 上部署服务](#使用-docker-compose-在-intel-gpu-上部署服务)。

### 2. 访问 Kbadmin UI

请参考 [ChatQnA with Kbadmin in UI](./Explore_Edge_Craft_RAG.md#chatqna-with-kbadmin-in-ui)。

## 在多 GPU 上部署 EC-RAG

本示例以 4 张 Arc B60 部署 Qwen3-30B-A3B 为例。  
开始前请先准备模型到 `MODEL_PATH` 并准备好 Docker 镜像。

```bash
export MODEL_PATH="${PWD}/models" # 模型路径
export LLM_MODEL="Qwen/Qwen3-30B-A3B"
pip install modelscope
modelscope download --model $LLM_MODEL --local_dir "${MODEL_PATH}/${LLM_MODEL}"

# vLLM 环境变量
export TP=4 # 多卡时可按需调整 TP
export ZE_AFFINITY_MASK=0,1,2,3 # 多卡时可按需调整
docker compose --profile b60 -f docker_compose/intel/gpu/arc/compose.yaml up -d
```
