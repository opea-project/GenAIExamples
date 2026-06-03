[English](README.md)

本目录包含 EdgeCraftRAG 的部署、启动和镜像构建脚本。

# 1.脚本介绍

本目录主要脚本如下：

- `quick_start.sh`：推荐新用户使用的一键部署脚本，支持自动安装与交互引导
- `bootstrap.sh`：非交互部署编排器（可独立使用，也可由 quick_start 调用）
- `model_download.sh`：模型准备脚本（支持 `vllm` / `ov` 模式，支持可选参数 `model_id` 和 `model_path`）
- `run_ov_baremetal.sh`：OpenVINO 裸金属启动脚本
- `run_ov_container.sh`：OpenVINO 容器启动脚本
- `run_vllm_baremetal.sh`：vLLM 裸金属启动脚本
- `run_vllm_container.sh`：vLLM 容器启动脚本
- `run_ovms_baremetal.sh`：OVMS 裸金属启动脚本
- `run_ovms_container.sh`：OVMS 容器启动脚本
- `build_images.sh`：容器镜像编译脚本

部署方式说明：

| 方式 | 描述 | 环境要求 | Milvus 支持 |
|------|------|----------|-------------|
| baremetal（裸金属） | 以 Python 进程方式启动服务 | Python 3.10+ | 否（仅内存） |
| container（容器） | 以 Docker 容器方式启动服务 | Docker / Docker Compose | 是（默认启用） |

提示：如需使用 Milvus，请选择容器部署。

# 2.快速部署脚本（新用户）

## 2.1 一键快速部署

推荐在 `EdgeCraftRAG` 根目录执行：

```bash
./tools/quick_start.sh
```

脚本会按以下默认行为执行：

- 进入非交互模式（non-interactive）
- 推理后端默认选择 OpenVINO（`INFERENCE_BACKEND` 未设置时，脚本会自动解析为 `openvino`）
- 部署方式默认是 baremetal（`DEPLOYMENT_METHOD` 默认 `baremetal`）

在 baremetal 默认模式下，会自动执行：

- 创建并激活 `EdgeCraftRAG/ecrag_venv` 虚拟环境（若不存在）
- 校验 Python 版本（要求 3.10+，推荐 3.10/3.11）
- 检查并安装关键 Python 依赖
- 在裸金属 UI 启动需要时检查并安装 `npm`
- 校验 Intel GPU 驱动/运行时，若缺失则在 apt 系统上自动安装
- 检查并自动下载缺失模型（embedding、reranker、OpenVINO LLM）
- 在调用 `bootstrap.sh` 前将本次部署环境快照写入 `workspace/bootstrap.env`
- 调用 `bootstrap.sh` 启动服务

对于 vLLM 部署或 container 部署方式，脚本会在部署前校验 Docker 与 Docker Compose。
在 Ubuntu 24.04 上，如果 Docker 或 Docker Compose 缺失，脚本会尝试自动安装并启动/启用 Docker 服务。

如需跳过 Intel GPU 驱动/运行时校验，可使用：

```bash
./tools/quick_start.sh --skip-gpu-driver-check
```

等价环境变量：

```bash
export SKIP_INTEL_GPU_DRIVER_CHECK=1
# 或保留校验但禁用自动安装：
export AUTO_INSTALL_INTEL_GPU_DRIVER=0
./tools/quick_start.sh
```

如需禁用 baremetal 准备阶段的 npm 自动安装，可使用：

```bash
export AUTO_INSTALL_NPM=0
./tools/quick_start.sh
```

启动成功后，终端会输出 UI 访问地址，例如：

```text
UI access URL: http://${HOST_IP}:8082
```

补充：如果你事先设置了 `DEPLOYMENT_METHOD=container`，脚本会跳过 venv/pip 检查，并按容器方式继续部署。

可通过环境变量覆盖：

```bash
export INFERENCE_BACKEND=openvino
export MODEL_PATH="${PWD}/workspace/models"
export DOC_PATH="${PWD}/workspace"
export TMPFILE_PATH="${PWD}/workspace"
export LLM_MODEL="Qwen/Qwen3-8B"
export HOST_IP="$(hostname -I | awk '{print $1}')"

./tools/quick_start.sh
```

