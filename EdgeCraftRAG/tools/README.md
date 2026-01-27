# EdgeCraftRAG one-click deployment script

## run quick_start.sh

### Run with Non-Interactive Mode:

You need to set environment before execute script, you can refer to [Prepare env variables and configurations](../docker_compose/intel/gpu/arc/README.md#4-prepare-env-variables-and-configurations) for env details.

```bash
# set start up env, below is an example:
export MODEL_PATH="${PWD}/models"
export LLM_MODEL="Qwen/Qwen3-8B" # Your model id
export HOST_IP=$ip_address # Your host ip
export VIDEOGROUPID=$(getent group video | cut -d: -f3)
export RENDERGROUPID=$(getent group render | cut -d: -f3)
export no_proxy=${no_proxy},${HOST_IP},edgecraftrag,edgecraftrag-server
export NO_PROXY=${NO_PROXY},${HOST_IP},edgecraftrag,edgecraftrag-server
export DOC_PATH=${PWD}/tests # your DOC_PATH
export TMPFILE_PATH=${PWD}/tests # your TMPFILE_PATH
# set vllm launch env, below is an example:
export VLLM_SERVICE_PORT_B60=8086
export DTYPE=float16
export TP=1 # for multi GPU, you can change TP value
export DP=1
export ZE_AFFINITY_MASK=0 # for multi GPU, you can export ZE_AFFINITY_MASK=0,1,2...
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
bash quick_start.sh
```

### Run with Interactive Mode:

```bash
bash -i quick_start.sh
# In this mode, you can follow the Interactive guide to set env and finish start up
```
