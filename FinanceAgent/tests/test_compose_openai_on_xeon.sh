#!/bin/bash
# Copyright (C) 2025 Intel Corporation
# SPDX-License-Identifier: Apache-2.0
set -xe

export WORKPATH=$(dirname "$PWD")
export WORKDIR=$WORKPATH/../../
echo "WORKDIR=${WORKDIR}"
export IP_ADDRESS=$(hostname -I | awk '{print $1}')
export HOST_IP=${IP_ADDRESS}
LOG_PATH=$WORKPATH

# Proxy settings
export NO_PROXY="${NO_PROXY},${HOST_IP}"
export HTTP_PROXY="${http_proxy}"
export HTTPS_PROXY="${https_proxy}"

export no_proxy="${no_proxy},${HOST_IP}"
export http_proxy="${http_proxy}"
export https_proxy="${https_proxy}"

# OPENAI and agent configuration
export OPENAI_API_KEY="${OPENAI_API_KEY}"
export OPENAI_LLM_MODEL_ID="${OPENAI_LLM_MODEL_ID:-gpt-4o-mini-2024-07-18}"
export RECURSION_LIMIT_WORKER="${RECURSION_LIMIT_WORKER:-12}"
export RECURSION_LIMIT_SUPERVISOR="${RECURSION_LIMIT_SUPERVISOR:-10}"
export TEMPERATURE="${TEMPERATURE:-0.5}"
export MAX_TOKENS="${MAX_TOKENS:-4096}"

# Hugging Face API token
export HUGGINGFACEHUB_API_TOKEN="${HF_TOKEN}"

# Dataprep and Docsum LLM configuration
export HF_CACHE_DIR="${HF_CACHE_DIR:-"./data"}"
export LLM_PORT="${LLLM_PORT:-8086}"
export LLM_ENDPOINT="http://${IP_ADDRESS}:${LLM_PORT}"
export LLM_MODEL_ID="${LLM_MODEL_ID:-meta-llama/Llama-3.1-8B-Instruct}"
export MAX_INPUT_TOKENS="${MAX_INPUT_TOKENS:-2048}"
export MAX_TOTAL_TOKENS="${MAX_TOTAL_TOKENS:-4096}"

# Worker URLs
export WORKER_FINQA_AGENT_URL="http://${IP_ADDRESS}:9095/v1/chat/completions"
export WORKER_RESEARCH_AGENT_URL="http://${IP_ADDRESS}:9096/v1/chat/completions"

# DocSum configuration
export DOCSUM_COMPONENT_NAME="${DOCSUM_COMPONENT_NAME:-"OpeaDocSumvLLM"}"
export DOCSUM_ENDPOINT="http://${IP_ADDRESS}:9000/v1/docsum"

# Toolset and prompt paths
export TOOLSET_PATH=$WORKDIR/GenAIExamples/FinanceAgent/tools/
export PROMPT_PATH=$WORKDIR/GenAIExamples/FinanceAgent/prompts/

#### env vars for dataprep #############
export DATAPREP_PORT="6007"
export TEI_EMBEDDER_PORT="10221"
export REDIS_URL_VECTOR="redis://${IP_ADDRESS}:6379"
export REDIS_URL_KV="redis://${IP_ADDRESS}:6380"

export DATAPREP_COMPONENT_NAME="OPEA_DATAPREP_REDIS_FINANCE"
export EMBEDDING_MODEL_ID="BAAI/bge-base-en-v1.5"
export TEI_EMBEDDING_ENDPOINT="http://${IP_ADDRESS}:${TEI_EMBEDDER_PORT}"
#######################################

function stop_dataprep() {
    echo "Stopping databases"
    cid=$(docker ps -aq --filter "name=dataprep-redis-server*" --filter "name=redis-*" --filter "name=tei-embedding-*")
    if [[ ! -z "$cid" ]]; then docker stop $cid && docker rm $cid && sleep 1s; fi
}

function stop_agent_docker() {
    cd $WORKPATH/docker_compose/intel/cpu/xeon/
    container_list=$(cat compose_openai.yaml | grep container_name | cut -d':' -f2)
    for container_name in $container_list; do
        cid=$(docker ps -aq --filter "name=$container_name")
        echo "Stopping container $container_name"
        if [[ ! -z "$cid" ]]; then docker rm $cid -f && sleep 1s; fi
    done
}

echo "workpath: $WORKPATH"
echo "=================== Stop containers ===================="
stop_agent_docker
stop_dataprep

cd $WORKPATH/tests

echo "=================== #1 Building docker images ===================="
bash step1_build_images.sh xeon
echo "=================== #1 Building docker images completed ===================="

echo "=================== #2 Start services ===================="
bash step2_start_services.sh xeon
echo "=================== #2 Endpoints for services started ===================="

echo "=================== #3 Validate ingest_validate_dataprep ===================="
bash step3_validate_ingest_validate_dataprep.sh
echo "=================== #3 Data ingestion and validation completed ===================="

echo "=================== #4 Start agents ===================="
bash step4_validate_agent_service.sh
echo "=================== #4 Agent test passed ===================="

echo "=================== #5 Stop microservices ===================="
stop_agent_docker
stop_dataprep
echo "=================== #5 Microservices stopped ==================="

echo y | docker system prune

echo "ALL DONE!!"
