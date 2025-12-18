# EdgeCraftRAG one-click deployment script

## run quick_start.sh

### Run with Non-Interactive Mode:

You need to set environment before execute script, you can refer to [Prepare env variables and configurations](../docker_compose/intel/gpu/arc/README.md#4-prepare-env-variables-and-configurations) for env details.
```bash
# set environment, below is an example:
export MODEL_PATH="${PWD}/models"
export LLM_MODEL="Qwen/Qwen3-8B" # Your model id
export HOST_IP=$ip_address # Your host ip
export VIDEOGROUPID=$(getent group video | cut -d: -f3)
export RENDERGROUPID=$(getent group render | cut -d: -f3)
export no_proxy=${no_proxy},${HOST_IP},edgecraftrag,edgecraftrag-server
export NO_PROXY=${NO_PROXY},${HOST_IP},edgecraftrag,edgecraftrag-server
export DOC_PATH=${PWD}/tests # your DOC_PATH
export TMPFILE_PATH=${PWD}/tests # your TMPFILE_PATH
bash quick_start.sh
```

### Run with Interactive Mode:
```bash
bash -i quick_start.sh
# In this mode, you can follow the Interactive guide to set env and finish start up
```