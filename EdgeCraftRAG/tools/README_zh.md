# EdgeCraftRAG 工具脚本

[English](README.md)

本目录包含用于构建镜像和启动 EC-RAG 服务的辅助脚本。

## 脚本

- `quick_start.sh`：一键启动 OpenVINO 或 vLLM 部署
- `build_images.sh`：构建 EC-RAG Docker 镜像

---

## quick_start.sh

请在 `EdgeCraftRAG` 根目录下运行：

```bash
./tools/quick_start.sh
```

### 默认行为

如果未提供环境变量，脚本会使用以下默认值：

```bash
MODEL_PATH=${WORKSPACE}/workspace/models
DOC_PATH=${WORKSPACE}/workspace
TMPFILE_PATH=${WORKSPACE}/workspace
LLM_MODEL=Qwen/Qwen3-8B
```

脚本还会自动执行以下操作：

- 自动创建并激活 Python 虚拟环境
- 在需要时安装 `python3-venv`
- 检查 `MODEL_PATH` 下必需模型是否存在
- 自动下载缺失的 embedding、reranker 和 LLM 模型
- 在启动完成后输出 UI 访问地址

### 非交互模式

默认情况下，非交互模式启动本地 OpenVINO 服务。

```bash
./tools/quick_start.sh
```

你也可以通过环境变量覆盖默认值：

```bash
export MODEL_PATH="${PWD}/workspace/models"
export DOC_PATH="${PWD}/workspace"
export TMPFILE_PATH="${PWD}/workspace"
export LLM_MODEL="Qwen/Qwen3-8B"
export HOST_IP="$(hostname -I | awk '{print $1}')"

./tools/quick_start.sh
```

### 使用 `COMPOSE_PROFILES` 选择部署模式

#### Core Ultra、B60 或 A770 上的 OpenVINO

```bash
./tools/quick_start.sh
```

#### Intel Arc A770 上的 vLLM

```bash
export COMPOSE_PROFILES=vLLM_A770
./tools/quick_start.sh
```

#### Intel Arc B60 上的 vLLM

```bash
export COMPOSE_PROFILES=vLLM_B60
./tools/quick_start.sh
```

可选的 B60/vLLM 环境变量：

```bash
export VLLM_SERVICE_PORT_B60=8086
export DTYPE=float16
export TP=1
export DP=1
export ZE_AFFINITY_MASK=0
export ENFORCE_EAGER=1
export TRUST_REMOTE_CODE=1
export DISABLE_SLIDING_WINDOW=1
export GPU_MEMORY_UTIL=0.8
export NO_ENABLE_PREFIX_CACHING=1
export MAX_NUM_BATCHED_TOKENS=8192
export DISABLE_LOG_REQUESTS=1
export MAX_MODEL_LEN=49152
export BLOCK_SIZE=64
export QUANTIZATION=fp8
```

### 交互模式

```bash
bash -i ./tools/quick_start.sh
```

在交互模式下，脚本会提示你输入：

- 部署模式：`vLLM_A770`、`vLLM_B60` 或 `ov`
- `HOST_IP`
- `DOC_PATH`
- `TMPFILE_PATH`
- `MODEL_PATH`
- `LLM_MODEL`
- 可选的 vLLM 运行参数

### 模型检查与自动下载

脚本会自动检查以下模型路径：

#### 公共模型

```text
${MODEL_PATH}/BAAI/bge-small-en-v1.5
${MODEL_PATH}/BAAI/bge-reranker-large
```

#### vLLM 模式

```text
${MODEL_PATH}/${LLM_MODEL}
```

#### OpenVINO 模式

```text
${MODEL_PATH}/${LLM_MODEL}/INT4_compressed_weights
```

如果缺少必需模型，脚本会自动下载并输出提示信息。

### UI 访问输出

启动完成后，脚本会输出：

```text
Service launched successfully.
UI access URL: http://${HOST_IP}:8082
If you are accessing from another machine, replace ${HOST_IP} with your server's reachable IP or hostname.
```

### 清理

停止并移除已部署容器：

```bash
./tools/quick_start.sh cleanup
```

---

## build_images.sh

构建全部镜像：

```bash
./tools/build_images.sh
```

只构建指定镜像：

```bash
./tools/build_images.sh mega
./tools/build_images.sh server
./tools/build_images.sh ui
./tools/build_images.sh all
```

完整部署说明请参考 [../docs/Advanced_Setup_zh.md](../docs/Advanced_Setup_zh.md).