按硬件选择 `INFERENCE_BACKEND`：

```bash
# OpenVINO（默认）
./tools/quick_start.sh

# vLLM_A770
export INFERENCE_BACKEND=vllm_a770
./tools/quick_start.sh

# vLLM_B60
export INFERENCE_BACKEND=vllm_b60
./tools/quick_start.sh

# OVMS
export INFERENCE_BACKEND=ovms
export OVMS_SOURCE_MODEL=OpenVINO/Qwen3-8B-int4-ov
export OVMS_MODEL_NAME=OpenVINO/Qwen3-8B-int4-ov
export OVMS_TARGET_DEVICE=GPU.0
./tools/quick_start.sh
```

对于 OVMS 部署，工具脚本会直接导出 compose 所需的 `OVMS_*` 环境变量。常见可覆盖项包括：`OVMS_SOURCE_MODEL`、`OVMS_MODEL_NAME`、`OVMS_TARGET_DEVICE`、`OVMS_TOOL_PARSER`、`OVMS_MAX_NUM_BATCHED_TOKENS`。

OVMS 相关行为说明：

- `OVMS_SOURCE_MODEL` 会保持你提供的原始模型 ID（例如 `Qwen/Qwen3-8B`），不会自动截断。
- `quick_start.sh` 与 `bootstrap.sh` 都会将 OVMS 变量写入 `workspace/bootstrap.env` 以便复用。
- 可通过 `source workspace/bootstrap.env && ./tools/bootstrap.sh` 复用同一套 OVMS 配置。

兼容说明：历史环境变量 `COMPOSE_PROFILES` 仍可使用，但新配置建议统一使用 `INFERENCE_BACKEND`。

`INFERENCE_BACKEND` 支持以下取值：

- `openvino`
- `vllm_a770`
- `vllm_b60`
- `ovms`


## 2.2 交互模式

```bash
./tools/quick_start.sh -i
```

交互模式适合首次部署或不确定参数时使用。执行 `./tools/quick_start.sh -i` 后，脚本会逐步提问并自动生成本次部署配置。

交互流程通常包括：

- 选择推理后端：OpenVINO / vLLM_A770 / vLLM_B60 / OVMS
- 选择部署方式：baremetal / container
- 配置关键参数：`HOST_IP`、`MODEL_PATH`、`DOC_PATH`、`TMPFILE_PATH`、`LLM_MODEL`
- 确认配置后开始部署，并在结束后输出访问地址

建议在以下场景使用交互模式：

- 首次安装，不熟悉环境变量名称和默认值
- 需要快速切换不同硬件或推理后端
- 希望先确认参数再执行，降低配置出错概率

示例：

```bash
cd EdgeCraftRAG
./tools/quick_start.sh -i
```

## 2.3 交互模式常见输入示例

以下示例用于说明交互过程中常见的输入内容，实际选项名称以终端提示为准。

### 示例 A：OpenVINO + baremetal（单机快速体验）

```text
部署后端: OpenVINO
部署方式: baremetal
HOST_IP: 192.168.1.20
MODEL_PATH: /home/scale/edgeai/applications.edge.ai.rag/EdgeCraftRAG/workspace/models
DOC_PATH: /home/scale/edgeai/applications.edge.ai.rag/EdgeCraftRAG/workspace
TMPFILE_PATH: /home/scale/edgeai/applications.edge.ai.rag/EdgeCraftRAG/workspace
LLM_MODEL: Qwen/Qwen3-8B
确认部署: y
```

### 示例 B：vLLM_B60 + container（需要 Milvus）

```text
部署后端: vLLM_B60
部署方式: container
HOST_IP: 192.168.1.20
MODEL_PATH: /home/scale/edgeai/applications.edge.ai.rag/EdgeCraftRAG/workspace/models
DOC_PATH: /home/scale/edgeai/applications.edge.ai.rag/EdgeCraftRAG/workspace
TMPFILE_PATH: /home/scale/edgeai/applications.edge.ai.rag/EdgeCraftRAG/workspace
LLM_MODEL: Qwen/Qwen3-8B
确认部署: y
```

### 示例 C：vLLM_A770 + container（A770 推荐）

```text
部署后端: vLLM_A770
部署方式: container
HOST_IP: 192.168.1.20
MODEL_PATH: /home/scale/edgeai/applications.edge.ai.rag/EdgeCraftRAG/workspace/models
DOC_PATH: /home/scale/edgeai/applications.edge.ai.rag/EdgeCraftRAG/workspace
TMPFILE_PATH: /home/scale/edgeai/applications.edge.ai.rag/EdgeCraftRAG/workspace
LLM_MODEL: Qwen/Qwen3-8B
确认部署: y
```

### 示例 D：OVMS + container

```text
部署后端: OVMS
部署方式: container
HOST_IP: 192.168.1.20
MODEL_PATH: /home/scale/edgeai/applications.edge.ai.rag/EdgeCraftRAG/workspace/models
DOC_PATH: /home/scale/edgeai/applications.edge.ai.rag/EdgeCraftRAG/workspace
TMPFILE_PATH: /home/scale/edgeai/applications.edge.ai.rag/EdgeCraftRAG/workspace
LLM_MODEL: Qwen/Qwen3-8B
确认部署: y
```

提示：

- 如果是远程服务器，请将 `HOST_IP` 设置为客户端可访问的地址。
- 如需持久化向量检索数据，请使用 container 部署方式。
- 若设备为 Intel Arc A770，优先选择 vLLM_A770 对应配置。

清理部署：

```bash
./tools/quick_start.sh cleanup
```

# 3.启动脚本

## 3.1 bootstrap.sh（非交互编排）

通过环境变量定义部署参数后执行：

```bash
export INFERENCE_BACKEND=openvino
export DEPLOYMENT_METHOD=baremetal
./tools/bootstrap.sh
```

使用默认值（openvino + baremetal）：

```bash
./tools/bootstrap.sh
```

配置复用：

- `quick_start.sh` 在真正部署前会写入 `workspace/bootstrap.env`。
- `bootstrap.sh` 也会保存配置，便于下次直接复用。
- 对于 OVMS，上述文件会包含 `OVMS_SOURCE_MODEL`、`OVMS_MODEL_NAME`、`OVMS_TARGET_DEVICE`、`OVMS_TOOL_PARSER` 等 `OVMS_*` 运行参数。

```bash
source workspace/bootstrap.env
./tools/bootstrap.sh
```

## 3.3 model_download.sh（模型准备）

基础用法：

```bash
./tools/model_download.sh <mode> [model_id] [model_path]
```

模式说明：

- `vllm`：准备 embedding/reranker 的 OpenVINO 模型 + vLLM LLM 模型
- `ov`：准备 embedding/reranker 的 OpenVINO 模型 + OpenVINO INT4 LLM 模型

可选参数：

- `model_id`：仅对本次执行覆盖 `LLM_MODEL`
- `model_path`：仅对本次执行覆盖 `MODEL_PATH`

示例：

```bash
./tools/model_download.sh vllm
./tools/model_download.sh ov Qwen/Qwen3-8B /data/models
```

环境行为说明：

- 若当前已激活虚拟环境，会优先复用
- 若未激活虚拟环境，脚本会自动创建并激活 `ecrag_venv`（与 `quick_start.sh` 一致）
- 若缺失 `python3-venv` 或 `pip`，脚本会在支持的包管理器上自动安装所需前置依赖

## 3.2 直接启动脚本

按推理后端与部署方式可直接调用以下脚本：

- OpenVINO 裸金属：`./tools/run_ov_baremetal.sh`
- OpenVINO 容器：`./tools/run_ov_container.sh`
- vLLM 裸金属：`./tools/run_vllm_baremetal.sh`
- vLLM 容器：`./tools/run_vllm_container.sh`
- OVMS 裸金属：`./tools/run_ovms_baremetal.sh`
- OVMS 容器：`./tools/run_ovms_container.sh`

适用于你已明确参数、希望跳过一键引导流程的场景。

# 4.容器镜像编译脚本

编译全部镜像：

```bash
./tools/build_images.sh
```

按组件编译：

```bash
./tools/build_images.sh mega
./tools/build_images.sh server
./tools/build_images.sh ui
./tools/build_images.sh all
```

完整部署说明请参考 [../docs/Advanced_Setup_zh.md](../docs/Advanced_Setup_zh.md)。
